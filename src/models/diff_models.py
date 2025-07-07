"""
Data models for CloudFormation diff changes

Resource Categorization System
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import re
import yaml
from pathlib import Path


class ChangeType(str, Enum):
    """Types of changes in CloudFormation diffs"""
    ADD = "+"
    REMOVE = "-"
    MODIFY = "~"
    NO_CHANGE = " "


class ResourceCategory(str, Enum):
    """High-level categories for AWS resources"""
    IAM_RESOURCES = "iam"
    SECURITY_RESOURCES = "security"
    COMPUTE_RESOURCES = "compute"
    NETWORK_RESOURCES = "network"
    STORAGE_RESOURCES = "storage"
    MONITORING_RESOURCES = "monitoring"
    ORGANIZATIONS_RESOURCES = "organizations"
    CUSTOM_RESOURCES = "custom"
    OTHER_RESOURCES = "other"


class ResourceCategorizer:
    """Categorizes AWS resources by service patterns"""
    
    # Default service patterns for categorization
    SERVICE_PATTERNS = {
        ResourceCategory.IAM_RESOURCES: [
            r"^AWS::IAM::",
        ],
        ResourceCategory.SECURITY_RESOURCES: [
            r"^AWS::KMS::",
            r"^AWS::SecretsManager::",
            r"^AWS::SecurityHub::",
            r"^AWS::GuardDuty::",
            r"^AWS::Config::",
            r"^AWS::CloudTrail::",
            r"^AWS::SSM::",  # SSM can contain security parameters
        ],
        ResourceCategory.COMPUTE_RESOURCES: [
            r"^AWS::Lambda::",
            r"^AWS::EC2::Instance",
            r"^AWS::ECS::",
            r"^AWS::Batch::",
        ],
        ResourceCategory.NETWORK_RESOURCES: [
            r"^AWS::EC2::VPC",
            r"^AWS::EC2::Subnet",
            r"^AWS::EC2::SecurityGroup",
            r"^AWS::EC2::RouteTable",
            r"^AWS::EC2::NetworkAcl",
            r"^AWS::ELB::",
            r"^AWS::ElasticLoadBalancingV2::",
            r"^AWS::Route53::",
        ],
        ResourceCategory.STORAGE_RESOURCES: [
            r"^AWS::S3::",
            r"^AWS::EBS::",
            r"^AWS::EFS::",
            r"^AWS::DynamoDB::",
            r"^AWS::RDS::",
        ],
        ResourceCategory.MONITORING_RESOURCES: [
            r"^AWS::Logs::",
            r"^AWS::CloudWatch::",
            r"^AWS::SNS::",
            r"^AWS::SQS::",
        ],
        ResourceCategory.ORGANIZATIONS_RESOURCES: [
            r"^AWS::Organizations::",
        ],
        ResourceCategory.CUSTOM_RESOURCES: [
            r"^Custom::",
        ],
    }
    
    @classmethod
    def categorize(cls, resource_type: str) -> ResourceCategory:
        """Categorize a resource type into a high-level category"""
        for category, patterns in cls.SERVICE_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, resource_type):
                    return category
        return ResourceCategory.OTHER_RESOURCES
    
    @classmethod
    def is_security_resource(cls, resource_type: str) -> bool:
        """Check if a resource type is security-related"""
        category = cls.categorize(resource_type)
        return category in [ResourceCategory.IAM_RESOURCES, ResourceCategory.SECURITY_RESOURCES]
    
    @classmethod
    def get_service_name(cls, resource_type: str) -> str:
        """Extract the AWS service name from resource type"""
        if resource_type.startswith("AWS::"):
            parts = resource_type.split("::", 2)
            return parts[1] if len(parts) > 1 else "Unknown"
        elif resource_type.startswith("Custom::"):
            return "Custom"
        return "Unknown"
    
    @classmethod
    def load_config(cls, config_path: str = None) -> dict:
        """Load categorization rules from configuration file"""
        if config_path is None:
            # Default config path relative to this file
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "config" / "resource_categorization.yaml"
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError):
            # Fall back to default patterns if config not available
            return None
    
    @classmethod
    def categorize_with_config(cls, resource_type: str, config: dict = None) -> ResourceCategory:
        """Categorize using external configuration if available"""
        if config is None:
            return cls.categorize(resource_type)
        
        # Check custom mappings first
        custom_mappings = config.get('custom_mappings', {})
        if resource_type in custom_mappings:
            category_name = custom_mappings[resource_type]
            return getattr(ResourceCategory, category_name.upper(), ResourceCategory.OTHER_RESOURCES)
        
        # Use configured service patterns
        service_patterns = config.get('service_patterns', {})
        for category_name, patterns in service_patterns.items():
            for pattern in patterns:
                if re.match(pattern, resource_type):
                    return getattr(ResourceCategory, category_name.upper(), ResourceCategory.OTHER_RESOURCES)
        
        return ResourceCategory.OTHER_RESOURCES


class RiskLevel(str, Enum):
    """Risk levels for changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PropertyChange(BaseModel):
    """Represents a change to a resource property"""
    property_path: str = Field(..., description="Path to the property (e.g., 'Environment.Variables.SOLUTION_ID')")
    change_type: ChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    class Config:
        json_encoders = {
            ChangeType: lambda v: v.value
        }


