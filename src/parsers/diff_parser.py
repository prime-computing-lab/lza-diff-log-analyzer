"""
CloudFormation diff parser for LZA logs
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..models.diff_models import (
    StackDiff, ResourceChange, PropertyChange, IAMStatementChange, 
    ChangeType, DiffAnalysis
)


class DiffParser:
    """Parser for CloudFormation diff files"""
    
    def __init__(self):
        self.current_stack: Optional[StackDiff] = None
        self.parsing_iam_section = False
        self.parsing_resources_section = False
        
    def parse_file(self, file_path: Path) -> StackDiff:
        """Parse a single diff file and return StackDiff"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content, file_path.name)
    
    def parse_content(self, content: str, filename: str) -> StackDiff:
        """Parse diff content and return StackDiff"""
        lines = content.split('\n')
        
        # Extract stack name and metadata from filename
        stack_name = self._extract_stack_name(filename)
        account_id = self._extract_account_id(filename)
        region = self._extract_region(filename)
        
        stack_diff = StackDiff(
            stack_name=stack_name,
            account_id=account_id,
            region=region
        )
        
        self.current_stack = stack_diff
        self.parsing_iam_section = False
        self.parsing_resources_section = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for different sections
            if line.startswith("Template"):
                i = self._parse_template_section(lines, i)
            elif line.startswith("IAM Statement Changes"):
                i = self._parse_iam_section(lines, i)
            elif line.startswith("Resources"):
                i = self._parse_resources_section(lines, i)
            else:
                i += 1
        
        return stack_diff
    
    def parse_directory(self, directory: Path) -> DiffAnalysis:
        """Parse all diff files in a directory"""
        analysis = DiffAnalysis()
        
        diff_files = list(directory.glob("*.diff"))
        analysis.total_stacks = len(diff_files)
        
        for file_path in diff_files:
            try:
                stack_diff = self.parse_file(file_path)
                analysis.stack_diffs.append(stack_diff)
                analysis.total_resources_changed += len(stack_diff.resource_changes)
                analysis.total_iam_changes += len(stack_diff.iam_statement_changes)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                continue
        
        return analysis
    
    def _extract_stack_name(self, filename: str) -> str:
        """Extract stack name from filename"""
        # Remove .diff extension
        name = filename.replace('.diff', '')
        return name
    
    def _extract_account_id(self, filename: str) -> Optional[str]:
        """Extract AWS account ID from filename"""
        match = re.search(r'(\d{12})', filename)
        return match.group(1) if match else None
    
    def _extract_region(self, filename: str) -> Optional[str]:
        """Extract AWS region from filename"""
        # Look for region patterns like us-east-1, ap-southeast-2
        match = re.search(r'([a-z]{2}-[a-z]+-\d)', filename)
        return match.group(1) if match else None
    
    def _parse_template_section(self, lines: List[str], start_idx: int) -> int:
        """Parse the Template section"""
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i]
            
            # Look for description changes
            if line.startswith("[~] Description"):
                desc_change = self._parse_description_change(line)
                if desc_change:
                    self.current_stack.description_change = desc_change
            
            # Stop when we hit the next section
            if (line.startswith("IAM Statement Changes") or 
                line.startswith("Resources") or 
                line.strip() == ""):
                break
            
            i += 1
        
        return i
    
    def _parse_description_change(self, line: str) -> Optional[PropertyChange]:
        """Parse description change line"""
        # Example: [~] Description Description: (SO0199-security) Landing Zone Accelerator on AWS. Version 1.10.0. to (SO0199-security) Landing Zone Accelerator on AWS. Version 1.12.1.
        match = re.search(r'Description: (.+?) to (.+)', line)
        if match:
            return PropertyChange(
                property_path="Description",
                change_type=ChangeType.MODIFY,
                old_value=match.group(1).strip(),
                new_value=match.group(2).strip()
            )
        return None
    
    def _parse_iam_section(self, lines: List[str], start_idx: int) -> int:
        """Parse the IAM Statement Changes section"""
        i = start_idx + 1
        
        # Skip the table header
        while i < len(lines) and not lines[i].startswith("│"):
            i += 1
        
        # Skip header row
        if i < len(lines) and lines[i].startswith("│"):
            i += 1
        
        # Skip separator row
        if i < len(lines) and lines[i].startswith("├"):
            i += 1
        
        # Parse IAM statement rows
        while i < len(lines):
            line = lines[i]
            
            if line.startswith("│"):
                iam_change = self._parse_iam_statement_row(line)
                if iam_change:
                    self.current_stack.iam_statement_changes.append(iam_change)
            elif line.startswith("└") or line.startswith("Resources"):
                break
            
            i += 1
        
        return i
    
    def _parse_iam_statement_row(self, line: str) -> Optional[IAMStatementChange]:
        """Parse a single IAM statement table row"""
        # Split by │ and clean up the parts
        parts = [part.strip() for part in line.split("│")]
        
        if len(parts) < 6:
            return None
        
        try:
            change_type_str = parts[1].strip()
            change_type = ChangeType.ADD if change_type_str == "+" else ChangeType.REMOVE if change_type_str == "-" else ChangeType.MODIFY
            
            resource = parts[2]
            effect = parts[3]
            action = parts[4]
            principal = parts[5] if len(parts) > 5 else None
            
            return IAMStatementChange(
                effect=effect,
                action=action,
                resource=resource,
                principal=principal,
                change_type=change_type
            )
        except (IndexError, ValueError):
            return None
    
    def _parse_resources_section(self, lines: List[str], start_idx: int) -> int:
        """Parse the Resources section"""
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i]
            
            if not line.strip():
                i += 1
                continue
            
            # Parse resource changes
            if line.startswith("[+]") or line.startswith("[-]") or line.startswith("[~]"):
                resource_change = self._parse_resource_change(lines, i)
                if resource_change:
                    self.current_stack.resource_changes.append(resource_change)
                    i = self._skip_resource_details(lines, i)
                else:
                    i += 1
            else:
                i += 1
        
        return i
    
    def _parse_resource_change(self, lines: List[str], start_idx: int) -> Optional[ResourceChange]:
        """Parse a resource change entry"""
        line = lines[start_idx]
        
        # Extract change type
        if line.startswith("[+]"):
            change_type = ChangeType.ADD
        elif line.startswith("[-]"):
            change_type = ChangeType.REMOVE
        elif line.startswith("[~]"):
            change_type = ChangeType.MODIFY
        else:
            return None
        
        # Extract resource type and logical ID
        # Format: [+] AWS::SSM::Parameter SsmParamAcceleratorVersionFF83282D
        match = re.search(r'\[.\] ([\w:]+) (\w+)', line)
        if not match:
            return None
        
        resource_type = match.group(1)
        logical_id = match.group(2)
        
        resource_change = ResourceChange(
            logical_id=logical_id,
            resource_type=resource_type,
            change_type=change_type
        )
        
        # Parse property changes for modified resources
        if change_type == ChangeType.MODIFY:
            property_changes = self._parse_property_changes(lines, start_idx + 1)
            resource_change.property_changes = property_changes
        
        return resource_change
    
    def _parse_property_changes(self, lines: List[str], start_idx: int) -> List[PropertyChange]:
        """Parse property changes for a modified resource"""
        property_changes = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            
            # Stop if we hit another resource or end of section
            if (line.startswith("[") or 
                not line.strip() or 
                (line.strip() and not line.startswith(" ") and not line.startswith("│"))):
                break
            
            # Parse property change lines
            if "├─ [-]" in line or "└─ [+]" in line or "├─ [~]" in line:
                prop_change = self._parse_single_property_change(line)
                if prop_change:
                    property_changes.append(prop_change)
            
            i += 1
        
        return property_changes
    
    def _parse_single_property_change(self, line: str) -> Optional[PropertyChange]:
        """Parse a single property change line"""
        # Example: │       ├─ [-] 1.10.0
        # Example: │       └─ [+] 1.12.1
        # Example: ├─ [~] Value
        
        if "[-]" in line:
            change_type = ChangeType.REMOVE
            value_match = re.search(r'\[-\] (.+)', line)
            if value_match:
                return PropertyChange(
                    property_path="Value",
                    change_type=change_type,
                    old_value=value_match.group(1).strip()
                )
        elif "[+]" in line:
            change_type = ChangeType.ADD
            value_match = re.search(r'\[\+\] (.+)', line)
            if value_match:
                return PropertyChange(
                    property_path="Value",
                    change_type=change_type,
                    new_value=value_match.group(1).strip()
                )
        elif "[~]" in line:
            change_type = ChangeType.MODIFY
            prop_match = re.search(r'\[~\] (.+)', line)
            if prop_match:
                return PropertyChange(
                    property_path=prop_match.group(1).strip(),
                    change_type=change_type
                )
        
        return None
    
    def _skip_resource_details(self, lines: List[str], start_idx: int) -> int:
        """Skip detailed resource change information"""
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i]
            
            # Stop when we hit another resource or section
            if (line.startswith("[") or 
                (line.strip() and not line.startswith(" ") and not line.startswith("│"))):
                break
            
            i += 1
        
        return i