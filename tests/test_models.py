"""
Unit tests for data models
"""

import pytest
from datetime import datetime
from src.models.diff_models import (
    ChangeType, ResourceCategory, RiskLevel, 
    PropertyChange, ResourceChange, IAMStatementChange, 
    StackDiff, DiffAnalysis, RiskAssessment, ResourceCategorizer
)


class TestEnums:
    """Test cases for enum classes"""
    
    def test_change_type_values(self):
        """Test ChangeType enum values"""
        assert ChangeType.ADD == "+"
        assert ChangeType.REMOVE == "-"
        assert ChangeType.MODIFY == "~"
        assert ChangeType.NO_CHANGE == " "
    
    def test_risk_level_values(self):
        """Test RiskLevel enum values"""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"


class TestPropertyChange:
    """Test cases for PropertyChange model"""
    
    def test_create_property_change(self):
        """Test creating a PropertyChange instance"""
        change = PropertyChange(
            property_path="Environment.Variables.SOLUTION_ID",
            change_type=ChangeType.MODIFY,
            old_value="AwsSolution/SO0199/1.10.0",
            new_value="AwsSolution/SO0199/1.12.1"
        )
        
        assert change.property_path == "Environment.Variables.SOLUTION_ID"
        assert change.change_type == ChangeType.MODIFY
        assert change.old_value == "AwsSolution/SO0199/1.10.0"
        assert change.new_value == "AwsSolution/SO0199/1.12.1"
    
    def test_property_change_serialization(self):
        """Test PropertyChange JSON serialization"""
        change = PropertyChange(
            property_path="Value",
            change_type=ChangeType.ADD,
            new_value="1.12.1"
        )
        
        data = change.dict()
        assert data['change_type'] == "+"


class TestResourceChange:
    """Test cases for ResourceChange model"""
    
    def test_create_resource_change(self):
        """Test creating a ResourceChange instance"""
        change = ResourceChange(
            logical_id="SsmParamAcceleratorVersion",
            resource_type="AWS::SSM::Parameter",
            change_type=ChangeType.MODIFY
        )
        
        assert change.logical_id == "SsmParamAcceleratorVersion"
        assert change.resource_type == "AWS::SSM::Parameter"
        assert change.change_type == ChangeType.MODIFY
        assert change.parsed_resource_category == ResourceCategory.SECURITY_RESOURCES
        assert change.service_name == "SSM"
    
    def test_custom_resource_type_parsing(self):
        """Test parsing of custom resource types"""
        change = ResourceChange(
            logical_id="CustomResource",
            resource_type="Custom::MyCustomResource",
            change_type=ChangeType.ADD
        )
        
        assert change.parsed_resource_category == ResourceCategory.CUSTOM_RESOURCES
    
    def test_unknown_resource_type_parsing(self):
        """Test parsing of unknown resource types"""
        change = ResourceChange(
            logical_id="UnknownResource",
            resource_type="AWS::UnknownService::UnknownResource",
            change_type=ChangeType.ADD
        )
        
        assert change.parsed_resource_category == ResourceCategory.OTHER_RESOURCES


class TestIAMStatementChange:
    """Test cases for IAMStatementChange model"""
    
    def test_create_iam_statement_change(self):
        """Test creating an IAMStatementChange instance"""
        change = IAMStatementChange(
            effect="Allow",
            action="kms:Decrypt",
            resource="arn:aws:kms:*:*:key/*",
            principal="AWS:arn:aws:iam::123456789012:root",
            change_type=ChangeType.ADD
        )
        
        assert change.effect == "Allow"
        assert change.action == "kms:Decrypt"
        assert change.resource == "arn:aws:kms:*:*:key/*"
        assert change.change_type == ChangeType.ADD


