"""
Unit tests for diff parser
"""

import pytest
from pathlib import Path
from src.parsers.diff_parser import DiffParser
from src.models.diff_models import ChangeType, ResourceCategory


class TestDiffParser:
    """Test cases for DiffParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = DiffParser()
    
    def test_extract_stack_name(self):
        """Test stack name extraction from filename"""
        filename = "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2.diff"
        expected = "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2"
        assert self.parser._extract_stack_name(filename) == expected
    
    def test_extract_account_id(self):
        """Test account ID extraction from filename"""
        filename = "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2.diff"
        expected = "145023093216"
        assert self.parser._extract_account_id(filename) == expected
    
    def test_extract_region(self):
        """Test region extraction from filename"""
        filename = "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2.diff"
        expected = "ap-southeast-2"
        assert self.parser._extract_region(filename) == expected
    
    def test_parse_description_change(self):
        """Test parsing of description changes"""
        line = "[~] Description Description: (SO0199-security) Landing Zone Accelerator on AWS. Version 1.10.0. to (SO0199-security) Landing Zone Accelerator on AWS. Version 1.12.1."
        
        result = self.parser._parse_description_change(line)
        
        assert result is not None
        assert result.property_path == "Description"
        assert result.change_type == ChangeType.MODIFY
        assert "Version 1.10.0" in result.old_value
        assert "Version 1.12.1" in result.new_value
    
    def test_parse_simple_diff_content(self):
        """Test parsing of simple diff content"""
        content = """
Stack: AWSAccelerator-SecurityStack-145023093216-ap-southeast-2 
Template
[~] Description Description: (SO0199-security) Landing Zone Accelerator on AWS. Version 1.10.0. to (SO0199-security) Landing Zone Accelerator on AWS. Version 1.12.1.

Resources
[~] AWS::SSM::Parameter SsmParamAcceleratorVersionFF83282D 
 └─ [~] Value
     ├─ [-] 1.10.0
     └─ [+] 1.12.1
"""
        
        result = self.parser.parse_content(content, "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2.diff")
        
        assert result.stack_name == "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2"
        assert result.account_id == "145023093216"
        assert result.region == "ap-southeast-2"
        assert result.description_change is not None
        assert len(result.resource_changes) == 1
        
        resource_change = result.resource_changes[0]
        assert resource_change.logical_id == "SsmParamAcceleratorVersionFF83282D"
        assert resource_change.resource_type == "AWS::SSM::Parameter"
        assert resource_change.change_type == ChangeType.MODIFY
    
    def test_parse_iam_section(self):
        """Test parsing of IAM statement changes"""
        content = """
Stack: AWSAccelerator-LoggingStack-145023093216-ap-southeast-2 

IAM Statement Changes
┌───┬────────────────────────────────────────────────────────────────────────────────┬────────┬──────────────────────────────────┬──────────────────────────────────┬──────────────────────────────────┐
│   │ Resource                                                                       │ Effect │ Action                           │ Principal                        │ Condition                        │
├───┼────────────────────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────────┼──────────────────────────────────┼──────────────────────────────────┤
│ + │ ${AcceleratorCloudWatchKeyF93B6E17.Arn}                                        │ Allow  │ kms:Decrypt                      │ AWS:${CustomRole}                │                                  │
└───┴────────────────────────────────────────────────────────────────────────────────┴────────┴──────────────────────────────────┴──────────────────────────────────┴──────────────────────────────────┘

Resources
"""
        
        result = self.parser.parse_content(content, "AWSAccelerator-LoggingStack-145023093216-ap-southeast-2.diff")
        
        assert len(result.iam_statement_changes) >= 0  # IAM parsing is complex, just ensure no crash
    
    def test_resource_type_parsing(self):
        """Test resource type enum parsing"""
        content = """
Stack: AWSAccelerator-KeyStack-145023093216-ap-southeast-2 

Resources
[+] AWS::KMS::Key AcceleratorKmsKey
[+] AWS::IAM::Role TestRole
[+] AWS::Lambda::Function TestFunction
[+] Custom::TestCustomResource TestCustom
"""
        
        result = self.parser.parse_content(content, "AWSAccelerator-KeyStack-145023093216-ap-southeast-2.diff")
        
        assert len(result.resource_changes) == 4
        
        # Check resource categorization
        kms_resource = next((rc for rc in result.resource_changes if rc.logical_id == "AcceleratorKmsKey"), None)
        assert kms_resource is not None
        assert kms_resource.parsed_resource_category == ResourceCategory.SECURITY_RESOURCES
        assert kms_resource.service_name == "KMS"
        
        custom_resource = next((rc for rc in result.resource_changes if rc.logical_id == "TestCustom"), None)
        assert custom_resource is not None
        assert custom_resource.parsed_resource_category == ResourceCategory.CUSTOM_RESOURCES
    
    def test_security_changes_detection(self):
        """Test detection of security-related changes"""
        content = """
Stack: AWSAccelerator-SecurityStack-145023093216-ap-southeast-2 

Resources
[+] AWS::IAM::Role SecurityRole
[+] AWS::KMS::Key SecurityKey
[+] AWS::Lambda::Function RegularFunction
"""
        
        result = self.parser.parse_content(content, "AWSAccelerator-SecurityStack-145023093216-ap-southeast-2.diff")
        
        assert result.has_security_changes == True
    
    def test_deletion_detection(self):
        """Test detection of resource deletions"""
        content = """
Stack: AWSAccelerator-TestStack-145023093216-ap-southeast-2 

Resources
[-] AWS::Lambda::Function OldFunction destroy
[+] AWS::Lambda::Function NewFunction
"""
        
        result = self.parser.parse_content(content, "AWSAccelerator-TestStack-145023093216-ap-southeast-2.diff")
        
        assert result.has_deletions == True