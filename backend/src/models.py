"""
Pydantic data models for AWS IAM entities and the output graph format.

These models are the shared contract between:
- iam_parser.py (produces IAM entity models)
- policy_evaluator.py (consumes PolicyStatement models)
- graph_builder.py (produces GraphNode/GraphLink models)
- escalation.py (produces EscalationPath models)
- api.py (serializes the full GraphOutput to JSON)
"""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────

class RiskLevel(str, enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RelationshipType(str, enum.Enum):
    CAN_ASSUME = "can_assume"
    HAS_POLICY = "has_policy"
    MEMBER_OF = "member_of"
    CAN_ACCESS = "can_access"


class NodeType(str, enum.Enum):
    USER = "user"
    ROLE = "role"
    GROUP = "group"
    POLICY = "policy"
    RESOURCE = "resource"


class PolicyEffect(str, enum.Enum):
    ALLOW = "Allow"
    DENY = "Deny"


# ──────────────────────────────────────────────
#  IAM Policy Models
# ──────────────────────────────────────────────

class PolicyCondition(BaseModel):
    """A single IAM policy condition block."""
    operator: str  # e.g. "StringEquals", "ArnLike"
    key: str  # e.g. "aws:SourceIp", "iam:PassedToService"
    values: list[str]


class PolicyStatement(BaseModel):
    """A single statement within an IAM policy document."""
    sid: Optional[str] = None
    effect: PolicyEffect
    actions: list[str] = Field(default_factory=list)  # e.g. ["s3:GetObject", "iam:*"]
    not_actions: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)  # e.g. ["*", "arn:aws:s3:::my-bucket"]
    not_resources: list[str] = Field(default_factory=list)
    conditions: list[PolicyCondition] = Field(default_factory=list)
    principals: list[str] = Field(default_factory=list)  # For trust policies


class PolicyDocument(BaseModel):
    """A complete IAM policy document."""
    version: str = "2012-10-17"
    statements: list[PolicyStatement] = Field(default_factory=list)


class ManagedPolicyAttachment(BaseModel):
    """Reference to an attached managed policy."""
    policy_name: str
    policy_arn: str


# ──────────────────────────────────────────────
#  IAM Identity Models
# ──────────────────────────────────────────────

class IAMPolicy(BaseModel):
    """A managed IAM policy with its document."""
    policy_name: str
    policy_id: str = ""
    arn: str
    path: str = "/"
    default_version_id: str = "v1"
    attachment_count: int = 0
    is_attachable: bool = True
    document: PolicyDocument = Field(default_factory=PolicyDocument)


class IAMUser(BaseModel):
    """An IAM user with their policies and group memberships."""
    user_name: str
    user_id: str = ""
    arn: str
    path: str = "/"
    group_list: list[str] = Field(default_factory=list)
    attached_managed_policies: list[ManagedPolicyAttachment] = Field(default_factory=list)
    inline_policies: list[IAMPolicy] = Field(default_factory=list)


class IAMRole(BaseModel):
    """An IAM role with its trust policy and permissions."""
    role_name: str
    role_id: str = ""
    arn: str
    path: str = "/"
    assume_role_policy_document: PolicyDocument = Field(default_factory=PolicyDocument)
    attached_managed_policies: list[ManagedPolicyAttachment] = Field(default_factory=list)
    inline_policies: list[IAMPolicy] = Field(default_factory=list)
    instance_profile_list: list[str] = Field(default_factory=list)


class IAMGroup(BaseModel):
    """An IAM group with its members and policies."""
    group_name: str
    group_id: str = ""
    arn: str
    path: str = "/"
    members: list[str] = Field(default_factory=list)  # user names
    attached_managed_policies: list[ManagedPolicyAttachment] = Field(default_factory=list)
    inline_policies: list[IAMPolicy] = Field(default_factory=list)


class IAMData(BaseModel):
    """The complete parsed IAM data from an AWS account or static export."""
    users: list[IAMUser] = Field(default_factory=list)
    roles: list[IAMRole] = Field(default_factory=list)
    groups: list[IAMGroup] = Field(default_factory=list)
    policies: list[IAMPolicy] = Field(default_factory=list)
    account_id: str = "000000000000"


# ──────────────────────────────────────────────
#  Effective Permission (output of policy evaluator)
# ──────────────────────────────────────────────

class EffectivePermission(BaseModel):
    """A resolved permission after evaluating Allow/Deny logic."""
    action: str
    resource: str
    effect: PolicyEffect
    source_policy: str = ""  # ARN or name of the policy granting this
    conditions: list[PolicyCondition] = Field(default_factory=list)


# ──────────────────────────────────────────────
#  Graph Output Models (contract with frontend)
# ──────────────────────────────────────────────

class GraphNode(BaseModel):
    """A node in the output permission graph."""
    id: str  # e.g. "user::alice" or "role::admin-role"
    type: NodeType
    name: str
    arn: str = ""
    risk_level: RiskLevel = RiskLevel.NONE
    risk_score: float = 0.0
    policies: list[str] = Field(default_factory=list)  # attached policy ARNs
    effective_permissions: list[str] = Field(default_factory=list)  # summarized for display
    escalation_paths: list[str] = Field(default_factory=list)  # escalation IDs


class GraphLink(BaseModel):
    """An edge in the output permission graph."""
    source: str
    target: str
    relationship: RelationshipType
    permissions: list[str] = Field(default_factory=list)
    is_escalation: bool = False
    risk_level: RiskLevel = RiskLevel.NONE
    label: str = ""


class EscalationPath(BaseModel):
    """A detected privilege escalation path."""
    id: str
    technique: str
    risk: RiskLevel
    path: list[str]  # ordered node IDs in the escalation chain
    required_permissions: list[str]
    description: str
    affected_identity: str = ""  # the starting identity


class GraphMetadata(BaseModel):
    """Metadata about the generated graph."""
    account_id: str = "000000000000"
    generated_at: str = ""
    source: str = "static"  # "static" or "live"
    node_count: int = 0
    link_count: int = 0
    escalation_count: int = 0


class GraphOutput(BaseModel):
    """The complete graph output — the JSON contract with the frontend."""
    metadata: GraphMetadata = Field(default_factory=GraphMetadata)
    nodes: list[GraphNode] = Field(default_factory=list)
    links: list[GraphLink] = Field(default_factory=list)
    escalation_paths: list[EscalationPath] = Field(default_factory=list)