class TestStackDiff:
    """Test cases for StackDiff model"""
    
    def test_create_stack_diff(self):
        """Test creating a StackDiff instance"""
        stack = StackDiff(
            stack_name="AWSAccelerator-SecurityStack-123456789012-us-east-1",
            account_id="123456789012",
            region="us-east-1"
        )
        
        assert stack.stack_name == "AWSAccelerator-SecurityStack-123456789012-us-east-1"
        assert stack.account_id == "123456789012"
        assert stack.region == "us-east-1"
        assert stack.has_security_changes == False
        assert stack.has_deletions == False
    
    def test_security_changes_detection(self):
        """Test detection of security-related changes"""
        stack = StackDiff(stack_name="TestStack")
        
        # Add IAM change
        stack.iam_statement_changes.append(
            IAMStatementChange(
                effect="Allow",
                action="s3:GetObject",
                resource="*",
                change_type=ChangeType.ADD
            )
        )
        
        assert stack.has_security_changes == True
    
    def test_security_changes_detection_via_resources(self):
        """Test detection of security changes via resource types"""
        stack = StackDiff(stack_name="TestStack")
        
        # Add security resource change
        stack.resource_changes.append(
            ResourceChange(
                logical_id="SecurityRole",
                resource_type="AWS::IAM::Role",
                change_type=ChangeType.ADD
            )
        )
        
        assert stack.has_security_changes == True
    
    def test_deletions_detection(self):
        """Test detection of resource deletions"""
        stack = StackDiff(stack_name="TestStack")
        
        # Add deletion
        stack.resource_changes.append(
            ResourceChange(
                logical_id="OldResource",
                resource_type="AWS::Lambda::Function",
                change_type=ChangeType.REMOVE
            )
        )
        
        assert stack.has_deletions == True


class TestDiffAnalysis:
    """Test cases for DiffAnalysis model"""
    
    def test_create_diff_analysis(self):
        """Test creating a DiffAnalysis instance"""
        analysis = DiffAnalysis(
            total_stacks=5,
            total_resources_changed=25,
            total_iam_changes=8
        )
        
        assert analysis.total_stacks == 5
        assert analysis.total_resources_changed == 25
        assert analysis.total_iam_changes == 8
        assert isinstance(analysis.timestamp, datetime)
    
    def test_stacks_with_security_changes(self):
        """Test filtering stacks with security changes"""
        analysis = DiffAnalysis()
        
        # Add stack with security changes
        security_stack = StackDiff(stack_name="SecurityStack")
        security_stack.iam_statement_changes.append(
            IAMStatementChange(
                effect="Allow",
                action="kms:*",
                resource="*",
                change_type=ChangeType.ADD
            )
        )
        
        # Add stack without security changes
        regular_stack = StackDiff(stack_name="RegularStack")
        regular_stack.resource_changes.append(
            ResourceChange(
                logical_id="Function",
                resource_type="AWS::Lambda::Function",
                change_type=ChangeType.MODIFY
            )
        )
        
        analysis.stack_diffs = [security_stack, regular_stack]
        
        security_stacks = analysis.stacks_with_security_changes
        assert len(security_stacks) == 1
        assert security_stacks[0].stack_name == "SecurityStack"
    
    def test_get_changes_by_category_and_service(self):
        """Test filtering changes by resource category and service"""
        analysis = DiffAnalysis()
        
        stack = StackDiff(stack_name="TestStack")
        stack.resource_changes = [
            ResourceChange(
                logical_id="Function1",
                resource_type="AWS::Lambda::Function",
                change_type=ChangeType.ADD
            ),
            ResourceChange(
                logical_id="Role1",
                resource_type="AWS::IAM::Role",
                change_type=ChangeType.MODIFY
            ),
            ResourceChange(
                logical_id="Function2",
                resource_type="AWS::Lambda::Function",
                change_type=ChangeType.REMOVE
            )
        ]
        analysis.stack_diffs = [stack]
        
        lambda_changes = analysis.get_changes_by_category(ResourceCategory.COMPUTE_RESOURCES)
        assert len(lambda_changes) == 2
        assert all(change.resource_type == "AWS::Lambda::Function" for change in lambda_changes)
        
        # Test get_changes_by_service method
        lambda_changes_by_service = analysis.get_changes_by_service("Lambda")
        assert len(lambda_changes_by_service) == 2