class ResourceChange(BaseModel):
    """Represents a change to a CloudFormation resource"""
    logical_id: str = Field(..., description="CloudFormation logical ID")
    resource_type: str = Field(..., description="AWS resource type")
    change_type: ChangeType
    property_changes: List[PropertyChange] = Field(default_factory=list)
    
    @property
    def parsed_resource_category(self) -> ResourceCategory:
        """Get the parsed resource category"""
        return ResourceCategorizer.categorize(self.resource_type)
    
    @property
    def service_name(self) -> str:
        """Get the AWS service name"""
        return ResourceCategorizer.get_service_name(self.resource_type)
    
    class Config:
        json_encoders = {
            ChangeType: lambda v: v.value
        }


class IAMStatementChange(BaseModel):
    """Represents changes to IAM policy statements"""
    effect: str  # Allow/Deny
    action: Union[str, List[str]]
    resource: Union[str, List[str]]
    principal: Optional[Union[str, Dict[str, Any]]] = None
    condition: Optional[Dict[str, Any]] = None
    change_type: ChangeType
    
    class Config:
        json_encoders = {
            ChangeType: lambda v: v.value
        }


class StackDiff(BaseModel):
    """Represents the diff for a single CloudFormation stack"""
    stack_name: str
    description_change: Optional[PropertyChange] = None
    resource_changes: List[ResourceChange] = Field(default_factory=list)
    iam_statement_changes: List[IAMStatementChange] = Field(default_factory=list)
    account_id: Optional[str] = None
    region: Optional[str] = None
    
    @property
    def has_security_changes(self) -> bool:
        """Check if this stack has security-related changes"""
        return (
            len(self.iam_statement_changes) > 0 or
            any(ResourceCategorizer.is_security_resource(rc.resource_type) 
                for rc in self.resource_changes)
        )
    
    @property
    def has_deletions(self) -> bool:
        """Check if this stack has resource deletions"""
        return any(rc.change_type == ChangeType.REMOVE for rc in self.resource_changes)


