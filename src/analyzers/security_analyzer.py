"""
Security and access risk analyzer
"""

import re
from typing import List, Set, Dict, Any
from ..models.diff_models import DiffAnalysis, ResourceChange, IAMStatementChange, ResourceCategory
from .base import BaseRiskAnalyzer, RiskFinding, RiskLevel, RiskCategory


class SecurityRiskAnalyzer(BaseRiskAnalyzer):
    """Analyzer for security and access-related risks"""
    
    def __init__(self):
        super().__init__(
            name="Security Risk Analyzer",
            description="Analyzes IAM, encryption, and security-related changes for potential risks"
        )
        self.risk_category = RiskCategory.SECURITY
        
        # Critical IAM actions that pose high risk
        self.high_risk_iam_actions = {
            # Admin and root access
            "*", "iam:*", "sts:AssumeRole", "sts:AssumeRoleWithSAML", "sts:AssumeRoleWithWebIdentity",
            
            # Resource manipulation
            "iam:CreateRole", "iam:DeleteRole", "iam:AttachRolePolicy", "iam:DetachRolePolicy",
            "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:UpdateAssumeRolePolicy",
            "iam:CreateUser", "iam:DeleteUser", "iam:AttachUserPolicy", "iam:DetachUserPolicy",
            "iam:PutUserPolicy", "iam:DeleteUserPolicy",
            
            # Security configuration
            "kms:CreateKey", "kms:DeleteKey", "kms:ScheduleKeyDeletion", "kms:PutKeyPolicy",
            "secretsmanager:DeleteSecret", "secretsmanager:PutSecretValue",
            
            # Organization and account management
            "organizations:*", "account:*",
            
            # Security services
            "config:DeleteConfigRule", "config:DeleteConfigurationRecorder",
            "cloudtrail:StopLogging", "cloudtrail:DeleteTrail",
            "guardduty:DeleteDetector", "securityhub:DisableSecurityHub"
        }
        
        # Sensitive resource types
        self.sensitive_resources = {
            "AWS::IAM::Role", "AWS::IAM::User", "AWS::IAM::Group", "AWS::IAM::Policy",
            "AWS::KMS::Key", "AWS::KMS::Alias",
            "AWS::SecretsManager::Secret",
            "AWS::SSM::Parameter",
            "AWS::Config::ConfigRule", "AWS::Config::ConfigurationRecorder",
            "AWS::CloudTrail::Trail",
            "AWS::GuardDuty::Detector",
            "AWS::SecurityHub::Hub",
            "AWS::Organizations::Account", "AWS::Organizations::OrganizationalUnit"
        }
    
    async def analyze(self, diff_analysis: DiffAnalysis) -> List[RiskFinding]:
        """Analyze security risks in the diff"""
        findings = []
        
        for stack_diff in diff_analysis.stack_diffs:
            # Analyze resource changes
            findings.extend(self._analyze_resource_changes(stack_diff))
            
            # Analyze IAM statement changes
            findings.extend(self._analyze_iam_changes(stack_diff))
        
        return findings
    
    def _analyze_resource_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze resource changes for security risks"""
        findings = []
        
        security_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in self.sensitive_resources
        ]
        
        for change in security_resources:
            # Check for deletions of security resources
            if self._is_deletion(change):
                findings.append(self._analyze_security_deletion(change, stack_diff.stack_name))
            
            # Check for modifications to security resources
            elif self._is_modification(change):
                findings.extend(self._analyze_security_modification(change, stack_diff.stack_name))
            
            # Check for new security resources
            elif self._is_addition(change):
                findings.extend(self._analyze_security_addition(change, stack_diff.stack_name))
        
        return findings
    
    def _analyze_security_deletion(self, change: ResourceChange, stack_name: str) -> RiskFinding:
        """Analyze deletion of security resources"""
        risk_level = RiskLevel.HIGH
        
        # Critical resources that should never be deleted
        if change.resource_type in ["AWS::KMS::Key", "AWS::CloudTrail::Trail", "AWS::Config::ConfigurationRecorder"]:
            risk_level = RiskLevel.CRITICAL
        
        # Determine impact based on resource type
        impact_map = {
            "AWS::IAM::Role": "Loss of access for applications and services using this role",
            "AWS::IAM::User": "Loss of access for user accounts and applications",
            "AWS::IAM::Policy": "Loss of permissions for resources using this policy",
            "AWS::KMS::Key": "Loss of encryption/decryption capability for encrypted resources",
            "AWS::SecretsManager::Secret": "Loss of stored credentials and secrets",
            "AWS::SSM::Parameter": "Loss of configuration parameters and secrets",
            "AWS::CloudTrail::Trail": "Loss of audit logging and compliance monitoring",
            "AWS::Config::ConfigRule": "Loss of compliance monitoring and configuration drift detection",
            "AWS::GuardDuty::Detector": "Loss of threat detection and security monitoring"
        }
        
        impact = impact_map.get(change.resource_type, "Unknown security impact")
        
        recommendations = [
            "Verify that this resource is no longer needed",
            "Ensure no applications or services depend on this resource",
            "Consider creating a backup or replacement before deletion",
            "Review all dependencies and references to this resource"
        ]
        
        # Add specific recommendations based on resource type
        if change.resource_type == "AWS::KMS::Key":
            recommendations.extend([
                "Ensure all encrypted resources have alternative encryption keys",
                "Check if any S3 buckets, RDS instances, or other services use this key",
                "Consider scheduling key deletion with a waiting period instead of immediate deletion"
            ])
        elif change.resource_type == "AWS::IAM::Role":
            recommendations.extend([
                "Verify no EC2 instances, Lambda functions, or other services use this role",
                "Check cross-account trust relationships that may depend on this role"
            ])
        
        return self._create_finding(
            finding_id=f"SEC-DEL-{change.logical_id}",
            title=f"Security Resource Deletion: {change.resource_type}",
            description=f"Security-sensitive resource '{change.logical_id}' of type {change.resource_type} is being deleted",
            risk_level=risk_level,
            stack_name=stack_name,
            resource_id=change.logical_id,
            resource_type=change.resource_type,
            change_type="deletion",
            impact_description=impact,
            recommendations=recommendations,
            affected_workloads=["All workloads using this security resource"],
            rollback_steps=[
                "Restore the resource configuration from backup",
                "Recreate the resource with identical configuration",
                "Verify all dependent resources are functioning"
            ],
            confidence_score=0.9,
            tags={"security", "deletion", change.resource_type.lower()}
        )
    
    def _analyze_security_modification(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze modifications to security resources"""
        findings = []
        
        # Analyze specific property changes
        if change.resource_type == "AWS::IAM::Role":
            findings.extend(self._analyze_iam_role_changes(change, stack_name))
        elif change.resource_type == "AWS::KMS::Key":
            findings.extend(self._analyze_kms_key_changes(change, stack_name))
        elif change.resource_type.startswith("AWS::IAM::"):
            findings.extend(self._analyze_generic_iam_changes(change, stack_name))
        
        return findings
    
    def _analyze_security_addition(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze addition of new security resources"""
        findings = []
        
        # New IAM roles with broad permissions are medium risk
        if change.resource_type == "AWS::IAM::Role":
            findings.append(self._create_finding(
                finding_id=f"SEC-NEW-{change.logical_id}",
                title=f"New IAM Role Created: {change.logical_id}",
                description=f"A new IAM role '{change.logical_id}' is being created",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="addition", 
                impact_description="New access permissions being granted",
                recommendations=[
                    "Review the role's trust policy and permissions",
                    "Ensure the role follows least privilege principle",
                    "Verify the role is necessary for the intended use case"
                ],
                confidence_score=0.7,
                tags={"security", "iam", "new_resource"}
            ))
        
        return findings
    
    def _analyze_iam_role_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze IAM role modifications"""
        findings = []
        
        # Check for trust policy changes
        if self._has_property_change(change, "AssumeRolePolicyDocument"):
            findings.append(self._create_finding(
                finding_id=f"SEC-TRUST-{change.logical_id}",
                title=f"IAM Role Trust Policy Change: {change.logical_id}",
                description=f"Trust policy for IAM role '{change.logical_id}' is being modified",
                risk_level=RiskLevel.HIGH,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Changes to who can assume this role and under what conditions",
                recommendations=[
                    "Review the new trust policy carefully",
                    "Ensure only authorized principals can assume the role",
                    "Verify external ID and condition requirements are appropriate",
                    "Check for overly permissive trust relationships"
                ],
                confidence_score=0.9,
                tags={"security", "iam", "trust_policy"}
            ))
        
        # Check for managed policy attachments
        if self._has_property_change(change, "ManagedPolicyArns"):
            findings.append(self._create_finding(
                finding_id=f"SEC-POLICY-{change.logical_id}",
                title=f"IAM Role Policy Attachment Change: {change.logical_id}",
                description=f"Managed policies attached to IAM role '{change.logical_id}' are being modified",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Changes to permissions granted to this role",
                recommendations=[
                    "Review all attached managed policies",
                    "Ensure new policies follow least privilege principle",
                    "Verify removed policies won't break functionality"
                ],
                confidence_score=0.8,
                tags={"security", "iam", "policies"}
            ))
        
        return findings
    
    def _analyze_kms_key_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze KMS key modifications"""
        findings = []
        
        if self._has_property_change(change, "KeyPolicy"):
            findings.append(self._create_finding(
                finding_id=f"SEC-KMS-{change.logical_id}",
                title=f"KMS Key Policy Change: {change.logical_id}",
                description=f"Key policy for KMS key '{change.logical_id}' is being modified",
                risk_level=RiskLevel.HIGH,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Changes to who can use the encryption key and perform key management operations",
                recommendations=[
                    "Review the new key policy carefully",
                    "Ensure only authorized principals have access",
                    "Verify key usage permissions are appropriate",
                    "Check that root user access is maintained for emergency recovery"
                ],
                affected_workloads=["All workloads using this KMS key for encryption"],
                confidence_score=0.9,
                tags={"security", "kms", "encryption"}
            ))
        
        return findings
    
    def _analyze_generic_iam_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze generic IAM resource changes"""
        findings = []
        
        # Any IAM resource modification is at least medium risk
        findings.append(self._create_finding(
            finding_id=f"SEC-IAM-{change.logical_id}",
            title=f"IAM Resource Modified: {change.resource_type}",
            description=f"IAM resource '{change.logical_id}' of type {change.resource_type} is being modified",
            risk_level=RiskLevel.MEDIUM,
            stack_name=stack_name,
            resource_id=change.logical_id,
            resource_type=change.resource_type,
            change_type="modification",
            impact_description="Changes to access control and permissions",
            recommendations=[
                "Review all changes to the IAM resource",
                "Ensure changes follow least privilege principle",
                "Verify changes don't break existing functionality",
                "Test changes in non-production environment first"
            ],
            confidence_score=0.7,
            tags={"security", "iam", "modification"}
        ))
        
        return findings
    
    def _analyze_iam_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze IAM statement changes"""
        findings = []
        
        for iam_change in stack_diff.iam_statement_changes:
            findings.extend(self._analyze_iam_statement_change(iam_change, stack_diff.stack_name))
        
        return findings
    
    def _analyze_iam_statement_change(self, iam_change: IAMStatementChange, stack_name: str) -> List[RiskFinding]:
        """Analyze individual IAM statement changes"""
        findings = []
        
        # Check for high-risk actions
        if iam_change.action:
            actions = iam_change.action if isinstance(iam_change.action, list) else [iam_change.action]
            high_risk_actions = [action for action in actions if self._is_high_risk_action(action)]
            
            if high_risk_actions:
                risk_level = RiskLevel.CRITICAL if "*" in high_risk_actions else RiskLevel.HIGH
                
                resource_str = str(iam_change.resource) if iam_change.resource else "unknown"
                findings.append(self._create_finding(
                    finding_id=f"SEC-IAM-STMT-{hash(resource_str)}",
                    title=f"High-Risk IAM Permissions: {resource_str}",
                    description=f"IAM statement with high-risk actions detected for resource '{resource_str}'",
                    risk_level=risk_level,
                    stack_name=stack_name,
                    resource_id=resource_str,
                    resource_type="IAM::Statement",
                    change_type=iam_change.change_type.value,
                    impact_description=f"Grants potentially dangerous permissions: {', '.join(high_risk_actions)}",
                    recommendations=[
                        "Review if these broad permissions are necessary",
                        "Consider using more specific, granular permissions",
                        "Implement condition statements to limit scope",
                        "Regularly audit usage of these permissions"
                    ],
                    affected_workloads=["All workloads using this IAM resource"],
                    confidence_score=0.95,
                    tags={"security", "iam", "high_risk_actions"}
                ))
        
        # Check for resource scope
        resource_str = str(iam_change.resource) if iam_change.resource else "unknown"
        resources = iam_change.resource if isinstance(iam_change.resource, list) else [iam_change.resource] if iam_change.resource else []
        if resources and "*" in str(resources):
            findings.append(self._create_finding(
                finding_id=f"SEC-IAM-WILDCARD-{hash(resource_str)}",
                title=f"Wildcard Resource Access: {resource_str}",
                description=f"IAM statement with wildcard resource access detected for '{resource_str}'",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=resource_str,
                resource_type="IAM::Statement",
                change_type=iam_change.change_type.value,
                impact_description="Grants access to all resources of the specified type",
                recommendations=[
                    "Consider specifying explicit resource ARNs instead of wildcards",
                    "Use condition statements to limit resource scope",
                    "Regularly review and minimize wildcard usage"
                ],
                confidence_score=0.8,
                tags={"security", "iam", "wildcard"}
            ))
        
        return findings
    
    def _is_high_risk_action(self, action: str) -> bool:
        """Check if an IAM action is high risk"""
        # Direct match
        if action in self.high_risk_iam_actions:
            return True
        
        # Pattern matching for wildcards
        for risk_action in self.high_risk_iam_actions:
            if "*" in risk_action:
                pattern = risk_action.replace("*", ".*")
                if re.match(pattern, action):
                    return True
        
        return False