class TestRiskAssessment:
    """Test cases for RiskAssessment model"""
    
    def test_create_risk_assessment(self):
        """Test creating a RiskAssessment instance"""
        assessment = RiskAssessment(
            risk_level=RiskLevel.HIGH,
            category="IAM Permissions",
            description="Broad IAM permissions granted to Lambda function",
            recommendation="Review and restrict IAM permissions to minimum required",
            confidence=0.85
        )
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.category == "IAM Permissions"
        assert assessment.confidence == 0.85
    
    def test_risk_assessment_confidence_validation(self):
        """Test confidence value validation"""
        # Valid confidence
        assessment = RiskAssessment(
            risk_level=RiskLevel.MEDIUM,
            category="Test",
            description="Test description",
            recommendation="Test recommendation",
            confidence=0.5
        )
        assert assessment.confidence == 0.5
        
        # Test boundary values
        with pytest.raises(ValueError):
            RiskAssessment(
                risk_level=RiskLevel.MEDIUM,
                category="Test",
                description="Test description",
                recommendation="Test recommendation",
                confidence=1.5  # Invalid: > 1.0
            )


class TestResourceCategorizer:
    """Test cases for ResourceCategorizer class"""
    
    def test_iam_resources_categorization(self):
        """Test categorization of IAM resources"""
        assert ResourceCategorizer.categorize("AWS::IAM::Role") == ResourceCategory.IAM_RESOURCES
        assert ResourceCategorizer.categorize("AWS::IAM::Policy") == ResourceCategory.IAM_RESOURCES
        assert ResourceCategorizer.categorize("AWS::IAM::User") == ResourceCategory.IAM_RESOURCES
    
    def test_security_resources_categorization(self):
        """Test categorization of security resources"""
        assert ResourceCategorizer.categorize("AWS::KMS::Key") == ResourceCategory.SECURITY_RESOURCES
        assert ResourceCategorizer.categorize("AWS::SecretsManager::Secret") == ResourceCategory.SECURITY_RESOURCES
        assert ResourceCategorizer.categorize("AWS::SSM::Parameter") == ResourceCategory.SECURITY_RESOURCES
    
    def test_compute_resources_categorization(self):
        """Test categorization of compute resources"""
        assert ResourceCategorizer.categorize("AWS::Lambda::Function") == ResourceCategory.COMPUTE_RESOURCES
        assert ResourceCategorizer.categorize("AWS::EC2::Instance") == ResourceCategory.COMPUTE_RESOURCES
    
    def test_network_resources_categorization(self):
        """Test categorization of network resources"""
        assert ResourceCategorizer.categorize("AWS::EC2::VPC") == ResourceCategory.NETWORK_RESOURCES
        assert ResourceCategorizer.categorize("AWS::EC2::Subnet") == ResourceCategory.NETWORK_RESOURCES
        assert ResourceCategorizer.categorize("AWS::ELB::LoadBalancer") == ResourceCategory.NETWORK_RESOURCES
    
    def test_custom_resources_categorization(self):
        """Test categorization of custom resources"""
        assert ResourceCategorizer.categorize("Custom::MyResource") == ResourceCategory.CUSTOM_RESOURCES
        assert ResourceCategorizer.categorize("Custom::LambdaFunction") == ResourceCategory.CUSTOM_RESOURCES
    
    def test_other_resources_categorization(self):
        """Test categorization of unknown resources"""
        assert ResourceCategorizer.categorize("AWS::NewService::NewResource") == ResourceCategory.OTHER_RESOURCES
        assert ResourceCategorizer.categorize("Unknown::Resource") == ResourceCategory.OTHER_RESOURCES
    
    def test_is_security_resource(self):
        """Test security resource detection"""
        assert ResourceCategorizer.is_security_resource("AWS::IAM::Role") == True
        assert ResourceCategorizer.is_security_resource("AWS::KMS::Key") == True
        assert ResourceCategorizer.is_security_resource("AWS::Lambda::Function") == False
        assert ResourceCategorizer.is_security_resource("AWS::EC2::VPC") == False
    
    def test_get_service_name(self):
        """Test service name extraction"""
        assert ResourceCategorizer.get_service_name("AWS::IAM::Role") == "IAM"
        assert ResourceCategorizer.get_service_name("AWS::Lambda::Function") == "Lambda"
        assert ResourceCategorizer.get_service_name("Custom::MyResource") == "Custom"
        assert ResourceCategorizer.get_service_name("Unknown::Resource") == "Unknown"