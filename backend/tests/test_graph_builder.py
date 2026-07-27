import pytest
import json
import os
from src.iam_parser import IAMParser
from src.graph_builder import GraphBuilder
from src.models import RiskLevel, RelationshipType

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), "r") as f:
        return json.load(f)

def test_build_simple_graph():
    parser = IAMParser()
    iam_data = parser.parse(load_fixture("simple_org.json"))
    builder = GraphBuilder(iam_data)
    graph_out = builder.build()
    
    assert graph_out.metadata.node_count > 0
    
    nodes = {n.id: n for n in graph_out.nodes}
    assert "user::Alice" in nodes
    assert "group::Developers" in nodes
    
    # Check link
    member_link = next((l for l in graph_out.links if l.source == "user::Alice" and l.target == "group::Developers"), None)
    assert member_link is not None
    assert member_link.relationship == RelationshipType.MEMBER_OF

def test_cycle_detection():
    parser = IAMParser()
    iam_data = parser.parse(load_fixture("circular_roles.json"))
    builder = GraphBuilder(iam_data)
    graph_out = builder.build()
    
    nodes = {n.id: n for n in graph_out.nodes}
    # Both roles should be tagged with MEDIUM risk due to cycle
    assert nodes["role::RoleA"].risk_level == RiskLevel.MEDIUM
    assert nodes["role::RoleB"].risk_level == RiskLevel.MEDIUM
    
    assume_links = [l for l in graph_out.links if l.relationship == RelationshipType.CAN_ASSUME]
    assert len(assume_links) == 2
