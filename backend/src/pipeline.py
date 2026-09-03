from typing import Dict, List, Tuple

from src.models import IAMData, GraphOutput, EffectivePermission
from src.graph_builder import GraphBuilder
from src.policy_evaluator import PolicyEvaluator
from src.escalation import detect_escalation_paths
from src.aws_exporter import AWSExporter

def process_iam_data(iam_data: IAMData) -> GraphOutput:
    # 1. Build initial graph
    builder = GraphBuilder(iam_data)
    graph_output = builder.build()
    
    # 2. Build effective permissions map
    evaluator = PolicyEvaluator()
    effective_permissions_map: Dict[str, List[EffectivePermission]] = {}
    
    # helper to find statements for a policy ARN or name
    def get_policy_statements(policy_id_or_name: str) -> List[Tuple[str, any]]:
        node = builder.nodes_dict.get(policy_id_or_name)
        if not node:
            return []
        
        # find the actual IAMPolicy
        for p in iam_data.policies:
            if f"policy::{p.policy_name}" == policy_id_or_name:
                return [(p.policy_name, stmt) for stmt in p.document.statements]
                
        # check inlines
        for entity_list in [iam_data.users, iam_data.roles, iam_data.groups]:
            for entity in entity_list:
                for p in entity.inline_policies:
                    if f"policy::{p.policy_name}" == policy_id_or_name:
                        return [(p.policy_name, stmt) for stmt in p.document.statements]
                        
        return []

    # get permissions for each identity
    for node_id, node in builder.nodes_dict.items():
        if node.type.value in ("user", "role", "group"):
            statements = []
            
            # get directly attached policies
            for link in builder.links_list:
                if link.source == node_id and link.relationship.value == "has_policy":
                    statements.extend(get_policy_statements(link.target))
                    
            # if user, get group policies too
            if node.type.value == "user":
                for link in builder.links_list:
                    if link.source == node_id and link.relationship.value == "member_of":
                        group_id = link.target
                        for glink in builder.links_list:
                            if glink.source == group_id and glink.relationship.value == "has_policy":
                                statements.extend(get_policy_statements(glink.target))
                                
            perms = evaluator.effective_permissions(node.arn, statements)
            effective_permissions_map[node_id] = perms
            
            # Update node's effective permissions for visualization
            node.effective_permissions = [f"{p.effect.value}: {p.action} on {p.resource}" for p in perms]
            
    # 3. Detect escalations
    escalation_paths = detect_escalation_paths(graph_output, effective_permissions_map)
    graph_output.escalation_paths = escalation_paths
    
    # Update node metadata based on escalations
    graph_output.metadata.escalation_count = len(escalation_paths)
    
    return graph_output

def load_live() -> IAMData:
    exporter = AWSExporter()
    return exporter.export_iam_data()
