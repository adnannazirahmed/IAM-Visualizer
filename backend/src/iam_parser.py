import json
import logging
from urllib.parse import unquote
from typing import Any, Dict, List, Optional
from src.models import (
    IAMData, IAMUser, IAMRole, IAMGroup, IAMPolicy,
    PolicyDocument, PolicyStatement, PolicyEffect, PolicyCondition,
    ManagedPolicyAttachment
)

logger = logging.getLogger(__name__)

class IAMParser:
    def __init__(self):
        pass

    def parse(self, raw_data: Dict[str, Any]) -> IAMData:
        """Parse raw IAM JSON data into an IAMData model."""
        account_id = "000000000000"
        
        iam_data = IAMData(account_id=account_id)
        
        # Parse Policies
        for pol_data in raw_data.get("Policies", []):
            try:
                policy = self._parse_managed_policy(pol_data)
                if policy:
                    iam_data.policies.append(policy)
            except Exception as e:
                logger.warning(f"Failed to parse policy {pol_data.get('PolicyName', 'unknown')}: {e}")
                
        # Parse Users
        for user_data in raw_data.get("UserDetailList", []):
            try:
                user = self._parse_user(user_data)
                if user:
                    iam_data.users.append(user)
            except Exception as e:
                logger.warning(f"Failed to parse user {user_data.get('UserName', 'unknown')}: {e}")

        # Parse Roles
        for role_data in raw_data.get("RoleDetailList", []):
            try:
                role = self._parse_role(role_data)
                if role:
                    iam_data.roles.append(role)
            except Exception as e:
                logger.warning(f"Failed to parse role {role_data.get('RoleName', 'unknown')}: {e}")

        # Parse Groups
        for group_data in raw_data.get("GroupDetailList", []):
            try:
                group = self._parse_group(group_data)
                if group:
                    iam_data.groups.append(group)
            except Exception as e:
                logger.warning(f"Failed to parse group {group_data.get('GroupName', 'unknown')}: {e}")

        return iam_data

    def _parse_managed_policy(self, data: Dict[str, Any]) -> Optional[IAMPolicy]:
        policy_name = data.get("PolicyName")
        if not policy_name:
            return None
        
        policy = IAMPolicy(
            policy_name=policy_name,
            policy_id=data.get("PolicyId", ""),
            arn=data.get("Arn", ""),
            path=data.get("Path", "/"),
            default_version_id=data.get("DefaultVersionId", "v1"),
            attachment_count=data.get("AttachmentCount", 0),
            is_attachable=data.get("IsAttachable", True)
        )
        
        # Extract the default policy version document
        versions = data.get("PolicyVersionList", [])
        for version in versions:
            if version.get("IsDefaultVersion"):
                doc_raw = version.get("Document")
                if doc_raw:
                    policy.document = self._parse_policy_document(doc_raw)
                break
                
        return policy

    def _parse_user(self, data: Dict[str, Any]) -> Optional[IAMUser]:
        user_name = data.get("UserName")
        if not user_name:
            return None
            
        user = IAMUser(
            user_name=user_name,
            user_id=data.get("UserId", ""),
            arn=data.get("Arn", ""),
            path=data.get("Path", "/"),
            group_list=data.get("GroupList", []),
            attached_managed_policies=self._parse_attached_policies(data.get("AttachedManagedPolicies", [])),
            inline_policies=self._parse_inline_policies(data.get("UserPolicyList", []))
        )
        return user

    def _parse_role(self, data: Dict[str, Any]) -> Optional[IAMRole]:
        role_name = data.get("RoleName")
        if not role_name:
            return None
            
        role = IAMRole(
            role_name=role_name,
            role_id=data.get("RoleId", ""),
            arn=data.get("Arn", ""),
            path=data.get("Path", "/"),
            attached_managed_policies=self._parse_attached_policies(data.get("AttachedManagedPolicies", [])),
            inline_policies=self._parse_inline_policies(data.get("RolePolicyList", [])),
            instance_profile_list=[ip.get("InstanceProfileName", "") for ip in data.get("InstanceProfileList", [])]
        )
        
        assume_doc = data.get("AssumeRolePolicyDocument")
        if assume_doc:
            role.assume_role_policy_document = self._parse_policy_document(assume_doc)
            
        return role

    def _parse_group(self, data: Dict[str, Any]) -> Optional[IAMGroup]:
        group_name = data.get("GroupName")
        if not group_name:
            return None
            
        group = IAMGroup(
            group_name=group_name,
            group_id=data.get("GroupId", ""),
            arn=data.get("Arn", ""),
            path=data.get("Path", "/"),
            attached_managed_policies=self._parse_attached_policies(data.get("AttachedManagedPolicies", [])),
            inline_policies=self._parse_inline_policies(data.get("GroupPolicyList", []))
        )
        return group

    def _parse_attached_policies(self, data: List[Dict[str, Any]]) -> List[ManagedPolicyAttachment]:
        attachments = []
        for att in data:
            if "PolicyName" in att and "PolicyArn" in att:
                attachments.append(ManagedPolicyAttachment(
                    policy_name=att["PolicyName"],
                    policy_arn=att["PolicyArn"]
                ))
        return attachments

    def _parse_inline_policies(self, data: List[Dict[str, Any]]) -> List[IAMPolicy]:
        policies = []
        for pol_data in data:
            name = pol_data.get("PolicyName")
            if not name:
                continue
            doc = pol_data.get("PolicyDocument")
            
            policy = IAMPolicy(
                policy_name=name,
                arn=f"inline-policy/{name}",
                document=self._parse_policy_document(doc) if doc else PolicyDocument()
            )
            policies.append(policy)
        return policies

    def _parse_policy_document(self, doc: Any) -> PolicyDocument:
        if isinstance(doc, str):
            # Sometimes URL encoded
            try:
                decoded = unquote(doc)
                doc = json.loads(decoded)
            except Exception:
                logger.warning("Failed to decode/parse string policy document.")
                return PolicyDocument()
                
        if not isinstance(doc, dict):
            return PolicyDocument()
            
        policy_doc = PolicyDocument(version=doc.get("Version", "2012-10-17"))
        
        statements = doc.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]
            
        for stmt in statements:
            if not isinstance(stmt, dict):
                continue
            parsed_stmt = self._parse_statement(stmt)
            if parsed_stmt:
                policy_doc.statements.append(parsed_stmt)
                
        return policy_doc

    def _parse_statement(self, stmt: Dict[str, Any]) -> Optional[PolicyStatement]:
        effect_str = stmt.get("Effect")
        if effect_str not in ["Allow", "Deny"]:
            return None
            
        effect = PolicyEffect.ALLOW if effect_str == "Allow" else PolicyEffect.DENY
        
        statement = PolicyStatement(
            sid=stmt.get("Sid"),
            effect=effect,
            actions=self._force_list(stmt.get("Action")),
            not_actions=self._force_list(stmt.get("NotAction")),
            resources=self._force_list(stmt.get("Resource")),
            not_resources=self._force_list(stmt.get("NotResource")),
            principals=self._parse_principals(stmt.get("Principal"))
        )
        
        # Parse conditions
        conditions_raw = stmt.get("Condition", {})
        if isinstance(conditions_raw, dict):
            for op, kv in conditions_raw.items():
                if isinstance(kv, dict):
                    for k, v in kv.items():
                        statement.conditions.append(PolicyCondition(
                            operator=op,
                            key=k,
                            values=self._force_list(v)
                        ))
        
        return statement
        
    def _parse_principals(self, principal: Any) -> List[str]:
        if not principal:
            return []
        if isinstance(principal, str):
            return [principal]
        if isinstance(principal, dict):
            res = []
            for k, v in principal.items():
                res.extend(self._force_list(v))
            return res
        if isinstance(principal, list):
            return [str(p) for p in principal]
        return []

    def _force_list(self, val: Any) -> List[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v) for v in val]
        return [str(val)]
