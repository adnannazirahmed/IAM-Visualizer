import pytest
import json
import os
from src.iam_parser import IAMParser
from src.models import IAMData, PolicyEffect

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), "r") as f:
        return json.load(f)

def test_parse_simple_org():
    parser = IAMParser()
    data = load_fixture("simple_org.json")
    iam_data = parser.parse(data)
    
    assert len(iam_data.users) == 2
    assert len(iam_data.groups) == 1
    assert len(iam_data.roles) == 1
    assert len(iam_data.policies) == 1
    
    # Check User
    alice = next((u for u in iam_data.users if u.user_name == "Alice"), None)
    assert alice is not None
    assert "Developers" in alice.group_list
    
def test_parse_wildcard_policies():
    parser = IAMParser()
    data = load_fixture("wildcard_policies.json")
    iam_data = parser.parse(data)
    
    assert len(iam_data.users) == 2
    admin = next(u for u in iam_data.users if u.user_name == "AdminUser")
    
    assert len(admin.inline_policies) == 1
    stmt = admin.inline_policies[0].document.statements[0]
    assert stmt.effect == PolicyEffect.ALLOW
    assert "*" in stmt.actions
    assert "*" in stmt.resources
    
def test_parse_malformed_json():
    parser = IAMParser()
    # Missing fields shouldn't crash it
    malformed = {
        "UserDetailList": [
            {"UserName": "MissingArn"} # no arn
        ]
    }
    iam_data = parser.parse(malformed)
    assert len(iam_data.users) == 1
    assert iam_data.users[0].user_name == "MissingArn"
    assert iam_data.users[0].arn == ""
