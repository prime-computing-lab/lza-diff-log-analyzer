"""
Operational and service risk analyzer
"""

from typing import List, Set, Dict, Any
from ..models.diff_models import DiffAnalysis, ResourceChange, ResourceCategory
from .base import BaseRiskAnalyzer, RiskFinding, RiskLevel, RiskCategory


class OperationalRiskAnalyzer(BaseRiskAnalyzer):
    """Analyzer for operational risks that could affect workload functionality"""
    
    def __init__(self):
        super().__init__(
            name="Operational Risk Analyzer",
            description="Analyzes changes that could impact workload operations, monitoring, and service reliability"
        )
        self.risk_category = RiskCategory.OPERATIONAL
        
        # Resources critical for workload operations
        self.operational_resources = {
            # Compute resources
            "AWS::EC2::Instance",
            "AWS::AutoScaling::AutoScalingGroup",
            "AWS::AutoScaling::LaunchConfiguration",
            "AWS::AutoScaling::LaunchTemplate",
            "AWS::ECS::Cluster",
            "AWS::ECS::Service",
            "AWS::ECS::TaskDefinition",
            "AWS::EKS::Cluster",
            "AWS::EKS::Nodegroup",
            "AWS::Lambda::Function",
            "AWS::Lambda::EventSourceMapping",
            
            # Storage resources
            "AWS::S3::Bucket",
            "AWS::S3::BucketPolicy",
            "AWS::EBS::Volume",
            "AWS::EFS::FileSystem",
            "AWS::FSx::FileSystem",
            
            # Database resources
            "AWS::RDS::DBInstance",
            "AWS::RDS::DBCluster",
            "AWS::RDS::DBSubnetGroup",
            "AWS::RDS::DBParameterGroup",
            "AWS::DynamoDB::Table",
            "AWS::ElastiCache::CacheCluster",
            "AWS::ElastiCache::ReplicationGroup",
            
            # Monitoring and logging
            "AWS::CloudWatch::Alarm",
            "AWS::CloudWatch::Dashboard",
            "AWS::Logs::LogGroup",
            "AWS::Logs::LogStream",
            "AWS::CloudTrail::Trail",
            
            # Load balancing and scaling
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            "AWS::ElasticLoadBalancingV2::Listener",
            "AWS::ApplicationAutoScaling::ScalableTarget",
            "AWS::ApplicationAutoScaling::ScalingPolicy",
            
            # Event and messaging
            "AWS::SNS::Topic",
            "AWS::SQS::Queue",
            "AWS::Events::Rule",
            "AWS::EventBridge::Rule",
            
            # Backup and disaster recovery
            "AWS::Backup::BackupPlan",
            "AWS::Backup::BackupVault",
            "AWS::DynamoDB::BackupPlan",
            
            # API and integration
            "AWS::ApiGateway::RestApi",
            "AWS::ApiGatewayV2::Api",
            "AWS::StepFunctions::StateMachine"
        }
        
        # Resources that if deleted could cause data loss
        self.data_loss_resources = {
            "AWS::S3::Bucket",
            "AWS::RDS::DBInstance",
            "AWS::RDS::DBCluster",
            "AWS::DynamoDB::Table",
            "AWS::EBS::Volume",
            "AWS::EFS::FileSystem",
            "AWS::FSx::FileSystem",
            "AWS::Backup::BackupVault",
            "AWS::Logs::LogGroup"
        }
        
        # Critical operational properties
        self.critical_operational_properties = {
            "InstanceType", "MinSize", "MaxSize", "DesiredCapacity",
            "TaskDefinition", "ServiceName", "ClusterName",
            "AlarmActions", "MetricName", "Threshold",
            "RetentionInDays", "DeletionPolicy", "BackupPolicy",
            "MultiAZ", "StorageType", "AllocatedStorage",
            "ProvisionedThroughput", "BillingMode",
            "HealthCheckType", "HealthCheckGracePeriod"
        }
    
    async def analyze(self, diff_analysis: DiffAnalysis) -> List[RiskFinding]:
        """Analyze operational risks in the diff"""
        findings = []
        
        for stack_diff in diff_analysis.stack_diffs:
            # Analyze operational resource changes
            findings.extend(self._analyze_operational_changes(stack_diff))
            
            # Analyze data loss risks
            findings.extend(self._analyze_data_loss_risks(stack_diff))
            
            # Analyze monitoring and alerting changes
            findings.extend(self._analyze_monitoring_changes(stack_diff))
            
            # Analyze scaling and performance changes
            findings.extend(self._analyze_scaling_changes(stack_diff))
        
        return findings
    
    def _analyze_operational_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes to operational resources"""
        findings = []
        
        operational_changes = [
            change for change in stack_diff.resource_changes
            if change.resource_type in self.operational_resources
        ]
        
        for change in operational_changes:
            if self._is_deletion(change):
                findings.append(self._analyze_operational_deletion(change, stack_diff.stack_name))
            elif self._is_modification(change):
                findings.extend(self._analyze_operational_modification(change, stack_diff.stack_name))
        
        return findings
    
    def _analyze_operational_deletion(self, change: ResourceChange, stack_name: str) -> RiskFinding:
        """Analyze deletion of operational resources"""
        # Assess risk level based on resource criticality
        risk_level = RiskLevel.MEDIUM
        
        # Critical compute and database resources
        if change.resource_type in [
            "AWS::RDS::DBInstance", "AWS::RDS::DBCluster", "AWS::DynamoDB::Table",
            "AWS::ECS::Service", "AWS::EKS::Cluster", "AWS::Lambda::Function"
        ]:
            risk_level = RiskLevel.HIGH
        
        # Infrastructure that affects multiple workloads
        if change.resource_type in [
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "AWS::AutoScaling::AutoScalingGroup"
        ]:
            risk_level = RiskLevel.HIGH
        
        # Impact assessment
        impact_map = {
            "AWS::Lambda::Function": "Loss of serverless function, breaking dependent applications",
            "AWS::ECS::Service": "Loss of containerized service, affecting application availability",
            "AWS::ECS::Cluster": "Loss of entire container cluster and all running services",
            "AWS::RDS::DBInstance": "Loss of database instance and potential data loss",
            "AWS::DynamoDB::Table": "Loss of NoSQL table and all stored data",
            "AWS::ElasticLoadBalancingV2::LoadBalancer": "Loss of load balancing, affecting application availability",
            "AWS::AutoScaling::AutoScalingGroup": "Loss of auto-scaling capability and compute capacity",
            "AWS::CloudWatch::Alarm": "Loss of monitoring and alerting for critical metrics",
            "AWS::SNS::Topic": "Loss of notification delivery mechanism",
            "AWS::SQS::Queue": "Loss of message queuing and processing capability"
        }
        
        impact = impact_map.get(
            change.resource_type,
            f"Loss of {change.resource_type} functionality"
        )
        
        # Affected workloads
        affected_workloads = self._identify_operational_workloads(change.resource_type)
        
        return self._create_finding(
            finding_id=f"OPS-DEL-{change.logical_id}",
            title=f"Operational Resource Deletion: {change.resource_type}",
            description=f"Operational resource '{change.logical_id}' is being deleted",
            risk_level=risk_level,
            stack_name=stack_name,
            resource_id=change.logical_id,
            resource_type=change.resource_type,
            change_type="deletion",
            impact_description=impact,
            affected_workloads=affected_workloads,
            recommendations=self._get_operational_deletion_recommendations(change.resource_type),
            rollback_steps=[
                "Restore resource configuration immediately",
                "Verify all dependent services are functioning",
                "Check application health and performance",
                "Monitor for any cascading failures"
            ],
            confidence_score=0.85,
            tags={"operational", "deletion", "workload_impact"}
        )
    
    def _analyze_operational_modification(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze modifications to operational resources"""
        findings = []
        
        # Check for critical property changes
        critical_changes = [
            prop.property_path for prop in (change.property_changes or [])
            if any(critical_prop.lower() in prop.property_path.lower() for critical_prop in self.critical_operational_properties)
        ]
        
        if critical_changes:
            risk_level = self._assess_operational_modification_risk(change.resource_type, critical_changes)
            
            findings.append(self._create_finding(
                finding_id=f"OPS-MOD-{change.logical_id}",
                title=f"Operational Configuration Change: {change.resource_type}",
                description=f"Critical operational properties modified in '{change.logical_id}': {', '.join(critical_changes)}",
                risk_level=risk_level,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description=self._get_operational_modification_impact(change.resource_type, critical_changes),
                affected_workloads=self._identify_operational_workloads(change.resource_type),
                recommendations=self._get_operational_modification_recommendations(change.resource_type, critical_changes),
                confidence_score=0.8,
                tags={"operational", "modification", "configuration_change"}
            ))
        
        # Specific analysis for different resource types
        if change.resource_type == "AWS::Lambda::Function":
            findings.extend(self._analyze_lambda_changes(change, stack_name))
        elif change.resource_type.startswith("AWS::RDS::"):
            findings.extend(self._analyze_rds_changes(change, stack_name))
        elif change.resource_type.startswith("AWS::AutoScaling::"):
            findings.extend(self._analyze_autoscaling_changes(change, stack_name))
        
        return findings
    
    def _analyze_data_loss_risks(self, stack_diff) -> List[RiskFinding]:
        """Analyze risks that could lead to data loss"""
        findings = []
        
        data_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in self.data_loss_resources
        ]
        
        for change in data_resources:
            if self._is_deletion(change):
                # Data loss from resource deletion
                findings.append(self._create_finding(
                    finding_id=f"DATA-LOSS-{change.logical_id}",
                    title=f"Potential Data Loss: {change.resource_type}",
                    description=f"Data-bearing resource '{change.logical_id}' is being deleted",
                    risk_level=RiskLevel.CRITICAL,
                    stack_name=stack_diff.stack_name,
                    resource_id=change.logical_id,
                    resource_type=change.resource_type,
                    change_type="deletion",
                    impact_description="Permanent loss of stored data",
                    affected_workloads=["All applications using this data store"],
                    recommendations=[
                        "STOP - Verify data backup exists before proceeding",
                        "Confirm this resource is no longer needed",
                        "Export/backup all critical data",
                        "Verify no applications depend on this data",
                        "Consider data migration to replacement resource"
                    ],
                    rollback_steps=[
                        "Restore from most recent backup immediately",
                        "Verify data integrity after restore",
                        "Check for any data loss since last backup"
                    ],
                    confidence_score=0.95,
                    tags={"data_loss", "critical", "backup_required"}
                ))
        
        return findings
    
    def _analyze_monitoring_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes to monitoring and alerting"""
        findings = []
        
        monitoring_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in [
                "AWS::CloudWatch::Alarm",
                "AWS::CloudWatch::Dashboard",
                "AWS::Logs::LogGroup",
                "AWS::CloudTrail::Trail"
            ]
        ]
        
        for change in monitoring_resources:
            if self._is_deletion(change):
                findings.append(self._create_finding(
                    finding_id=f"MON-DEL-{change.logical_id}",
                    title=f"Monitoring Resource Deletion: {change.resource_type}",
                    description=f"Monitoring resource '{change.logical_id}' is being deleted",
                    risk_level=RiskLevel.MEDIUM,
                    stack_name=stack_diff.stack_name,
                    resource_id=change.logical_id,
                    resource_type=change.resource_type,
                    change_type="deletion",
                    impact_description="Loss of monitoring, alerting, or logging capability",
                    recommendations=[
                        "Verify alternative monitoring exists",
                        "Ensure critical alerts are not lost",
                        "Check if logs are archived elsewhere",
                        "Consider impact on compliance requirements"
                    ],
                    confidence_score=0.7,
                    tags={"monitoring", "alerting", "observability"}
                ))
        
        return findings
    
    def _analyze_scaling_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes that could affect scaling and performance"""
        findings = []
        
        scaling_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in [
                "AWS::AutoScaling::AutoScalingGroup",
                "AWS::ApplicationAutoScaling::ScalableTarget",
                "AWS::ApplicationAutoScaling::ScalingPolicy"
            ]
        ]
        
        for change in scaling_resources:
            if self._is_modification(change):
                # Check for capacity or scaling changes
                scaling_props = [
                    prop.property_path for prop in (change.property_changes or [])
                    if any(scale_prop in prop.property_path.lower() for scale_prop in ["minsize", "maxsize", "desiredcapacity", "targetvalue"])
                ]
                
                if scaling_props:
                    findings.append(self._create_finding(
                        finding_id=f"SCALE-MOD-{change.logical_id}",
                        title=f"Scaling Configuration Change: {change.resource_type}",
                        description=f"Scaling properties modified in '{change.logical_id}': {', '.join(scaling_props)}",
                        risk_level=RiskLevel.MEDIUM,
                        stack_name=stack_diff.stack_name,
                        resource_id=change.logical_id,
                        resource_type=change.resource_type,
                        change_type="modification",
                        impact_description="Changes to scaling behavior may affect performance and cost",
                        recommendations=[
                            "Review new scaling parameters carefully",
                            "Ensure capacity is sufficient for expected load",
                            "Monitor scaling events after deployment",
                            "Verify cost implications of scaling changes"
                        ],
                        confidence_score=0.7,
                        tags={"scaling", "performance", "capacity"}
                    ))
        
        return findings
    
    def _analyze_lambda_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze Lambda function specific changes"""
        findings = []
        
        # Check for runtime or memory changes
        if self._has_property_change(change, "Runtime") or self._has_property_change(change, "MemorySize"):
            findings.append(self._create_finding(
                finding_id=f"LAMBDA-RUNTIME-{change.logical_id}",
                title=f"Lambda Runtime/Memory Change: {change.logical_id}",
                description=f"Lambda function runtime or memory configuration is being modified",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Runtime or memory changes may affect function performance and compatibility",
                recommendations=[
                    "Test function thoroughly with new configuration",
                    "Verify code compatibility with new runtime",
                    "Monitor execution duration and memory usage",
                    "Consider gradual rollout using aliases"
                ],
                confidence_score=0.8,
                tags={"lambda", "runtime", "performance"}
            ))
        
        return findings
    
    def _analyze_rds_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze RDS specific changes"""
        findings = []
        
        # Check for instance type or storage changes
        if self._has_property_change(change, "DBInstanceClass") or \
           self._has_property_change(change, "AllocatedStorage"):
            
            findings.append(self._create_finding(
                finding_id=f"RDS-CONFIG-{change.logical_id}",
                title=f"RDS Configuration Change: {change.logical_id}",
                description=f"RDS instance type or storage configuration is being modified",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Database configuration changes may cause downtime and affect performance",
                recommendations=[
                    "Plan maintenance window for changes",
                    "Backup database before modifications",
                    "Monitor database performance after changes",
                    "Test application connectivity during change"
                ],
                confidence_score=0.8,
                tags={"rds", "database", "performance", "downtime"}
            ))
        
        return findings
    
    def _analyze_autoscaling_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze Auto Scaling specific changes"""
        findings = []
        
        # Check for launch template or configuration changes
        if self._has_property_change(change, "LaunchTemplate") or \
           self._has_property_change(change, "LaunchConfigurationName"):
            
            findings.append(self._create_finding(
                finding_id=f"ASG-LAUNCH-{change.logical_id}",
                title=f"Auto Scaling Launch Configuration Change: {change.logical_id}",
                description=f"Auto Scaling Group launch configuration is being modified",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Launch configuration changes will affect new instances created by Auto Scaling",
                recommendations=[
                    "Test new launch configuration thoroughly",
                    "Consider rolling update strategy",
                    "Monitor instance health during rollout",
                    "Have rollback plan ready"
                ],
                confidence_score=0.8,
                tags={"autoscaling", "launch_config", "instances"}
            ))
        
        return findings
    
    def _assess_operational_modification_risk(self, resource_type: str, changed_properties: List[str]) -> RiskLevel:
        """Assess risk level for operational modifications"""
        # Critical changes that could cause immediate impact
        critical_props = {"InstanceType", "TaskDefinition", "AlarmActions", "DeletionPolicy"}
        
        if any(prop in critical_props for prop in changed_properties):
            return RiskLevel.HIGH
        
        # Capacity and scaling changes
        capacity_props = {"MinSize", "MaxSize", "DesiredCapacity", "MemorySize"}
        if any(prop in capacity_props for prop in changed_properties):
            return RiskLevel.MEDIUM
        
        return RiskLevel.MEDIUM
    
    def _get_operational_modification_impact(self, resource_type: str, changed_properties: List[str]) -> str:
        """Get impact description for operational modifications"""
        if "InstanceType" in changed_properties:
            return "Instance type changes may affect performance and require restarts"
        elif "TaskDefinition" in changed_properties:
            return "Task definition changes will trigger service updates and container restarts"
        elif any("size" in prop.lower() or "capacity" in prop.lower() for prop in changed_properties):
            return "Capacity changes may affect application performance and scaling behavior"
        else:
            return "Configuration changes may affect operational behavior"
    
    def _get_operational_deletion_recommendations(self, resource_type: str) -> List[str]:
        """Get recommendations for operational resource deletions"""
        base_recommendations = [
            "Verify no applications depend on this resource",
            "Check for downstream impacts on other services",
            "Consider maintenance window for deletion"
        ]
        
        specific_recommendations = {
            "AWS::Lambda::Function": [
                "Check all event sources and triggers",
                "Verify no API Gateway or other services invoke this function",
                "Review CloudWatch logs for recent usage"
            ],
            "AWS::RDS::DBInstance": [
                "CRITICAL: Ensure final snapshot is created",
                "Verify all applications have migrated to alternative database",
                "Export any required data before deletion"
            ],
            "AWS::ElasticLoadBalancingV2::LoadBalancer": [
                "Verify alternative load balancing exists",
                "Check all DNS records pointing to this load balancer",
                "Coordinate with application teams"
            ]
        }
        
        return base_recommendations + specific_recommendations.get(resource_type, [])
    
    def _get_operational_modification_recommendations(self, resource_type: str, changed_properties: List[str]) -> List[str]:
        """Get recommendations for operational modifications"""
        return [
            "Test changes in non-production environment first",
            "Monitor application performance after changes",
            "Have rollback plan ready",
            "Consider gradual rollout if possible",
            "Verify all dependent services remain functional"
        ]
    
    def _identify_operational_workloads(self, resource_type: str) -> List[str]:
        """Identify workloads affected by operational changes"""
        workload_map = {
            "AWS::Lambda::Function": [
                "Serverless applications",
                "Event-driven processes",
                "API backends"
            ],
            "AWS::ECS::Service": [
                "Containerized applications",
                "Microservices",
                "Web applications"
            ],
            "AWS::RDS::DBInstance": [
                "Database-dependent applications",
                "Web applications",
                "Data analytics workloads"
            ],
            "AWS::ElasticLoadBalancingV2::LoadBalancer": [
                "Web applications",
                "API services",
                "Multi-tier applications"
            ]
        }
        
        return workload_map.get(resource_type, ["Applications using this resource"])