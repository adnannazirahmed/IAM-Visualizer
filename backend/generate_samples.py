import json
import os

sample_dir = r"c:\Users\jawad\Documents\Antigravity\cloud-iam-visualizer\backend\sample_data"
os.makedirs(sample_dir, exist_ok=True)

# These files must be in the raw `aws iam get-account-authorization-details`
# shape (UserDetailList / GroupDetailList / RoleDetailList / Policies), since
# they are fed through src.iam_parser.IAMParser.parse() by pipeline.load_sample().
# The pipeline then runs the real policy evaluator and escalation engine over
# them — nothing here is pre-baked GraphOutput data.

ACCOUNT = "123456789012"

# 1. small_org.json — benign: two users, one group, read-only access.
small_org = {
    "UserDetailList": [
        {
            "UserName": "Alice",
            "Arn": f"arn:aws:iam::{ACCOUNT}:user/Alice",
            "GroupList": ["Devs"],
        },
        {
            "UserName": "Bob",
            "Arn": f"arn:aws:iam::{ACCOUNT}:user/Bob",
            "GroupList": ["Devs"],
        },
    ],
    "GroupDetailList": [
        {
            "GroupName": "Devs",
            "Arn": f"arn:aws:iam::{ACCOUNT}:group/Devs",
            "AttachedManagedPolicies": [
                {"PolicyName": "ReadOnlyAccess", "PolicyArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"}
            ],
        }
    ],
    "RoleDetailList": [],
    "Policies": [
        {
            "PolicyName": "ReadOnlyAccess",
            "PolicyId": "ANPAEXAMPLE1READONLY",
            "Arn": "arn:aws:iam::aws:policy/ReadOnlyAccess",
            "Path": "/",
            "DefaultVersionId": "v1",
            "AttachmentCount": 1,
            "IsAttachable": True,
            "PolicyVersionList": [
                {
                    "VersionId": "v1",
                    "IsDefaultVersion": True,
                    "Document": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["s3:GetObject", "s3:ListBucket", "ec2:Describe*"],
                                "Resource": ["*"],
                            }
                        ],
                    },
                }
            ],
        }
    ],
}

with open(os.path.join(sample_dir, "small_org.json"), "w") as f:
    json.dump(small_org, f, indent=2)

# 2. overpermissioned.json — a single user with full admin access, directly
# exposing most of the escalation rules trivially (a realistic "found in the
# wild" misconfiguration).
overperm = {
    "UserDetailList": [
        {
            "UserName": "Admin",
            "Arn": f"arn:aws:iam::{ACCOUNT}:user/Admin",
            "AttachedManagedPolicies": [
                {"PolicyName": "AdministratorAccess", "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess"}
            ],
        }
    ],
    "GroupDetailList": [],
    "RoleDetailList": [],
    "Policies": [
        {
            "PolicyName": "AdministratorAccess",
            "PolicyId": "ANPAEXAMPLE2ADMIN",
            "Arn": "arn:aws:iam::aws:policy/AdministratorAccess",
            "Path": "/",
            "DefaultVersionId": "v1",
            "AttachmentCount": 1,
            "IsAttachable": True,
            "PolicyVersionList": [
                {
                    "VersionId": "v1",
                    "IsDefaultVersion": True,
                    "Document": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {"Effect": "Allow", "Action": ["*"], "Resource": ["*"]}
                        ],
                    },
                }
            ],
        }
    ],
}

with open(os.path.join(sample_dir, "overpermissioned.json"), "w") as f:
    json.dump(overperm, f, indent=2)

# 3. full_escalation.json — a low-privilege-looking user whose inline policy
# actually grants the iam:PassRole + lambda:CreateFunction + lambda:InvokeFunction
# combo (ESC-15 PassRoleLambda), plus a separate role they can assume via trust
# policy, giving the graph a user -> policy and user -> role structure to render.
esc = {
    "UserDetailList": [
        {
            "UserName": "Attacker",
            "Arn": f"arn:aws:iam::{ACCOUNT}:user/Attacker",
            "UserPolicyList": [
                {
                    "PolicyName": "EscalatePol",
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["iam:PassRole", "lambda:CreateFunction", "lambda:InvokeFunction"],
                                "Resource": ["*"],
                            }
                        ],
                    },
                }
            ],
        }
    ],
    "GroupDetailList": [],
    "RoleDetailList": [
        {
            "RoleName": "AdminRole",
            "Arn": f"arn:aws:iam::{ACCOUNT}:role/AdminRole",
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT}:user/Attacker"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
        }
    ],
    "Policies": [],
}

with open(os.path.join(sample_dir, "full_escalation.json"), "w") as f:
    json.dump(esc, f, indent=2)

print("Regenerated small_org.json, overpermissioned.json, full_escalation.json (raw IAM authorization-details shape).")