class DiffAnalysis(BaseModel):
    """Complete analysis of all diff logs"""
    timestamp: datetime = Field(default_factory=datetime.now)
    stack_diffs: List[StackDiff] = Field(default_factory=list)
    total_stacks: int = 0
    total_resources_changed: int = 0
    total_iam_changes: int = 0
    
    @property
    def stacks_with_security_changes(self) -> List[StackDiff]:
        """Get stacks with security-related changes"""
        return [stack for stack in self.stack_diffs if stack.has_security_changes]
    
    @property
    def stacks_with_deletions(self) -> List[StackDiff]:
        """Get stacks with resource deletions"""
        return [stack for stack in self.stack_diffs if stack.has_deletions]
    
    def get_changes_by_category(self, category: ResourceCategory) -> List[ResourceChange]:
        """Get all changes for a specific resource category"""
        changes = []
        for stack in self.stack_diffs:
            changes.extend([
                rc for rc in stack.resource_changes 
                if rc.parsed_resource_category == category
            ])
        return changes
    
    def get_changes_by_service(self, service_name: str) -> List[ResourceChange]:
        """Get all changes for a specific AWS service"""
        changes = []
        for stack in self.stack_diffs:
            changes.extend([
                rc for rc in stack.resource_changes 
                if rc.service_name.lower() == service_name.lower()
            ])
        return changes
    
    def get_detailed_context_summary(self) -> Dict[str, Any]:
        """Create detailed context summary for LLM analysis"""
        context = {
            "overview": {
                "total_stacks": self.total_stacks,
                "total_resources_changed": self.total_resources_changed,
                "total_iam_changes": self.total_iam_changes,
                "analysis_timestamp": self.timestamp.isoformat() if self.timestamp else None
            },
            "stacks": {},
            "changes_by_category": {},
            "changes_by_service": {},
            "iam_changes": [],
            "security_findings": [],
            "high_risk_changes": [],
            "stack_files": []
        }
        
        # Process each stack
        for stack in self.stack_diffs:
            stack_info = {
                "name": stack.stack_name,
                "account_id": stack.account_id,
                "region": stack.region,
                "has_security_changes": stack.has_security_changes,
                "has_deletions": stack.has_deletions,
                "resource_changes_count": len(stack.resource_changes),
                "iam_changes_count": len(stack.iam_statement_changes),
                "resource_changes": [],
                "iam_changes": []
            }
            
            # Add stack to file list for reference
            context["stack_files"].append({
                "stack_name": stack.stack_name,
                "filename": f"{stack.stack_name}.diff",
                "account": stack.account_id,
                "region": stack.region
            })
            
            # Process resource changes
            for rc in stack.resource_changes:
                change_info = {
                    "logical_id": rc.logical_id,
                    "resource_type": rc.resource_type,
                    "service": rc.service_name,
                    "category": rc.parsed_resource_category.value,
                    "change_type": rc.change_type.value,
                    "property_changes": len(rc.property_changes)
                }
                stack_info["resource_changes"].append(change_info)
                
                # Categorize changes
                category = rc.parsed_resource_category.value
                if category not in context["changes_by_category"]:
                    context["changes_by_category"][category] = []
                context["changes_by_category"][category].append({
                    "stack": stack.stack_name,
                    "resource": rc.logical_id,
                    "type": rc.resource_type,
                    "change": rc.change_type.value
                })
                
                # Group by service
                service = rc.service_name
                if service not in context["changes_by_service"]:
                    context["changes_by_service"][service] = []
                context["changes_by_service"][service].append({
                    "stack": stack.stack_name,
                    "resource": rc.logical_id,
                    "change": rc.change_type.value
                })
                
                # Track high-risk changes (deletions and security-related)
                if (rc.change_type == ChangeType.REMOVE or 
                    ResourceCategorizer.is_security_resource(rc.resource_type)):
                    context["high_risk_changes"].append({
                        "stack": stack.stack_name,
                        "resource": rc.logical_id,
                        "type": rc.resource_type,
                        "change": rc.change_type.value,
                        "reason": "Deletion" if rc.change_type == ChangeType.REMOVE else "Security Resource"
                    })
            
            # Process IAM changes
            for iam in stack.iam_statement_changes:
                iam_info = {
                    "effect": iam.effect,
                    "action": iam.action,
                    "resource": iam.resource,
                    "principal": iam.principal,
                    "change_type": iam.change_type.value
                }
                stack_info["iam_changes"].append(iam_info)
                context["iam_changes"].append({
                    "stack": stack.stack_name,
                    **iam_info
                })
                
                # Track security findings
                if iam.effect == "Allow" and (
                    isinstance(iam.action, str) and "*" in iam.action or
                    isinstance(iam.action, list) and any("*" in action for action in iam.action)
                ):
                    context["security_findings"].append({
                        "stack": stack.stack_name,
                        "type": "Wildcard IAM Permission",
                        "details": f"{iam.effect} {iam.action} on {iam.resource}",
                        "severity": "HIGH"
                    })
            
            context["stacks"][stack.stack_name] = stack_info
        
        return context
    
    def get_context_for_question_type(self, question_keywords: List[str]) -> Dict[str, Any]:
        """Get relevant context based on question keywords"""
        full_context = self.get_detailed_context_summary()
        
        # Determine question type and filter context accordingly
        question_type = self._determine_question_type(question_keywords)
        
        if question_type == "iam":
            return {
                "question_type": "iam",
                "iam_changes": full_context["iam_changes"],
                "security_findings": full_context["security_findings"],
                "relevant_stacks": {k: v for k, v in full_context["stacks"].items() 
                                  if v["iam_changes_count"] > 0},
                "overview": full_context["overview"]
            }
        
        elif question_type == "stack":
            return {
                "question_type": "stack",
                "stacks": full_context["stacks"],
                "stack_files": full_context["stack_files"],
                "overview": full_context["overview"]
            }
        
        elif question_type == "risk":
            return {
                "question_type": "risk",
                "high_risk_changes": full_context["high_risk_changes"],
                "security_findings": full_context["security_findings"],
                "stacks_with_deletions": [s for s in full_context["stacks"].values() if s["has_deletions"]],
                "overview": full_context["overview"]
            }
        
        elif question_type == "service":
            return {
                "question_type": "service",
                "changes_by_service": full_context["changes_by_service"],
                "changes_by_category": full_context["changes_by_category"],
                "overview": full_context["overview"]
            }
        
        elif question_type == "file":
            return {
                "question_type": "file",
                "stack_files": full_context["stack_files"],
                "stacks": full_context["stacks"],
                "overview": full_context["overview"]
            }
        
        else:
            # Return comprehensive context for general questions
            return full_context
    
    def _determine_question_type(self, keywords: List[str]) -> str:
        """Determine the type of question based on keywords"""
        keyword_str = " ".join(keywords).lower()
        
        if any(word in keyword_str for word in ["iam", "permission", "role", "policy", "access", "principal"]):
            return "iam"
        elif any(word in keyword_str for word in ["stack", "which", "list", "file", "name"]):
            return "stack"
        elif any(word in keyword_str for word in ["risk", "dangerous", "concern", "critical", "high", "security"]):
            return "risk"
        elif any(word in keyword_str for word in ["service", "aws", "resource", "type"]):
            return "service"
        elif any(word in keyword_str for word in ["file", "filename", "diff", "log"]):
            return "file"
        else:
            return "general"
    
    def dict(self, **kwargs):
        """Override dict method to handle datetime serialization"""
        # Use Pydantic's built-in serialization with encoders
        kwargs.setdefault('exclude_unset', False)
        data = super().dict(**kwargs)
        
        # Recursively handle datetime and other non-serializable objects
        def serialize_objects(obj):
            if isinstance(obj, dict):
                return {k: serialize_objects(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize_objects(item) for item in obj]
            elif isinstance(obj, set):
                return list(obj)  # Convert sets to lists for JSON serialization
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        return serialize_objects(data)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ChangeType: lambda v: v.value,
            ResourceCategory: lambda v: v.value,
            RiskLevel: lambda v: v.value,
        }


