"""
Base classes for risk analysis engines
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.diff_models import (
    DiffAnalysis, 
    StackDiff, 
    ResourceChange, 
    IAMStatementChange,
    ResourceCategory
)


class RiskLevel(str, Enum):
    """Risk levels for changes"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    """Categories of risks"""
    SECURITY = "security"
    CONNECTIVITY = "connectivity"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    DATA_LOSS = "data_loss"
    PERFORMANCE = "performance"


class RiskFinding(BaseModel):
    """Individual risk finding"""
    id: str = Field(..., description="Unique identifier for the finding")
    title: str = Field(..., description="Brief title of the risk")
    description: str = Field(..., description="Detailed description of the risk")
    risk_level: RiskLevel = Field(..., description="Severity level of the risk")
    risk_category: RiskCategory = Field(..., description="Category of the risk")
    
    # Context information
    stack_name: str = Field(..., description="CloudFormation stack name")
    resource_id: Optional[str] = Field(None, description="Logical ID of the resource")
    resource_type: Optional[str] = Field(None, description="AWS resource type")
    change_type: Optional[str] = Field(None, description="Type of change (add/modify/delete)")
    
    # Impact assessment
    impact_description: str = Field(..., description="Description of potential impact")
    affected_workloads: List[str] = Field(default_factory=list, description="Workloads that may be affected")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    rollback_steps: List[str] = Field(default_factory=list, description="Steps to rollback if needed")
    
    # Additional metadata
    confidence_score: float = Field(default=0.8, description="Confidence in the risk assessment (0-1)")
    tags: Set[str] = Field(default_factory=set, description="Tags for categorization")
    detected_at: datetime = Field(default_factory=datetime.now, description="When the risk was detected")


class RiskAssessment(BaseModel):
    """Complete risk assessment for a diff analysis"""
    analysis_id: str = Field(..., description="Unique identifier for the analysis")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Risk findings
    findings: List[RiskFinding] = Field(default_factory=list)
    
    # Summary statistics
    total_findings: int = Field(default=0)
    critical_count: int = Field(default=0)
    high_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    low_count: int = Field(default=0)
    
    # Risk categories
    security_risks: int = Field(default=0)
    connectivity_risks: int = Field(default=0)
    operational_risks: int = Field(default=0)
    compliance_risks: int = Field(default=0)
    data_loss_risks: int = Field(default=0)
    
    # Overall assessment
    overall_risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    recommended_action: str = Field(default="Proceed with caution")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._update_statistics()
    
    def _update_statistics(self):
        """Update summary statistics based on findings"""
        self.total_findings = len(self.findings)
        
        # Count by risk level
        self.critical_count = sum(1 for f in self.findings if f.risk_level == RiskLevel.CRITICAL)
        self.high_count = sum(1 for f in self.findings if f.risk_level == RiskLevel.HIGH)
        self.medium_count = sum(1 for f in self.findings if f.risk_level == RiskLevel.MEDIUM)
        self.low_count = sum(1 for f in self.findings if f.risk_level == RiskLevel.LOW)
        
        # Count by category
        self.security_risks = sum(1 for f in self.findings if f.risk_category == RiskCategory.SECURITY)
        self.connectivity_risks = sum(1 for f in self.findings if f.risk_category == RiskCategory.CONNECTIVITY)
        self.operational_risks = sum(1 for f in self.findings if f.risk_category == RiskCategory.OPERATIONAL)
        self.compliance_risks = sum(1 for f in self.findings if f.risk_category == RiskCategory.COMPLIANCE)
        self.data_loss_risks = sum(1 for f in self.findings if f.risk_category == RiskCategory.DATA_LOSS)
        
        # Determine overall risk level
        if self.critical_count > 0:
            self.overall_risk_level = RiskLevel.CRITICAL
            self.recommended_action = "STOP - Critical risks identified. Review and mitigate before proceeding."
        elif self.high_count > 0:
            self.overall_risk_level = RiskLevel.HIGH
            self.recommended_action = "CAUTION - High-risk changes detected. Careful review recommended."
        elif self.medium_count > 0:
            self.overall_risk_level = RiskLevel.MEDIUM
            self.recommended_action = "REVIEW - Medium-risk changes detected. Standard review process."
        else:
            self.overall_risk_level = RiskLevel.LOW
            self.recommended_action = "PROCEED - Low-risk changes detected. Minimal review required."
    
    def add_finding(self, finding: RiskFinding):
        """Add a new risk finding"""
        self.findings.append(finding)
        self._update_statistics()
    
    def get_findings_by_level(self, level: RiskLevel) -> List[RiskFinding]:
        """Get findings by risk level"""
        return [f for f in self.findings if f.risk_level == level]
    
    def get_findings_by_category(self, category: RiskCategory) -> List[RiskFinding]:
        """Get findings by risk category"""
        return [f for f in self.findings if f.risk_category == category]
    
    def get_critical_findings(self) -> List[RiskFinding]:
        """Get critical findings that require immediate attention"""
        return self.get_findings_by_level(RiskLevel.CRITICAL)


class BaseRiskAnalyzer(ABC):
    """Base class for risk analyzers"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.risk_category = RiskCategory.OPERATIONAL  # Default, override in subclasses
    
    @abstractmethod
    async def analyze(self, diff_analysis: DiffAnalysis) -> List[RiskFinding]:
        """Analyze diff and return risk findings"""
        pass
    
    def _create_finding(
        self,
        finding_id: str,
        title: str,
        description: str,
        risk_level: RiskLevel,
        stack_name: str,
        impact_description: str,
        recommendations: List[str],
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        change_type: Optional[str] = None,
        affected_workloads: Optional[List[str]] = None,
        rollback_steps: Optional[List[str]] = None,
        confidence_score: float = 0.8,
        tags: Optional[Set[str]] = None
    ) -> RiskFinding:
        """Helper method to create risk findings"""
        return RiskFinding(
            id=finding_id,
            title=title,
            description=description,
            risk_level=risk_level,
            risk_category=self.risk_category,
            stack_name=stack_name,
            resource_id=resource_id,
            resource_type=resource_type,
            change_type=change_type,
            impact_description=impact_description,
            affected_workloads=affected_workloads or [],
            recommendations=recommendations,
            rollback_steps=rollback_steps or [],
            confidence_score=confidence_score,
            tags=tags or set()
        )
    
    def _is_deletion(self, change: ResourceChange) -> bool:
        """Check if a change is a deletion"""
        return change.change_type.value == "-"
    
    def _is_addition(self, change: ResourceChange) -> bool:
        """Check if a change is an addition"""
        return change.change_type.value == "+"
    
    def _is_modification(self, change: ResourceChange) -> bool:
        """Check if a change is a modification"""
        return change.change_type.value == "~"
    
    def _has_property_change(self, change: ResourceChange, property_name: str) -> bool:
        """Check if a specific property has changed"""
        if not change.property_changes:
            return False
        return any(property_name.lower() in prop.property_path.lower() for prop in change.property_changes)


class RiskAnalysisEngine:
    """Main engine that coordinates all risk analyzers"""
    
    def __init__(self):
        self.analyzers: List[BaseRiskAnalyzer] = []
    
    def register_analyzer(self, analyzer: BaseRiskAnalyzer):
        """Register a risk analyzer"""
        self.analyzers.append(analyzer)
    
    async def analyze(self, diff_analysis: DiffAnalysis) -> RiskAssessment:
        """Run all analyzers and compile results"""
        analysis_id = f"risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        assessment = RiskAssessment(analysis_id=analysis_id)
        
        # Run all analyzers
        for analyzer in self.analyzers:
            try:
                findings = await analyzer.analyze(diff_analysis)
                for finding in findings:
                    assessment.add_finding(finding)
            except Exception as e:
                # Log error but continue with other analyzers
                print(f"Error in analyzer {analyzer.name}: {e}")
        
        return assessment
    
    def get_analyzer_info(self) -> List[Dict[str, Any]]:
        """Get information about registered analyzers"""
        return [
            {
                "name": analyzer.name,
                "description": analyzer.description,
                "category": analyzer.risk_category.value
            }
            for analyzer in self.analyzers
        ]