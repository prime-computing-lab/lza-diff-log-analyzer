"""
Enhanced IAM parser that handles multi-line IAM statement tables correctly
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from ..models.diff_models import IAMStatementChange, ChangeType


class EnhancedIAMParser:
    """Enhanced parser for IAM Statement Changes tables in CloudFormation diffs"""
    
    def __init__(self):
        # Patterns for IAM table parsing
        self.iam_table_start = re.compile(r'IAM Statement Changes')
        self.table_border = re.compile(r'[┌┬┐├┼┤└┴┘─│]')
        self.table_row = re.compile(r'│\s*([+\-~]?)\s*│')
        
        # Patterns for extracting table content
        self.change_indicator = re.compile(r'^\s*([+\-~])\s*')
        self.json_block = re.compile(r'({[^}]*})')
        
    def parse_iam_statements(self, lines: List[str], start_idx: int) -> Tuple[List[IAMStatementChange], int]:
        """
        Parse IAM Statement Changes table from diff lines
        
        Args:
            lines: List of diff lines
            start_idx: Index where IAM table starts
            
        Returns:
            Tuple of (parsed_statements, next_index)
        """
        statements = []
        i = start_idx
        
        # Find the table header
        while i < len(lines) and not self.iam_table_start.search(lines[i]):
            i += 1
        
        if i >= len(lines):
            return statements, i
        
        # Skip to the actual table content (after header borders)
        i += 1
        while i < len(lines) and self.table_border.search(lines[i]):
            i += 1
        
        # Parse table rows
        current_statement = None
        while i < len(lines):
            line = lines[i]
            
            # Check if we've reached the end of the table
            if line.startswith('└') or line.startswith('Resources') or line.strip() == '':
                break
            
            # Skip border lines
            if self.table_border.search(line) and not '│' in line:
                i += 1
                continue
            
            # Parse table row
            parsed_row = self._parse_table_row(line)
            if parsed_row:
                if parsed_row['is_new_statement']:
                    # Save previous statement if exists
                    if current_statement:
                        statements.append(current_statement)
                    
                    # Start new statement
                    current_statement = IAMStatementChange(
                        effect=parsed_row['effect'],
                        action=parsed_row['action'],
                        resource=parsed_row['resource'],
                        principal=parsed_row['principal'],
                        condition=parsed_row['condition'],
                        change_type=parsed_row['change_type']
                    )
                else:
                    # Continue building current statement
                    if current_statement:
                        self._merge_continuation_row(current_statement, parsed_row)
            
            i += 1
        
        # Add the last statement
        if current_statement:
            statements.append(current_statement)
        
        return statements, i
    
    def _parse_table_row(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single table row"""
        if not '│' in line:
            return None
        
        # Split by │ and clean up
        parts = [part.strip() for part in line.split('│')]
        
        if len(parts) < 6:
            return None
        
        try:
            # Extract change type
            change_indicator = parts[1].strip()
            is_new_statement = change_indicator in ['+', '-', '~']
            
            if is_new_statement:
                change_type = self._parse_change_type(change_indicator)
                
                return {
                    'is_new_statement': True,
                    'change_type': change_type,
                    'resource': parts[2].strip(),
                    'effect': parts[3].strip(),
                    'action': parts[4].strip(),
                    'principal': parts[5].strip() if len(parts) > 5 else None,
                    'condition': self._extract_condition_from_parts(parts[6:]) if len(parts) > 6 else None
                }
            else:
                # This is a continuation row
                return {
                    'is_new_statement': False,
                    'continuation_content': ' '.join(parts[2:])  # Join all content parts
                }
        
        except (IndexError, ValueError):
            return None
    
    def _parse_change_type(self, indicator: str) -> ChangeType:
        """Parse change type from indicator"""
        if indicator == '+':
            return ChangeType.ADD
        elif indicator == '-':
            return ChangeType.REMOVE
        elif indicator == '~':
            return ChangeType.MODIFY
        else:
            return ChangeType.NO_CHANGE
    
    def _extract_condition_from_parts(self, parts: List[str]) -> Optional[Dict[str, Any]]:
        """Extract condition from table parts"""
        if not parts:
            return None
        
        condition_text = ' '.join(parts).strip()
        
        # Try to parse as JSON
        try:
            # Look for JSON-like structures
            json_match = self.json_block.search(condition_text)
            if json_match:
                return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
        
        # Return as string if not JSON
        return condition_text if condition_text else None
    
    def _merge_continuation_row(self, statement: IAMStatementChange, row_data: Dict[str, Any]):
        """Merge continuation row data into existing statement"""
        if not row_data.get('continuation_content'):
            return
        
        continuation = row_data['continuation_content'].strip()
        
        # Try to parse continuation as JSON for conditions
        try:
            # Look for JSON structures in continuation
            json_match = self.json_block.search(continuation)
            if json_match:
                json_data = json.loads(json_match.group(1))
                
                # Merge with existing condition
                if statement.condition:
                    if isinstance(statement.condition, dict):
                        statement.condition.update(json_data)
                    else:
                        statement.condition = json_data
                else:
                    statement.condition = json_data
        except (json.JSONDecodeError, AttributeError):
            # If not JSON, append to condition as string
            if statement.condition:
                if isinstance(statement.condition, str):
                    statement.condition += f" {continuation}"
                else:
                    statement.condition = f"{statement.condition} {continuation}"
            else:
                statement.condition = continuation
    
    def group_related_changes(self, statements: List[IAMStatementChange]) -> List[Dict[str, Any]]:
        """Group related ADD/REMOVE pairs for semantic analysis"""
        grouped = []
        processed = set()
        
        for i, statement in enumerate(statements):
            if i in processed:
                continue
            
            if statement.change_type == ChangeType.ADD:
                # Look for matching REMOVE
                matching_remove = None
                for j, other in enumerate(statements[i+1:], i+1):
                    if (j not in processed and 
                        other.change_type == ChangeType.REMOVE and
                        self._statements_match_for_grouping(statement, other)):
                        matching_remove = other
                        processed.add(j)
                        break
                
                if matching_remove:
                    grouped.append({
                        'type': 'change_pair',
                        'add_statement': statement,
                        'remove_statement': matching_remove,
                        'resource': statement.resource
                    })
                else:
                    grouped.append({
                        'type': 'standalone_add',
                        'statement': statement,
                        'resource': statement.resource
                    })
                
                processed.add(i)
            
            elif statement.change_type == ChangeType.REMOVE:
                # Only add if not already processed as part of a pair
                if i not in processed:
                    grouped.append({
                        'type': 'standalone_remove',
                        'statement': statement,
                        'resource': statement.resource
                    })
                    processed.add(i)
        
        return grouped
    
    def _statements_match_for_grouping(self, add_stmt: IAMStatementChange, 
                                     remove_stmt: IAMStatementChange) -> bool:
        """Check if two statements should be grouped together"""
        # Must have same basic elements
        return (add_stmt.effect == remove_stmt.effect and
                add_stmt.action == remove_stmt.action and
                add_stmt.resource == remove_stmt.resource and
                add_stmt.principal == remove_stmt.principal)
    
    def analyze_semantic_changes(self, grouped_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze grouped changes for semantic meaning"""
        analysis = {
            'total_groups': len(grouped_changes),
            'formal_changes': 0,
            'substantive_changes': 0,
            'details': []
        }
        
        for group in grouped_changes:
            if group['type'] == 'change_pair':
                # Analyze the pair
                pair_analysis = self._analyze_change_pair(
                    group['add_statement'], 
                    group['remove_statement']
                )
                analysis['details'].append(pair_analysis)
                
                if pair_analysis['is_formal']:
                    analysis['formal_changes'] += 1
                else:
                    analysis['substantive_changes'] += 1
            
            else:
                # Standalone changes are typically substantive
                analysis['substantive_changes'] += 1
                analysis['details'].append({
                    'type': group['type'],
                    'is_formal': False,
                    'resource': group['resource'],
                    'description': f"Standalone {group['type'].replace('_', ' ')}"
                })
        
        return analysis
    
    def _analyze_change_pair(self, add_stmt: IAMStatementChange, 
                           remove_stmt: IAMStatementChange) -> Dict[str, Any]:
        """Analyze a pair of ADD/REMOVE statements"""
        analysis = {
            'type': 'change_pair',
            'is_formal': True,
            'resource': add_stmt.resource,
            'description': '',
            'condition_analysis': None
        }
        
        # Compare conditions
        if add_stmt.condition != remove_stmt.condition:
            condition_analysis = self._compare_conditions(add_stmt.condition, remove_stmt.condition)
            analysis['condition_analysis'] = condition_analysis
            analysis['is_formal'] = condition_analysis['is_formal']
            analysis['description'] = condition_analysis['description']
        else:
            analysis['description'] = 'No meaningful changes detected'
        
        return analysis
    
    def _compare_conditions(self, add_condition: Any, remove_condition: Any) -> Dict[str, Any]:
        """Compare two conditions for semantic differences"""
        if add_condition is None and remove_condition is None:
            return {'is_formal': True, 'description': 'No conditions'}
        
        if add_condition is None or remove_condition is None:
            return {'is_formal': False, 'description': 'Condition added or removed'}
        
        # Convert to comparable format
        add_cond = self._normalize_condition(add_condition)
        remove_cond = self._normalize_condition(remove_condition)
        
        # Check for string-to-array conversion
        if self._is_string_array_conversion(add_cond, remove_cond):
            return {
                'is_formal': True,
                'description': 'String-to-array conversion (no security impact)'
            }
        
        # Check for other formal changes
        if add_cond == remove_cond:
            return {
                'is_formal': True,
                'description': 'Formatting change only'
            }
        
        # Substantive change
        return {
            'is_formal': False,
            'description': f'Condition changed from {remove_cond} to {add_cond}'
        }
    
    def _normalize_condition(self, condition: Any) -> Any:
        """Normalize condition for comparison"""
        if isinstance(condition, str):
            try:
                return json.loads(condition)
            except json.JSONDecodeError:
                return condition
        return condition
    
    def _is_string_array_conversion(self, cond1: Any, cond2: Any) -> bool:
        """Check if the difference is just string-to-array conversion"""
        if not isinstance(cond1, dict) or not isinstance(cond2, dict):
            return False
        
        # Check each key in the conditions
        for key in set(cond1.keys()) | set(cond2.keys()):
            if key not in cond1 or key not in cond2:
                return False  # Key added/removed
            
            val1 = cond1[key]
            val2 = cond2[key]
            
            # Check nested dictionaries
            if isinstance(val1, dict) and isinstance(val2, dict):
                if not self._is_string_array_conversion(val1, val2):
                    return False
            else:
                # Check for string/array conversion
                if isinstance(val1, list) and isinstance(val2, str):
                    if len(val1) != 1 or val1[0] != val2:
                        return False
                elif isinstance(val1, str) and isinstance(val2, list):
                    if len(val2) != 1 or val2[0] != val1:
                        return False
                elif val1 != val2:
                    return False
        
        return True