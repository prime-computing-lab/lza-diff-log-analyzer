"""
Operational compliance risk analyzer for cloud administrators
"""

from typing import List, Set, Dict, Any
from ..models.diff_models import DiffAnalysis, ResourceChange, ResourceCategory
from .base import BaseRiskAnalyzer, RiskFinding, RiskLevel, RiskCategory


class OperationalComplianceAnalyzer(BaseRiskAnalyzer):
    """Analyzer for operational compliance risks relevant to cloud administrators"""
    
    def __init__(self):
        super().__init__(
            name="Operational Compliance Analyzer",
            description="Analyzes changes that could impact operational compliance and audit requirements"
        )
        self.risk_category = RiskCategory.COMPLIANCE
        
        # Resources critical for operational compliance and auditing
        self.operational_compliance_resources = {
            # Auditing and logging - essential for operations
            "AWS::CloudTrail::Trail",
            "AWS::Config::ConfigRule",
            "AWS::Config::ConfigurationRecorder",
            "AWS::Config::DeliveryChannel",
            "AWS::Logs::LogGroup",
            
            # Security monitoring - operational security
            "AWS::GuardDuty::Detector",
            "AWS::SecurityHub::Hub",
            "AWS::AccessAnalyzer::Analyzer",
            
            # LZA governance controls
            "AWS::Organizations::Policy",
            "AWS::ControlTower::EnabledControl",
            
            # IAM for operational access
            "AWS::IAM::Role",
            "AWS::IAM::Policy",
            "AWS::SSO::PermissionSet",
            
            # Encryption for operational security
            "AWS::KMS::Key",
            "AWS::KMS::Alias",
            
            # Backup for operational continuity
            "AWS::Backup::BackupPlan",
            "AWS::Backup::BackupVault",
            "AWS::S3::Bucket"
        }
        
        # Operational compliance areas for cloud administrators
        self.operational_areas = {
            "audit_logging": {
                "resources": ["AWS::CloudTrail::Trail", "AWS::Logs::LogGroup"],
                "description": "Audit trail and operational logging"
            },
            "configuration_monitoring": {
                "resources": ["AWS::Config::ConfigRule", "AWS::Config::ConfigurationRecorder"],
                "description": "Configuration compliance monitoring"
            },
            "security_monitoring": {
                "resources": ["AWS::GuardDuty::Detector", "AWS::SecurityHub::Hub"],
                "description": "Security event monitoring and alerting"
            },
            "access_management": {
                "resources": ["AWS::IAM::Role", "AWS::IAM::Policy", "AWS::SSO::PermissionSet"],
                "description": "Identity and access management"
            },
            "data_protection": {
                "resources": ["AWS::KMS::Key", "AWS::Backup::BackupPlan"],
                "description": "Data encryption and backup protection"
            },
            "governance_controls": {
                "resources": ["AWS::Organizations::Policy", "AWS::ControlTower::EnabledControl"],
                "description": "LZA governance and organizational controls"
            }
        }
        
        # Critical operational properties
        self.operational_critical_properties = {
            "LoggingEnabled", "RetentionInDays", "IncludeGlobalServiceEvents",
            "IsMultiRegionTrail", "EnableLogFileValidation",
            "EncryptionConfiguration", "DeletionPolicy", "BackupPolicy"
        }
    
    async def analyze(self, diff_analysis: DiffAnalysis) -> List[RiskFinding]:
        """Analyze operational compliance risks"""
        findings = []
        
        for stack_diff in diff_analysis.stack_diffs:
            # Analyze operational compliance resource changes
            findings.extend(self._analyze_operational_compliance_changes(stack_diff))
            
            # Analyze audit and logging changes
            findings.extend(self._analyze_audit_changes(stack_diff))
            
            # Analyze LZA governance changes
            findings.extend(self._analyze_lza_governance_changes(stack_diff))
        
        return findings
    
    def _analyze_operational_compliance_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes to operationally critical compliance resources"""
        findings = []
        
        compliance_changes = [
            change for change in stack_diff.resource_changes
            if change.resource_type in self.operational_compliance_resources
        ]
        
        for change in compliance_changes:
            if self._is_deletion(change):
                findings.append(self._analyze_compliance_deletion(change, stack_diff.stack_name))
            elif self._is_modification(change):
                findings.extend(self._analyze_compliance_modification(change, stack_diff.stack_name))
        
        return findings
    
    def _analyze_compliance_deletion(self, change: ResourceChange, stack_name: str) -> RiskFinding:
        """Analyze deletion of operationally critical compliance resources"""
        # Assess risk level based on compliance criticality
        risk_level = RiskLevel.HIGH
        
        # Critical operational compliance infrastructure
        if change.resource_type in [
            "AWS::CloudTrail::Trail",
            "AWS::Config::ConfigRule",
            "AWS::Config::ConfigurationRecorder"
        ]:
            risk_level = RiskLevel.CRITICAL
        
        # Assess impact on operational areas
        affected_areas = self._get_affected_operational_areas(change.resource_type)
        
        # Impact assessment
        impact_map = {
            "AWS::CloudTrail::Trail": "Loss of audit logging, violating most compliance frameworks",
            "AWS::Config::ConfigRule": "Loss of configuration compliance monitoring",
            "AWS::Config::ConfigurationRecorder": "Loss of resource configuration tracking",
            "AWS::GuardDuty::Detector": "Loss of threat detection and security monitoring",
            "AWS::SecurityHub::Hub": "Loss of centralized security findings and compliance status",
            "AWS::KMS::Key": "Loss of encryption capability, affecting data protection compliance",
            "AWS::Backup::BackupPlan": "Loss of data backup and recovery capability",
            "AWS::Organizations::Policy": "Loss of organizational governance and control"
        }
        
        impact = impact_map.get(
            change.resource_type,
            f"Loss of compliance control: {change.resource_type}"
        )
        
        # Add operational area impact
        if affected_areas:
            impact += f" Affects operational areas: {', '.join(affected_areas)}"
        
        return self._create_finding(
            finding_id=f"COMP-DEL-{change.logical_id}",
            title=f"Compliance Resource Deletion: {change.resource_type}",
            description=f"Compliance-critical resource '{change.logical_id}' is being deleted",
            risk_level=risk_level,
            stack_name=stack_name,
            resource_id=change.logical_id,
            resource_type=change.resource_type,
            change_type="deletion",
            impact_description=impact,
            affected_workloads=["All workloads subject to compliance requirements"],
            recommendations=self._get_operational_deletion_recommendations(change.resource_type, affected_areas),
            rollback_steps=[
                "Immediately restore compliance resource",
                "Verify compliance monitoring is restored",
                "Check for any compliance violations during outage",
                "Document incident for compliance reporting"
            ],
            confidence_score=0.95,
            tags={"operational_compliance", "audit", "critical"}
        )
    
    def _analyze_compliance_modification(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze modifications to compliance resources"""
        findings = []
        
        # Check for critical operational property changes
        critical_changes = [
            prop.property_path for prop in (change.property_changes or [])
            if any(critical_prop.lower() in prop.property_path.lower() for critical_prop in self.operational_critical_properties)
        ]
        
        if critical_changes:
            risk_level = self._assess_operational_modification_risk(change.resource_type, critical_changes)
            affected_areas = self._get_affected_operational_areas(change.resource_type)
            
            findings.append(self._create_finding(
                finding_id=f"COMP-MOD-{change.logical_id}",
                title=f"Compliance Configuration Change: {change.resource_type}",
                description=f"Compliance-critical properties modified in '{change.logical_id}': {', '.join(critical_changes)}",
                risk_level=risk_level,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description=self._get_operational_modification_impact(change.resource_type, critical_changes, affected_areas),
                affected_workloads=["All workloads requiring operational compliance"],
                recommendations=self._get_operational_modification_recommendations(change.resource_type, critical_changes),
                confidence_score=0.85,
                tags={"operational_compliance", "configuration_change"}
            ))
        
        return findings
    
    def _analyze_lza_governance_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes affecting LZA governance controls"""
        findings = []
        
        governance_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in [
                "AWS::Organizations::Policy",
                "AWS::ControlTower::EnabledControl"
            ]
        ]
        
        for change in governance_resources:
            if self._is_deletion(change) or self._is_modification(change):
                findings.append(self._create_finding(
                    finding_id=f"LZA-GOV-{change.logical_id}",
                    title=f"LZA Governance Change: {change.resource_type}",
                    description=f"LZA governance resource '{change.logical_id}' is being modified",
                    risk_level=RiskLevel.HIGH,
                    stack_name=stack_diff.stack_name,
                    resource_id=change.logical_id,
                    resource_type=change.resource_type,
                    change_type=change.change_type.value,
                    impact_description="Changes to LZA governance controls and organizational policies",
                    affected_workloads=["All LZA managed accounts and workloads"],
                    recommendations=[
                        "Review impact on all LZA managed accounts",
                        "Verify changes align with LZA governance model",
                        "Test governance controls in non-production first",
                        "Document changes for operational records",
                        "Validate Control Tower integration remains functional"
                    ],
                    confidence_score=0.9,
                    tags={"lza_governance", "operational_compliance", "control_tower"}
                ))
        
        return findings
    
    def _analyze_audit_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes to audit and logging systems"""
        findings = []
        
        audit_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in [
                "AWS::CloudTrail::Trail",
                "AWS::Logs::LogGroup",
                "AWS::Config::ConfigRule"
            ]
        ]
        
        for change in audit_resources:
            if self._is_modification(change):
                # Check for logging configuration changes
                logging_changes = [
                    prop.property_path for prop in (change.property_changes or [])
                    if any(log_prop in prop.property_path.lower() for log_prop in ["logging", "retention", "delivery"])
                ]
                
                if logging_changes:
                    findings.append(self._create_finding(
                        finding_id=f"AUDIT-{change.logical_id}",
                        title=f"Audit Logging Change: {change.resource_type}",
                        description=f"Audit logging configuration modified in '{change.logical_id}'",
                        risk_level=RiskLevel.MEDIUM,
                        stack_name=stack_diff.stack_name,
                        resource_id=change.logical_id,
                        resource_type=change.resource_type,
                        change_type="modification",
                        impact_description="Changes to audit logging may affect compliance monitoring and forensic capabilities",
                        recommendations=[
                            "Verify logging requirements are still met",
                            "Check retention periods comply with regulations",
                            "Ensure log delivery mechanisms are functional",
                            "Test log analysis and alerting systems"
                        ],
                        confidence_score=0.8,
                        tags={"audit", "logging", "compliance"}
                    ))
        
        return findings
    
    
    def _get_affected_operational_areas(self, resource_type: str) -> List[str]:
        """Identify which operational areas are affected by resource changes"""
        affected = []
        
        for area_name, area_config in self.operational_areas.items():
            if resource_type in area_config['resources']:
                affected.append(area_config['description'])
        
        return affected
    
    def _assess_operational_modification_risk(self, resource_type: str, changed_properties: List[str]) -> RiskLevel:
        """Assess risk level for operational compliance modifications"""
        # Critical operational properties
        critical_props = {"LoggingEnabled", "RetentionInDays", "EncryptionConfiguration", "DeletionPolicy"}
        
        if any(prop in critical_props for prop in changed_properties):
            return RiskLevel.HIGH
        
        # Audit and monitoring properties
        audit_props = {"IncludeGlobalServiceEvents", "IsMultiRegionTrail", "EnableLogFileValidation"}
        if any(prop in audit_props for prop in changed_properties):
            return RiskLevel.MEDIUM
        
        return RiskLevel.MEDIUM
    
    def _get_operational_modification_impact(self, resource_type: str, changed_properties: List[str], affected_areas: List[str]) -> str:
        """Get impact description for operational compliance modifications"""
        base_impact = f"Changes to {resource_type} configuration may affect operational compliance"
        
        if "LoggingEnabled" in changed_properties:
            base_impact = "Changes to logging configuration may affect audit trail and operational visibility"
        elif "RetentionInDays" in changed_properties:
            base_impact = "Changes to retention policy may affect operational audit requirements"
        elif "EncryptionConfiguration" in changed_properties:
            base_impact = "Changes to encryption may affect operational data protection"
        
        if affected_areas:
            base_impact += f". Potentially affects: {', '.join(affected_areas)}"
        
        return base_impact
    
    def _get_operational_deletion_recommendations(self, resource_type: str, affected_areas: List[str]) -> List[str]:
        """Get recommendations for operational compliance resource deletions"""
        base_recommendations = [
            "STOP - Review operational requirements before proceeding",
            "Verify alternative operational controls exist",
            "Document operational justification for change",
            "Coordinate with operations team"
        ]
        
        specific_recommendations = {
            "AWS::CloudTrail::Trail": [
                "Ensure alternative audit logging exists",
                "Verify operational audit trail requirements",
                "Check if logs are archived in another location",
                "Test operational monitoring after change"
            ],
            "AWS::Config::ConfigRule": [
                "Verify alternative configuration monitoring exists",
                "Ensure operational monitoring is not affected",
                "Document configuration compliance impact",
                "Test alert systems after change"
            ],
            "AWS::KMS::Key": [
                "Ensure all encrypted data has alternative keys",
                "Verify operational encryption requirements",
                "Plan key rotation and migration strategy",
                "Test application functionality after change"
            ]
        }
        
        recommendations = base_recommendations + specific_recommendations.get(resource_type, [])
        
        if affected_areas:
            recommendations.append(f"Review impact on operational areas: {', '.join(affected_areas)}")
        
        return recommendations
    
    def _get_operational_modification_recommendations(self, resource_type: str, changed_properties: List[str]) -> List[str]:
        """Get recommendations for operational compliance modifications"""
        return [
            "Review changes against operational requirements",
            "Verify operational monitoring remains functional",
            "Test operational systems after changes",
            "Document changes for operational records",
            "Coordinate with operations team before deployment",
            "Validate operational impact in non-production first"
        ]