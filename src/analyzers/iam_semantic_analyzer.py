"""
Semantic analyzer for IAM policy changes to distinguish formal vs substantive changes
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from ..models.diff_models import IAMStatementChange, ChangeType


class IAMChangeType(str, Enum):
    """Types of IAM changes from a semantic perspective"""
    FORMAL = "formal"           # Structure changes, no security impact
    SUBSTANTIVE = "substantive" # Permission changes, security impact
    MIXED = "mixed"            # Both formal and substantive elements


class IAMSemanticAnalyzer:
    """Analyzes IAM policy changes for semantic meaning"""
    
    def __init__(self):
        self.cloudformation_ref_pattern = re.compile(r'\$\{[^}]+\}')
        self.arn_pattern = re.compile(r'arn:[^:]*:[^:]*:[^:]*:[^:]*:[^:]*')
    
    def analyze_iam_changes(self, iam_changes: List[IAMStatementChange]) -> Dict[str, Any]:
        """Analyze a list of IAM changes for semantic meaning"""
        if not iam_changes:
            return {
                "total_changes": 0,
                "formal_changes": 0,
                "substantive_changes": 0,
                "change_pairs": [],
                "overall_assessment": "No IAM changes detected"
            }
        
        # Group changes by resource for comparison
        resource_groups = self._group_changes_by_resource(iam_changes)
        
        analysis_results = {
            "total_changes": len(iam_changes),
            "formal_changes": 0,
            "substantive_changes": 0,
            "change_pairs": [],
            "resource_analyses": {},
            "overall_assessment": ""
        }
        
        # Analyze each resource group
        for resource, changes in resource_groups.items():
            resource_analysis = self._analyze_resource_changes(resource, changes)
            analysis_results["resource_analyses"][resource] = resource_analysis
            
            # Update counters
            analysis_results["formal_changes"] += resource_analysis["formal_count"]
            analysis_results["substantive_changes"] += resource_analysis["substantive_count"]
            
            # Add change pairs
            analysis_results["change_pairs"].extend(resource_analysis["change_pairs"])
        
        # Generate overall assessment
        analysis_results["overall_assessment"] = self._generate_overall_assessment(analysis_results)
        
        return analysis_results
    
    def _group_changes_by_resource(self, iam_changes: List[IAMStatementChange]) -> Dict[str, List[IAMStatementChange]]:
        """Group IAM changes by resource for paired analysis"""
        resource_groups = {}
        
        for change in iam_changes:
            resource_key = self._normalize_resource_name(change.resource)
            if resource_key not in resource_groups:
                resource_groups[resource_key] = []
            resource_groups[resource_key].append(change)
        
        return resource_groups
    
    def _normalize_resource_name(self, resource: str) -> str:
        """Normalize resource names for comparison"""
        if isinstance(resource, list):
            resource = str(resource)
        
        # Remove CloudFormation intrinsic functions for comparison
        normalized = self.cloudformation_ref_pattern.sub('${CF_REF}', resource)
        return normalized
    
    def _analyze_resource_changes(self, resource: str, changes: List[IAMStatementChange]) -> Dict[str, Any]:
        """Analyze changes for a specific resource"""
        analysis = {
            "resource": resource,
            "change_count": len(changes),
            "formal_count": 0,
            "substantive_count": 0,
            "change_pairs": [],
            "assessment": ""
        }
        
        # Look for ADD/REMOVE pairs
        add_changes = [c for c in changes if c.change_type == ChangeType.ADD]
        remove_changes = [c for c in changes if c.change_type == ChangeType.REMOVE]
        
        # Analyze pairs
        for add_change in add_changes:
            matching_remove = self._find_matching_remove_change(add_change, remove_changes)
            if matching_remove:
                pair_analysis = self._analyze_change_pair(add_change, matching_remove)
                analysis["change_pairs"].append(pair_analysis)
                
                if pair_analysis["type"] == IAMChangeType.FORMAL:
                    analysis["formal_count"] += 1
                elif pair_analysis["type"] == IAMChangeType.SUBSTANTIVE:
                    analysis["substantive_count"] += 1
            else:
                # Standalone add - likely substantive
                analysis["substantive_count"] += 1
                analysis["change_pairs"].append({
                    "type": IAMChangeType.SUBSTANTIVE,
                    "add_change": add_change,
                    "remove_change": None,
                    "description": "New permission added",
                    "security_impact": "MEDIUM"
                })
        
        # Handle standalone removes
        for remove_change in remove_changes:
            if not any(pair["remove_change"] == remove_change for pair in analysis["change_pairs"]):
                analysis["substantive_count"] += 1
                analysis["change_pairs"].append({
                    "type": IAMChangeType.SUBSTANTIVE,
                    "add_change": None,
                    "remove_change": remove_change,
                    "description": "Permission removed",
                    "security_impact": "LOW"
                })
        
        # Generate assessment
        analysis["assessment"] = self._generate_resource_assessment(analysis)
        
        return analysis
    
    def _find_matching_remove_change(self, add_change: IAMStatementChange, remove_changes: List[IAMStatementChange]) -> Optional[IAMStatementChange]:
        """Find a matching remove change for an add change"""
        for remove_change in remove_changes:
            if self._changes_match_for_pairing(add_change, remove_change):
                return remove_change
        return None
    
    def _changes_match_for_pairing(self, add_change: IAMStatementChange, remove_change: IAMStatementChange) -> bool:
        """Check if two changes should be paired for analysis"""
        # Must have same basic policy elements
        if (add_change.effect != remove_change.effect or
            add_change.action != remove_change.action or
            add_change.principal != remove_change.principal):
            return False
        
        # Resource should be the same (accounting for CloudFormation references)
        add_resource = self._normalize_resource_name(add_change.resource)
        remove_resource = self._normalize_resource_name(remove_change.resource)
        
        return add_resource == remove_resource
    
    def _analyze_change_pair(self, add_change: IAMStatementChange, remove_change: IAMStatementChange) -> Dict[str, Any]:
        """Analyze a pair of ADD/REMOVE changes"""
        pair_analysis = {
            "type": IAMChangeType.FORMAL,
            "add_change": add_change,
            "remove_change": remove_change,
            "description": "",
            "security_impact": "NONE",
            "details": {}
        }
        
        # Compare conditions
        condition_analysis = self._compare_conditions(add_change.condition, remove_change.condition)
        pair_analysis["details"]["condition_analysis"] = condition_analysis
        
        if condition_analysis["type"] == "formal":
            pair_analysis["type"] = IAMChangeType.FORMAL
            pair_analysis["description"] = condition_analysis["description"]
            pair_analysis["security_impact"] = "NONE"
        else:
            pair_analysis["type"] = IAMChangeType.SUBSTANTIVE
            pair_analysis["description"] = condition_analysis["description"]
            pair_analysis["security_impact"] = condition_analysis["security_impact"]
        
        return pair_analysis
    
    def _compare_conditions(self, add_condition: Optional[Dict[str, Any]], 
                          remove_condition: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare two IAM conditions for semantic differences"""
        if add_condition is None and remove_condition is None:
            return {
                "type": "formal",
                "description": "No conditions in either change",
                "security_impact": "NONE"
            }
        
        if add_condition is None or remove_condition is None:
            return {
                "type": "substantive",
                "description": "Condition added or removed",
                "security_impact": "MEDIUM"
            }
        
        # Parse conditions if they're strings
        try:
            if isinstance(add_condition, str):
                add_condition = json.loads(add_condition)
            if isinstance(remove_condition, str):
                remove_condition = json.loads(remove_condition)
        except json.JSONDecodeError:
            return {
                "type": "unknown",
                "description": "Unable to parse conditions",
                "security_impact": "MEDIUM"
            }
        
        # Compare condition structure and values
        semantic_diff = self._find_semantic_condition_differences(add_condition, remove_condition)
        
        if semantic_diff["is_formal"]:
            return {
                "type": "formal",
                "description": semantic_diff["description"],
                "security_impact": "NONE",
                "details": semantic_diff["details"]
            }
        else:
            return {
                "type": "substantive",
                "description": semantic_diff["description"],
                "security_impact": semantic_diff["security_impact"],
                "details": semantic_diff["details"]
            }
    
    def _find_semantic_condition_differences(self, add_cond: Dict[str, Any], 
                                           remove_cond: Dict[str, Any]) -> Dict[str, Any]:
        """Find semantic differences between two conditions"""
        differences = {
            "is_formal": True,
            "description": "",
            "security_impact": "NONE",
            "details": []
        }
        
        # Check each condition operator
        all_operators = set(add_cond.keys()) | set(remove_cond.keys())
        
        for operator in all_operators:
            add_values = add_cond.get(operator, {})
            remove_values = remove_cond.get(operator, {})
            
            if operator not in add_cond:
                differences["is_formal"] = False
                differences["description"] = f"Condition operator '{operator}' added"
                differences["security_impact"] = "MEDIUM"
                differences["details"].append(f"Added: {operator}")
                continue
            
            if operator not in remove_cond:
                differences["is_formal"] = False
                differences["description"] = f"Condition operator '{operator}' removed"
                differences["security_impact"] = "MEDIUM"
                differences["details"].append(f"Removed: {operator}")
                continue
            
            # Compare values within the operator
            value_comparison = self._compare_condition_values(add_values, remove_values)
            differences["details"].append(f"{operator}: {value_comparison['description']}")
            
            if not value_comparison["is_formal"]:
                differences["is_formal"] = False
                differences["description"] = f"Condition '{operator}' values changed: {value_comparison['description']}"
                differences["security_impact"] = value_comparison["security_impact"]
        
        # If all differences are formal, create appropriate description
        if differences["is_formal"]:
            if any("string to array" in detail for detail in differences["details"]):
                differences["description"] = "Condition values converted from string to array format (formal change)"
            else:
                differences["description"] = "Condition structure changed without semantic impact"
        
        return differences
    
    def _compare_condition_values(self, add_values: Dict[str, Any], 
                                 remove_values: Dict[str, Any]) -> Dict[str, Any]:
        """Compare values within a condition operator"""
        comparison = {
            "is_formal": True,
            "description": "",
            "security_impact": "NONE"
        }
        
        all_keys = set(add_values.keys()) | set(remove_values.keys())
        
        for key in all_keys:
            add_val = add_values.get(key)
            remove_val = remove_values.get(key)
            
            if add_val is None or remove_val is None:
                comparison["is_formal"] = False
                comparison["description"] = f"Condition key '{key}' added or removed"
                comparison["security_impact"] = "MEDIUM"
                continue
            
            # Check for string/array conversion
            if self._is_string_array_conversion(add_val, remove_val):
                comparison["description"] = f"'{key}' converted from string to array (formal change)"
                # This remains formal
            elif self._is_array_string_conversion(add_val, remove_val):
                comparison["description"] = f"'{key}' converted from array to string (formal change)"
                # This remains formal
            elif add_val != remove_val:
                comparison["is_formal"] = False
                comparison["description"] = f"'{key}' value changed from {remove_val} to {add_val}"
                comparison["security_impact"] = "MEDIUM"
        
        return comparison
    
    def _is_string_array_conversion(self, add_val: Any, remove_val: Any) -> bool:
        """Check if this is a string to array conversion with same content"""
        if isinstance(add_val, list) and isinstance(remove_val, str):
            return len(add_val) == 1 and add_val[0] == remove_val
        return False
    
    def _is_array_string_conversion(self, add_val: Any, remove_val: Any) -> bool:
        """Check if this is an array to string conversion with same content"""
        if isinstance(add_val, str) and isinstance(remove_val, list):
            return len(remove_val) == 1 and remove_val[0] == add_val
        return False
    
    def _generate_resource_assessment(self, analysis: Dict[str, Any]) -> str:
        """Generate assessment text for a resource"""
        formal_count = analysis["formal_count"]
        substantive_count = analysis["substantive_count"]
        
        if formal_count > 0 and substantive_count == 0:
            return f"All {formal_count} change(s) are formal with no security impact"
        elif formal_count == 0 and substantive_count > 0:
            return f"All {substantive_count} change(s) are substantive and require security review"
        elif formal_count > 0 and substantive_count > 0:
            return f"{formal_count} formal change(s) with no impact, {substantive_count} substantive change(s) require review"
        else:
            return "No changes detected"
    
    def _generate_overall_assessment(self, analysis: Dict[str, Any]) -> str:
        """Generate overall assessment text"""
        formal_count = analysis["formal_changes"]
        substantive_count = analysis["substantive_changes"]
        total_count = analysis["total_changes"]
        
        if total_count == 0:
            return "No IAM changes detected"
        
        if formal_count > 0 and substantive_count == 0:
            return f"All {total_count} IAM changes are formal (no security impact)"
        elif formal_count == 0 and substantive_count > 0:
            return f"All {total_count} IAM changes are substantive (require security review)"
        else:
            return f"{formal_count} formal changes (no impact), {substantive_count} substantive changes (require review)"
    
    def get_change_summary_for_llm(self, analysis: Dict[str, Any]) -> str:
        """Get a formatted summary for LLM context"""
        summary_parts = [
            f"IAM SEMANTIC ANALYSIS SUMMARY:",
            f"Total Changes: {analysis['total_changes']}",
            f"Formal Changes: {analysis['formal_changes']} (no security impact)",
            f"Substantive Changes: {analysis['substantive_changes']} (require review)",
            f"Overall Assessment: {analysis['overall_assessment']}",
            ""
        ]
        
        if analysis["change_pairs"]:
            summary_parts.append("DETAILED CHANGE ANALYSIS:")
            for i, pair in enumerate(analysis["change_pairs"]):
                summary_parts.append(f"{i+1}. {pair['description']} (Security Impact: {pair['security_impact']})")
        
        return "\n".join(summary_parts)