class RiskAssessment(BaseModel):
    """Risk assessment for a specific change or stack"""
    risk_level: RiskLevel
    category: str = Field(..., description="Category of risk (e.g., 'IAM Permissions', 'Resource Deletion')")
    description: str = Field(..., description="Human-readable description of the risk")
    recommendation: str = Field(..., description="Recommended action to take")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level of the assessment (0-1)")
    
    class Config:
        json_encoders = {
            RiskLevel: lambda v: v.value
        }


class ComprehensiveAnalysisResult(BaseModel):
    """Complete analysis results from rule-based and LLM analysis"""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when analysis was created")
    
    # Input data reference
    input_analysis: DiffAnalysis = Field(..., description="Original diff analysis that was processed")
    
    # Rule-based analysis results
    rule_based_analysis: Dict[str, Any] = Field(..., description="Results from rule-based analyzers")
    
    # LLM analysis results (optional)
    llm_analysis: Optional[Dict[str, Any]] = Field(None, description="Results from LLM analysis if enabled")
    
    # Combined assessment
    combined_assessment: Optional[Dict[str, Any]] = Field(None, description="Combined insights from all analysis methods")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata and statistics")
    
    def get_enhanced_context_for_llm(self) -> Dict[str, Any]:
        """Get comprehensive context including analysis results for LLM queries"""
        # Get base diff analysis context
        diff_context = self.input_analysis.get_detailed_context_summary()
        
        # Add rule-based analysis results
        rule_analysis = self.rule_based_analysis or {}
        
        # Add LLM analysis insights if available
        llm_insights = {}
        if self.llm_analysis:
            llm_insights = {
                "provider": self.llm_analysis.get("provider"),
                "model": self.llm_analysis.get("model"),
                "summary": self.llm_analysis.get("summary", {}),
                "available_analysis_types": list(self.llm_analysis.get("analysis_results", {}).keys())
            }
        
        # Combine everything
        enhanced_context = {
            **diff_context,
            "analysis_metadata": {
                "analysis_id": self.analysis_id,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "analyzers_used": self.metadata.get("analyzers_used", []),
                "llm_enabled": self.metadata.get("llm_enabled", False)
            },
            "risk_assessment": {
                "overall_risk_level": rule_analysis.get("overall_risk_level"),
                "total_findings": rule_analysis.get("total_findings", 0),
                "risk_counts": {
                    "critical": rule_analysis.get("critical_count", 0),
                    "high": rule_analysis.get("high_count", 0),
                    "medium": rule_analysis.get("medium_count", 0),
                    "low": rule_analysis.get("low_count", 0)
                },
                "risk_categories": {
                    "security": rule_analysis.get("security_risks", 0),
                    "connectivity": rule_analysis.get("connectivity_risks", 0),
                    "operational": rule_analysis.get("operational_risks", 0),
                    "compliance": rule_analysis.get("compliance_risks", 0),
                    "data_loss": rule_analysis.get("data_loss_risks", 0)
                },
                "recommendation": rule_analysis.get("recommended_action")
            },
            "llm_insights": llm_insights,
            "findings": rule_analysis.get("findings", [])
        }
        
        return enhanced_context
    
    def get_context_for_question_type(self, question_keywords: List[str]) -> Dict[str, Any]:
        """Get relevant context based on question type, including analysis results"""
        # Get base context from diff analysis
        base_context = self.input_analysis.get_context_for_question_type(question_keywords)
        
        # Get enhanced context
        enhanced_context = self.get_enhanced_context_for_llm()
        
        # Merge relevant analysis data based on question type
        question_type = base_context.get("question_type", "general")
        
        if question_type == "iam":
            # Add relevant risk findings for IAM questions
            iam_findings = [
                finding for finding in enhanced_context["findings"]
                if "iam" in finding.get("category", "").lower() or 
                   "permission" in finding.get("title", "").lower()
            ]
            base_context["relevant_findings"] = iam_findings
            base_context["risk_assessment"] = enhanced_context["risk_assessment"]
            
        elif question_type == "risk":
            # Add full risk assessment for risk questions
            base_context["risk_assessment"] = enhanced_context["risk_assessment"]
            base_context["findings"] = enhanced_context["findings"]
            base_context["llm_insights"] = enhanced_context["llm_insights"]
            
        elif question_type == "stack":
            # Add stack-specific findings
            base_context["analysis_metadata"] = enhanced_context["analysis_metadata"]
            
        # Always include overview risk information
        base_context["risk_overview"] = {
            "overall_level": enhanced_context["risk_assessment"]["overall_risk_level"],
            "total_findings": enhanced_context["risk_assessment"]["total_findings"],
            "recommendation": enhanced_context["risk_assessment"]["recommendation"]
        }
        
        return base_context
    
    def dict(self, **kwargs):
        """Override dict method to handle datetime serialization"""
        # Use Pydantic's built-in serialization with encoders
        kwargs.setdefault('exclude_unset', False)
        data = super().dict(**kwargs)
        
        # Recursively handle datetime and other non-serializable objects
        def serialize_objects(obj):
            if isinstance(obj, dict):
                return {k: serialize_objects(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize_objects(item) for item in obj]
            elif isinstance(obj, set):
                return list(obj)  # Convert sets to lists for JSON serialization
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        return serialize_objects(data)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ChangeType: lambda v: v.value,
            ResourceCategory: lambda v: v.value,
            RiskLevel: lambda v: v.value,
        }