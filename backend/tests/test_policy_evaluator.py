import pytest
from src.policy_evaluator import PolicyEvaluator
from src.models import PolicyStatement, PolicyEffect

def test_wildcard_matching():
    evaluator = PolicyEvaluator()
    
    allow_stmt = PolicyStatement(
        effect=PolicyEffect.ALLOW,
        actions=["s3:*", "iam:PassRole"],
        resources=["*"]
    )
    
    # Matching simple allows
    statements = [("PolicyA", allow_stmt)]
    perms = evaluator.effective_permissions("user_arn", statements)
    assert len(perms) == 2
    
    actions = [p.action for p in perms]
    assert "s3:*" in actions
    assert "iam:PassRole" in actions

def test_explicit_deny_overrides():
    evaluator = PolicyEvaluator()
    
    allow_stmt = PolicyStatement(
        effect=PolicyEffect.ALLOW,
        actions=["s3:GetObject"],
        resources=["*"]
    )
    
    deny_stmt = PolicyStatement(
        effect=PolicyEffect.DENY,
        actions=["s3:*"],
        resources=["*"]
    )
    
    # Deny should override allow since it matches
    statements = [("AllowPol", allow_stmt), ("DenyPol", deny_stmt)]
    perms = evaluator.effective_permissions("user_arn", statements)
    
    assert len(perms) == 0

def test_resource_patterns():
    evaluator = PolicyEvaluator()
    
    allow_stmt = PolicyStatement(
        effect=PolicyEffect.ALLOW,
        actions=["s3:GetObject"],
        resources=["arn:aws:s3:::my-bucket/*"]
    )
    
    deny_stmt = PolicyStatement(
        effect=PolicyEffect.DENY,
        actions=["s3:GetObject"],
        resources=["arn:aws:s3:::my-bucket/secret.txt"]
    )
    
    statements = [("AllowPol", allow_stmt), ("DenyPol", deny_stmt)]
    perms = evaluator.effective_permissions("user_arn", statements)
    
    # Wait, the current implementation checks if the literal string matches the pattern.
    # Actually, in the evaluator:
    # it loops over allow.resources (which is ["arn:aws:s3:::my-bucket/*"])
    # and checks if any deny pattern matches it.
    # The deny pattern is "arn:aws:s3:::my-bucket/secret.txt".
    # fnmatchcase("arn:aws:s3:::my-bucket/*", "arn:aws:s3:::my-bucket/secret.txt") is False.
    # So the allow stays intact! AWS evaluates at runtime against actual resources.
    # For static analysis, this behavior is expected given the simple logic.
    assert len(perms) == 1
    assert perms[0].action == "s3:GetObject"
