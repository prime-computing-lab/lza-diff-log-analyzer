"""
Network connectivity risk analyzer
"""

import re
from typing import List, Set, Dict, Any
from ..models.diff_models import DiffAnalysis, ResourceChange, ResourceCategory
from .base import BaseRiskAnalyzer, RiskFinding, RiskLevel, RiskCategory


class NetworkRiskAnalyzer(BaseRiskAnalyzer):
    """Analyzer for network connectivity and infrastructure risks"""
    
    def __init__(self):
        super().__init__(
            name="Network Risk Analyzer",
            description="Analyzes network changes that could impact connectivity, especially hub-spoke architectures"
        )
        self.risk_category = RiskCategory.CONNECTIVITY
        
        # Critical network resources for enterprise connectivity
        self.critical_network_resources = {
            # Transit Gateway resources (hub-spoke critical)
            "AWS::EC2::TransitGateway",
            "AWS::EC2::TransitGatewayAttachment",
            "AWS::EC2::TransitGatewayRouteTable",
            "AWS::EC2::TransitGatewayRoute",
            "AWS::EC2::TransitGatewayRouteTableAssociation",
            "AWS::EC2::TransitGatewayRouteTablePropagation",
            
            # Direct Connect (on-premises connectivity)
            "AWS::DirectConnect::VirtualInterface",
            "AWS::DirectConnect::Connection",
            "AWS::DirectConnect::LAG",
            
            # VPN connections
            "AWS::EC2::VPNConnection",
            "AWS::EC2::VPNGateway",
            "AWS::EC2::CustomerGateway",
            
            # VPC and core networking
            "AWS::EC2::VPC",
            "AWS::EC2::Subnet",
            "AWS::EC2::RouteTable",
            "AWS::EC2::Route",
            "AWS::EC2::InternetGateway",
            "AWS::EC2::NATGateway",
            "AWS::EC2::EgressOnlyInternetGateway",
            
            # VPC Peering
            "AWS::EC2::VPCPeeringConnection",
            
            # DNS and service discovery
            "AWS::Route53::HostedZone",
            "AWS::Route53Resolver::ResolverRule",
            "AWS::Route53Resolver::ResolverEndpoint",
            
            # Load balancers (workload connectivity)
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            
            # Security groups and NACLs
            "AWS::EC2::SecurityGroup",
            "AWS::EC2::NetworkAcl",
            
            # VPC Endpoints (service connectivity)
            "AWS::EC2::VPCEndpoint",
            "AWS::EC2::VPCEndpointService"
        }
        
        # Hub-spoke specific patterns
        self.hub_spoke_indicators = {
            "transit", "hub", "spoke", "shared", "connectivity", "networking"
        }
        
        # Critical network properties that affect connectivity
        self.critical_network_properties = {
            "CidrBlock", "RouteTableId", "DestinationCidrBlock", "GatewayId",
            "TransitGatewayId", "VpcId", "SubnetId", "SecurityGroupRules",
            "Ingress", "Egress", "FromPort", "ToPort", "IpProtocol",
            "AttachmentId", "PropagationRouteTableIds", "AssociationRouteTableIds"
        }
    
    async def analyze(self, diff_analysis: DiffAnalysis) -> List[RiskFinding]:
        """Analyze network connectivity risks"""
        findings = []
        
        for stack_diff in diff_analysis.stack_diffs:
            # Analyze network resource changes
            findings.extend(self._analyze_network_changes(stack_diff))
            
            # Analyze hub-spoke specific risks
            findings.extend(self._analyze_hub_spoke_risks(stack_diff))
            
            # Analyze cross-account network risks
            findings.extend(self._analyze_cross_account_network_risks(stack_diff))
        
        return findings
    
    def _analyze_network_changes(self, stack_diff) -> List[RiskFinding]:
        """Analyze changes to network resources"""
        findings = []
        
        network_changes = [
            change for change in stack_diff.resource_changes
            if change.resource_type in self.critical_network_resources
        ]
        
        for change in network_changes:
            if self._is_deletion(change):
                findings.append(self._analyze_network_deletion(change, stack_diff.stack_name))
            elif self._is_modification(change):
                findings.extend(self._analyze_network_modification(change, stack_diff.stack_name))
            elif self._is_addition(change):
                findings.extend(self._analyze_network_addition(change, stack_diff.stack_name))
        
        return findings
    
    def _analyze_network_deletion(self, change: ResourceChange, stack_name: str) -> RiskFinding:
        """Analyze deletion of network resources"""
        # Determine risk level based on resource criticality
        risk_level = RiskLevel.HIGH
        
        # Critical infrastructure that could break everything
        if change.resource_type in [
            "AWS::EC2::TransitGateway",
            "AWS::DirectConnect::VirtualInterface",
            "AWS::EC2::VPNConnection"
        ]:
            risk_level = RiskLevel.CRITICAL
        
        # Impact assessment by resource type
        impact_map = {
            "AWS::EC2::TransitGateway": "Complete loss of hub-spoke connectivity across the organization",
            "AWS::EC2::TransitGatewayAttachment": "Loss of connectivity for specific VPC to the transit gateway",
            "AWS::EC2::TransitGatewayRouteTable": "Loss of routing configuration for transit gateway connections",
            "AWS::DirectConnect::VirtualInterface": "Loss of dedicated network connection to on-premises",
            "AWS::EC2::VPNConnection": "Loss of VPN connectivity to on-premises or remote sites",
            "AWS::EC2::VPC": "Complete loss of network infrastructure and all contained resources",
            "AWS::EC2::Subnet": "Loss of network segment, affecting all resources in the subnet",
            "AWS::EC2::RouteTable": "Loss of routing configuration, potentially isolating resources",
            "AWS::EC2::Route": "Loss of specific network route, potentially breaking connectivity",
            "AWS::EC2::InternetGateway": "Loss of internet connectivity for the VPC",
            "AWS::EC2::NATGateway": "Loss of outbound internet access for private subnets",
            "AWS::Route53Resolver::ResolverRule": "Loss of DNS resolution for specific domains",
            "AWS::ElasticLoadBalancingV2::LoadBalancer": "Loss of load balancing and application access",
            "AWS::EC2::VPCEndpoint": "Loss of private connectivity to AWS services"
        }
        
        impact = impact_map.get(
            change.resource_type,
            "Loss of network connectivity or functionality"
        )
        
        # Workloads that could be affected
        affected_workloads = self._identify_affected_workloads(change.resource_type)
        
        # Recommendations based on resource type
        recommendations = self._get_network_deletion_recommendations(change.resource_type)
        
        return self._create_finding(
            finding_id=f"NET-DEL-{change.logical_id}",
            title=f"Critical Network Resource Deletion: {change.resource_type}",
            description=f"Network resource '{change.logical_id}' of type {change.resource_type} is being deleted",
            risk_level=risk_level,
            stack_name=stack_name,
            resource_id=change.logical_id,
            resource_type=change.resource_type,
            change_type="deletion",
            impact_description=impact,
            affected_workloads=affected_workloads,
            recommendations=recommendations,
            rollback_steps=[
                "Immediately restore the network resource configuration",
                "Verify all dependent resources are reconnected",
                "Test connectivity from all affected workloads",
                "Monitor network traffic to ensure normal operation"
            ],
            confidence_score=0.95,
            tags={"network", "connectivity", "deletion", "critical"}
        )
    
    def _analyze_network_modification(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze modifications to network resources"""
        findings = []
        
        # Check for critical property changes
        critical_changes = [
            prop.property_path for prop in (change.property_changes or [])
            if any(critical_prop.lower() in prop.property_path.lower() for critical_prop in self.critical_network_properties)
        ]
        
        if critical_changes:
            risk_level = self._assess_network_modification_risk(change.resource_type, critical_changes)
            
            findings.append(self._create_finding(
                finding_id=f"NET-MOD-{change.logical_id}",
                title=f"Network Configuration Change: {change.resource_type}",
                description=f"Critical network properties modified in '{change.logical_id}': {', '.join(critical_changes)}",
                risk_level=risk_level,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description=self._get_modification_impact(change.resource_type, critical_changes),
                affected_workloads=self._identify_affected_workloads(change.resource_type),
                recommendations=self._get_network_modification_recommendations(change.resource_type, critical_changes),
                confidence_score=0.85,
                tags={"network", "connectivity", "modification"}
            ))
        
        # Special analysis for specific resource types
        if change.resource_type == "AWS::EC2::SecurityGroup":
            findings.extend(self._analyze_security_group_changes(change, stack_name))
        elif change.resource_type.startswith("AWS::EC2::TransitGateway"):
            findings.extend(self._analyze_transit_gateway_changes(change, stack_name))
        
        return findings
    
    def _analyze_network_addition(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze addition of new network resources"""
        findings = []
        
        # New network resources are generally lower risk but worth noting
        if change.resource_type in ["AWS::EC2::SecurityGroup", "AWS::EC2::Route"]:
            findings.append(self._create_finding(
                finding_id=f"NET-NEW-{change.logical_id}",
                title=f"New Network Resource: {change.resource_type}",
                description=f"New network resource '{change.logical_id}' is being created",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="addition",
                impact_description="New network configuration that may affect connectivity",
                recommendations=[
                    "Review the new network configuration",
                    "Ensure it doesn't conflict with existing network rules",
                    "Test connectivity after deployment",
                    "Verify it follows network security best practices"
                ],
                confidence_score=0.6,
                tags={"network", "new_resource"}
            ))
        
        return findings
    
    def _analyze_hub_spoke_risks(self, stack_diff) -> List[RiskFinding]:
        """Analyze risks specific to hub-spoke architectures"""
        findings = []
        
        # Look for hub-spoke indicators in stack name or resource names
        is_hub_spoke_stack = any(
            indicator in stack_diff.stack_name.lower()
            for indicator in self.hub_spoke_indicators
        )
        
        if is_hub_spoke_stack:
            # Higher risk assessment for hub-spoke infrastructure
            transit_gateway_changes = [
                change for change in stack_diff.resource_changes
                if "TransitGateway" in change.resource_type
            ]
            
            for change in transit_gateway_changes:
                if self._is_deletion(change) or self._is_modification(change):
                    findings.append(self._create_finding(
                        finding_id=f"HUB-SPOKE-{change.logical_id}",
                        title=f"Hub-Spoke Infrastructure Change: {change.resource_type}",
                        description=f"Change to hub-spoke critical resource '{change.logical_id}' detected",
                        risk_level=RiskLevel.CRITICAL,
                        stack_name=stack_diff.stack_name,
                        resource_id=change.logical_id,
                        resource_type=change.resource_type,
                        change_type=change.change_type.value,
                        impact_description="Potential disruption to organization-wide hub-spoke connectivity",
                        affected_workloads=[
                            "All spoke VPCs and workloads",
                            "Cross-account connectivity",
                            "On-premises to cloud connectivity",
                            "Shared services access"
                        ],
                        recommendations=[
                            "Coordinate with all spoke VPC owners before proceeding",
                            "Plan maintenance window for the change",
                            "Have rollback plan ready",
                            "Test connectivity from multiple spoke VPCs after change",
                            "Monitor all transit gateway attachments and routes"
                        ],
                        confidence_score=0.9,
                        tags={"hub_spoke", "critical_infrastructure", "organization_wide"}
                    ))
        
        return findings
    
    def _analyze_cross_account_network_risks(self, stack_diff) -> List[RiskFinding]:
        """Analyze risks that could affect cross-account connectivity"""
        findings = []
        
        # Look for resources that typically enable cross-account access
        cross_account_resources = [
            change for change in stack_diff.resource_changes
            if change.resource_type in [
                "AWS::EC2::TransitGatewayAttachment",
                "AWS::EC2::VPCPeeringConnection",
                "AWS::RAM::ResourceShare"  # Resource Access Manager
            ]
        ]
        
        for change in cross_account_resources:
            if self._is_deletion(change):
                findings.append(self._create_finding(
                    finding_id=f"CROSS-ACCT-{change.logical_id}",
                    title=f"Cross-Account Network Resource Deletion: {change.resource_type}",
                    description=f"Resource '{change.logical_id}' that enables cross-account connectivity is being deleted",
                    risk_level=RiskLevel.HIGH,
                    stack_name=stack_diff.stack_name,
                    resource_id=change.logical_id,
                    resource_type=change.resource_type,
                    change_type="deletion",
                    impact_description="Loss of connectivity between AWS accounts",
                    affected_workloads=["Workloads in connected AWS accounts"],
                    recommendations=[
                        "Coordinate with owners of connected AWS accounts",
                        "Verify no cross-account workloads depend on this connectivity",
                        "Plan alternative connectivity if needed",
                        "Notify all affected account owners before proceeding"
                    ],
                    confidence_score=0.8,
                    tags={"cross_account", "connectivity"}
                ))
        
        return findings
    
    def _analyze_security_group_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze security group modifications"""
        findings = []
        
        # Security group changes can break connectivity
        if self._has_property_change(change, "SecurityGroupIngress") or \
           self._has_property_change(change, "SecurityGroupEgress"):
            
            findings.append(self._create_finding(
                finding_id=f"NET-SG-{change.logical_id}",
                title=f"Security Group Rules Modified: {change.logical_id}",
                description=f"Ingress or egress rules for security group '{change.logical_id}' are being modified",
                risk_level=RiskLevel.MEDIUM,
                stack_name=stack_name,
                resource_id=change.logical_id,
                resource_type=change.resource_type,
                change_type="modification",
                impact_description="Changes to network traffic filtering rules may block or allow unintended traffic",
                recommendations=[
                    "Review all rule changes carefully",
                    "Ensure new rules don't block required traffic",
                    "Verify new rules don't allow unintended access",
                    "Test application connectivity after changes"
                ],
                confidence_score=0.7,
                tags={"network", "security_group", "traffic_filtering"}
            ))
        
        return findings
    
    def _analyze_transit_gateway_changes(self, change: ResourceChange, stack_name: str) -> List[RiskFinding]:
        """Analyze Transit Gateway specific changes"""
        findings = []
        
        # Any transit gateway change in enterprise is high risk
        findings.append(self._create_finding(
            finding_id=f"TGW-{change.logical_id}",
            title=f"Transit Gateway Change: {change.resource_type}",
            description=f"Transit Gateway resource '{change.logical_id}' is being modified",
            risk_level=RiskLevel.HIGH,
            stack_name=stack_name,
            resource_id=change.logical_id,
            resource_type=change.resource_type,
            change_type="modification",
            impact_description="Changes to transit gateway configuration may affect multi-VPC connectivity",
            affected_workloads=["All VPCs attached to the transit gateway"],
            recommendations=[
                "Review transit gateway routing changes",
                "Verify all VPC attachments remain functional",
                "Test connectivity between all attached VPCs",
                "Monitor route propagation settings"
            ],
            confidence_score=0.9,
            tags={"transit_gateway", "hub_spoke", "multi_vpc"}
        ))
        
        return findings
    
    def _assess_network_modification_risk(self, resource_type: str, changed_properties: List[str]) -> RiskLevel:
        """Assess risk level for network modifications"""
        # Critical changes that could break connectivity
        critical_props = {"CidrBlock", "RouteTableId", "GatewayId", "TransitGatewayId"}
        
        if any(prop in critical_props for prop in changed_properties):
            return RiskLevel.HIGH
        
        # Route and security changes
        if any("route" in prop.lower() or "security" in prop.lower() for prop in changed_properties):
            return RiskLevel.MEDIUM
        
        return RiskLevel.MEDIUM
    
    def _get_modification_impact(self, resource_type: str, changed_properties: List[str]) -> str:
        """Get impact description for network modifications"""
        if "CidrBlock" in changed_properties:
            return "IP address range changes may affect routing and connectivity"
        elif "RouteTable" in str(changed_properties):
            return "Routing changes may redirect or block network traffic"
        elif "SecurityGroup" in str(changed_properties):
            return "Security rule changes may block or allow different network traffic"
        else:
            return "Network configuration changes may affect connectivity"
    
    def _get_network_deletion_recommendations(self, resource_type: str) -> List[str]:
        """Get specific recommendations for network resource deletions"""
        base_recommendations = [
            "Verify no workloads depend on this network resource",
            "Check for any hardcoded references to this resource",
            "Plan for alternative network paths if needed"
        ]
        
        specific_recommendations = {
            "AWS::EC2::TransitGateway": [
                "Coordinate with all spoke VPC owners",
                "Ensure alternative hub-spoke connectivity exists",
                "Plan organization-wide maintenance window"
            ],
            "AWS::DirectConnect::VirtualInterface": [
                "Verify backup connectivity to on-premises exists",
                "Coordinate with network operations team",
                "Check with on-premises network administrators"
            ],
            "AWS::EC2::VPNConnection": [
                "Ensure alternative VPN connections exist",
                "Verify redundant connectivity paths",
                "Coordinate with remote site administrators"
            ],
            "AWS::EC2::NATGateway": [
                "Ensure alternative outbound connectivity exists",
                "Check for workloads requiring internet access",
                "Consider NAT instance alternatives if needed"
            ]
        }
        
        return base_recommendations + specific_recommendations.get(resource_type, [])
    
    def _get_network_modification_recommendations(self, resource_type: str, changed_properties: List[str]) -> List[str]:
        """Get recommendations for network modifications"""
        return [
            "Test connectivity thoroughly after changes",
            "Have rollback plan ready",
            "Monitor network traffic patterns",
            "Verify all dependent applications function correctly",
            "Consider gradual rollout if possible"
        ]
    
    def _identify_affected_workloads(self, resource_type: str) -> List[str]:
        """Identify workloads that could be affected by network changes"""
        workload_map = {
            "AWS::EC2::TransitGateway": [
                "All workloads in spoke VPCs",
                "Cross-account applications",
                "Hybrid cloud workloads",
                "Shared services"
            ],
            "AWS::DirectConnect::VirtualInterface": [
                "Hybrid applications",
                "On-premises data synchronization",
                "Legacy system integrations"
            ],
            "AWS::EC2::VPC": [
                "All workloads in the VPC",
                "Connected applications",
                "Database connections"
            ],
            "AWS::EC2::SecurityGroup": [
                "Applications using this security group",
                "Load balancers and target groups",
                "Database connections"
            ]
        }
        
        return workload_map.get(resource_type, ["Workloads using this network resource"])