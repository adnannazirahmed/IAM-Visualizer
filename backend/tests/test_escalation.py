import pytest
from src.models import (
    GraphOutput, GraphNode, NodeType, RiskLevel, GraphLink, RelationshipType,
    EffectivePermission, PolicyEffect, PolicyCondition
)
from src.escalation import detect_escalation_paths, RULES, get_risk_score

def create_dummy_graph():
    graph = GraphOutput()
    
    # Benign User
    user1 = GraphNode(id="user::benign", type=NodeType.USER, name="benign")
    # Malicious User with CreateNewPolicyVersion (iam:CreatePolicyVersion)
    user2 = GraphNode(id="user::attacker1", type=NodeType.USER, name="attacker1")
    # Malicious Role with CreateEC2WithExistingIP (iam:PassRole + ec2:RunInstances)
    role1 = GraphNode(id="role::attacker2", type=NodeType.ROLE, name="attacker2")
    # Group in a cycle
    group1 = GraphNode(id="group::cycle_group", type=NodeType.GROUP, name="cycle_group")
    user3 = GraphNode(id="user::cycle_user", type=NodeType.USER, name="cycle_user")
    
    graph.nodes = [user1, user2, role1, group1, user3]
    
    # Links for cycle
    graph.links = [
        GraphLink(source="user::cycle_user", target="group::cycle_group", relationship=RelationshipType.MEMBER_OF),
        # Assume some bizarre configuration allows the group to assume a role that the user belongs to... 
        # But let's just add a dummy edge that could cause a cycle if we traversed all relationships.
        # The path logic traverses CAN_ASSUME and MEMBER_OF.
        # user -> group is standard. If group -> user existed (invalid in AWS but good for testing cycle detection).
        GraphLink(source="group::cycle_group", target="user::cycle_user", relationship=RelationshipType.CAN_ASSUME),
    ]
    return graph

def create_allow_perm(action: str) -> EffectivePermission:
    return EffectivePermission(action=action, resource="*", effect=PolicyEffect.ALLOW)

def create_deny_perm(action: str) -> EffectivePermission:
    return EffectivePermission(action=action, resource="*", effect=PolicyEffect.DENY)

def test_benign_identity():
    graph = create_dummy_graph()
    eff_map = {
        "user::benign": [create_allow_perm("s3:GetObject"), create_allow_perm("ec2:DescribeInstances")]
    }
    paths = detect_escalation_paths(graph, eff_map)
    
    benign_node = next(n for n in graph.nodes if n.id == "user::benign")
    assert benign_node.risk_level == RiskLevel.NONE
    assert benign_node.risk_score == 0.0
    
    # Verify no paths involve this user as source
    assert not any(p.affected_identity == "user::benign" for p in paths)

def test_critical_escalation():
    # Test CreateNewPolicyVersion
    graph = create_dummy_graph()
    eff_map = {
        "user::attacker1": [create_allow_perm("iam:CreatePolicyVersion")]
    }
    paths = detect_escalation_paths(graph, eff_map)
    
    attacker_node = next(n for n in graph.nodes if n.id == "user::attacker1")
    assert attacker_node.risk_level == RiskLevel.CRITICAL
    assert attacker_node.risk_score == 1.0
    
    path = next(p for p in paths if p.affected_identity == "user::attacker1")
    assert path.technique == "CreateNewPolicyVersion"
    assert path.risk == RiskLevel.CRITICAL

def test_high_escalation_multi_action():
    # Test CreateEC2WithExistingIP
    graph = create_dummy_graph()
    eff_map = {
        "role::attacker2": [create_allow_perm("iam:PassRole"), create_allow_perm("ec2:RunInstances")]
    }
    paths = detect_escalation_paths(graph, eff_map)
    
    attacker_node = next(n for n in graph.nodes if n.id == "role::attacker2")
    assert attacker_node.risk_level == RiskLevel.HIGH
    assert attacker_node.risk_score == 0.75
    
    path = next(p for p in paths if p.affected_identity == "role::attacker2")
    assert path.technique == "CreateEC2WithExistingIP"
    assert path.risk == RiskLevel.HIGH

def test_wildcard_permission_matching():
    # Test wildcard matches multiple rules
    graph = create_dummy_graph()
    # iam:* matches all IAM escalations
    eff_map = {
        "user::attacker1": [create_allow_perm("iam:*")]
    }
    paths = detect_escalation_paths(graph, eff_map)
    
    # It should trigger AttachUserPolicy, CreateNewPolicyVersion, etc.
    assert len(paths) >= 10 
    attacker_node = next(n for n in graph.nodes if n.id == "user::attacker1")
    assert attacker_node.risk_level == RiskLevel.CRITICAL
    
    # Specific pattern match
    eff_map_specific = {
        "user::attacker1": [create_allow_perm("iam:Create*Policy*")]
    }
    paths_specific = detect_escalation_paths(graph, eff_map_specific)
    techniques = [p.technique for p in paths_specific]
    assert "CreateNewPolicyVersion" in techniques
    assert "AttachUserPolicy" not in techniques

def test_deny_overrides_allow():
    graph = create_dummy_graph()
    eff_map = {
        "user::attacker1": [
            create_allow_perm("iam:CreatePolicyVersion"),
            create_deny_perm("iam:CreatePolicyVersion")
        ]
    }
    paths = detect_escalation_paths(graph, eff_map)
    
    attacker_node = next(n for n in graph.nodes if n.id == "user::attacker1")
    assert attacker_node.risk_level == RiskLevel.NONE
    assert len(paths) == 0

def test_cycle_handling():
    # Ensure cycle doesn't cause infinite loop
    graph = create_dummy_graph()
    eff_map = {
        "user::cycle_user": [create_allow_perm("iam:PassRole"), create_allow_perm("ssm:StartSession")],
        "group::cycle_group": []
    }
    # It should traverse user -> group -> user and stop due to visited set
    paths = detect_escalation_paths(graph, eff_map)
    
    # cycle_user should have escalation
    user_node = next(n for n in graph.nodes if n.id == "user::cycle_user")
    assert user_node.risk_level == RiskLevel.HIGH
    
    # cycle_group might be visited from user and checked.
    # since we pass the permissions map, only the exact node's perms trigger rules.
    # But wait, in detect_escalation_paths, the perms are fetched per `curr_id`.
    # Let's ensure no recursion error occurs (it passes if it completes)
    assert len(paths) > 0
