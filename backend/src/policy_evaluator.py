import fnmatch
from typing import List, Dict, Tuple, Any
from src.models import PolicyStatement, PolicyEffect, EffectivePermission

class PolicyEvaluator:
    def __init__(self):
        pass

    def effective_permissions(
        self, 
        identity_arn: str, 
        statements: List[Tuple[str, PolicyStatement]],
        all_policies: List[Any] = None
    ) -> List[EffectivePermission]:
        """
        Evaluate IAM policy statements and return effective permissions.
        statements: list of tuples (source_policy_name/arn, PolicyStatement)
        """
        allows = []
        denies = []
        
        # We process each action/resource pair across all statements
        # Since AWS evaluates per action/resource, we can collect them.
        
        # In a real implementation, we would evaluate a specific request context.
        # For visualization, we extract the allow rules and remove those overridden by deny rules.
        
        for source, stmt in statements:
            if stmt.effect == PolicyEffect.ALLOW:
                allows.append((source, stmt))
            elif stmt.effect == PolicyEffect.DENY:
                denies.append((source, stmt))
                
        # Simple evaluation:
        # 1. Gather all allowed action/resource pairs.
        effective_perms = []
        
        for source, allow_stmt in allows:
            for action in allow_stmt.actions:
                for resource in allow_stmt.resources:
                    
                    # Check if this action/resource is denied
                    is_denied = False
                    for deny_source, deny_stmt in denies:
                        if self._matches_deny(action, resource, deny_stmt):
                            is_denied = True
                            break
                            
                    if not is_denied:
                        effective_perms.append(EffectivePermission(
                            action=action,
                            resource=resource,
                            effect=PolicyEffect.ALLOW,
                            source_policy=source,
                            conditions=allow_stmt.conditions
                        ))
                        
        return effective_perms

    def _matches_deny(self, action: str, resource: str, deny_stmt: PolicyStatement) -> bool:
        action_match = False
        if deny_stmt.actions:
            action_match = any(self._match_pattern(action, pat) for pat in deny_stmt.actions)
        elif deny_stmt.not_actions:
            action_match = not any(self._match_pattern(action, pat) for pat in deny_stmt.not_actions)
            
        if not action_match:
            return False
            
        resource_match = False
        if deny_stmt.resources:
            resource_match = any(self._match_pattern(resource, pat) for pat in deny_stmt.resources)
        elif deny_stmt.not_resources:
            resource_match = not any(self._match_pattern(resource, pat) for pat in deny_stmt.not_resources)
            
        return resource_match

    def _match_pattern(self, string: str, pattern: str) -> bool:
        # fnmatch does case-insensitive on Windows, but IAM is case-sensitive, though fnmatchcase is sensitive
        return fnmatch.fnmatchcase(string, pattern)
