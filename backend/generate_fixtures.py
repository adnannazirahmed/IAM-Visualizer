import json
import os

fixtures_dir = r"c:\Users\jawad\Documents\Antigravity\cloud-iam-visualizer\backend\tests\fixtures"
os.makedirs(fixtures_dir, exist_ok=True)

# 1. simple_org.json
simple_org = {
    "UserDetailList": [
        {"UserName": "Alice", "Arn": "arn:aws:iam::123:user/Alice", "GroupList": ["Developers"], "AttachedManagedPolicies": []},
        {"UserName": "Bob", "Arn": "arn:aws:iam::123:user/Bob", "GroupList": ["Developers"], "AttachedManagedPolicies": []}
    ],
    "GroupDetailList": [
        {
            "GroupName": "Developers", 
            "Arn": "arn:aws:iam::123:group/Developers", 
            "AttachedManagedPolicies": [{"PolicyName": "ViewOnly", "PolicyArn": "arn:aws:iam::aws:policy/ViewOnlyAccess"}]
        }
    ],
    "RoleDetailList": [
        {"RoleName": "AppRole", "Arn": "arn:aws:iam::123:role/AppRole", "AssumeRolePolicyDocument": {"Statement": []}, "AttachedManagedPolicies": []}
    ],
    "Policies": [
        {"PolicyName": "ViewOnly", "Arn": "arn:aws:iam::aws:policy/ViewOnlyAccess", "PolicyVersionList": [{"IsDefaultVersion": True, "Document": {"Statement": [{"Effect": "Allow", "Action": ["s3:Get*", "s3:List*"], "Resource": ["*"]}]}}]}
    ]
}

with open(os.path.join(fixtures_dir, "simple_org.json"), "w") as f:
    json.dump(simple_org, f, indent=2)

# 2. wildcard_policies.json
wildcard = {
    "UserDetailList": [
        {
            "UserName": "AdminUser", 
            "Arn": "arn:aws:iam::123:user/AdminUser", 
            "UserPolicyList": [
                {"PolicyName": "Admin", "PolicyDocument": {"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}}
            ]
        },
        {
            "UserName": "IAMAdmin", 
            "Arn": "arn:aws:iam::123:user/IAMAdmin", 
            "UserPolicyList": [
                {"PolicyName": "IAMAdmin", "PolicyDocument": {"Statement": [{"Effect": "Allow", "Action": "iam:*", "Resource": "*"}]}}
            ]
        }
    ]
}

with open(os.path.join(fixtures_dir, "wildcard_policies.json"), "w") as f:
    json.dump(wildcard, f, indent=2)

# 3. explicit_denies.json
denies = {
    "UserDetailList": [
        {
            "UserName": "ConflictedUser", 
            "Arn": "arn:aws:iam::123:user/ConflictedUser", 
            "UserPolicyList": [
                {
                    "PolicyName": "AllowAndDeny", 
                    "PolicyDocument": {
                        "Statement": [
                            {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": ["*"]},
                            {"Effect": "Deny", "Action": ["s3:*"], "Resource": ["*"]}
                        ]
                    }
                }
            ]
        }
    ]
}
with open(os.path.join(fixtures_dir, "explicit_denies.json"), "w") as f:
    json.dump(denies, f, indent=2)

# 4. circular_roles.json
circular = {
    "RoleDetailList": [
        {
            "RoleName": "RoleA", 
            "Arn": "arn:aws:iam::123:role/RoleA", 
            "AssumeRolePolicyDocument": {
                "Statement": [{"Effect": "Allow", "Action": ["sts:AssumeRole"], "Principal": {"AWS": "arn:aws:iam::123:role/RoleB"}}]
            }
        },
        {
            "RoleName": "RoleB", 
            "Arn": "arn:aws:iam::123:role/RoleB", 
            "AssumeRolePolicyDocument": {
                "Statement": [{"Effect": "Allow", "Action": ["sts:AssumeRole"], "Principal": {"AWS": "arn:aws:iam::123:role/RoleA"}}]
            }
        }
    ]
}
with open(os.path.join(fixtures_dir, "circular_roles.json"), "w") as f:
    json.dump(circular, f, indent=2)

# 5. escalation_scenarios.json
escalation = {
    "UserDetailList": [
        {
            "UserName": "BadActor1", 
            "Arn": "arn:aws:iam::123:user/BadActor1", 
            "UserPolicyList": [
                {
                    "PolicyName": "EscalationPolicy", 
                    "PolicyDocument": {
                        "Statement": [
                            {"Effect": "Allow", "Action": ["iam:PassRole", "lambda:CreateFunction"], "Resource": ["*"]},
                            {"Effect": "Allow", "Action": ["iam:CreatePolicyVersion"], "Resource": ["*"]},
                            {"Effect": "Allow", "Action": ["iam:AttachUserPolicy"], "Resource": ["*"]}
                        ]
                    }
                }
            ]
        }
    ]
}
with open(os.path.join(fixtures_dir, "escalation_scenarios.json"), "w") as f:
    json.dump(escalation, f, indent=2)
