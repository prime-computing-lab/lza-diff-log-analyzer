"""
File I/O and validation utilities for diff parsing
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Union, Dict, Any
from ..models.diff_models import DiffAnalysis, ComprehensiveAnalysisResult, StackDiff


class FileValidator:
    """Validates diff files and directories"""
    
    VALID_EXTENSIONS = {'.diff', '.txt'}
    EXPECTED_STACK_PREFIXES = {
        'AWSAccelerator-CustomizationsStack',
        'AWSAccelerator-DependenciesStack',
        'AWSAccelerator-FinalizeStack',
        'AWSAccelerator-IdentityCenterStack',
        'AWSAccelerator-KeyStack',
        'AWSAccelerator-LoggingStack',
        'AWSAccelerator-NetworkAssociationsStack',
        'AWSAccelerator-NetworkAssociationsGwlbStack',
        'AWSAccelerator-NetworkPrepStack',
        'AWSAccelerator-NetworkVpcStack',
        'AWSAccelerator-NetworkVpcDnsStack',
        'AWSAccelerator-NetworkVpcEndpointsStack',
        'AWSAccelerator-OperationsStack',
        'AWSAccelerator-OrganizationsStack',
        'AWSAccelerator-ResourcePolicyEnforcementStack',
        'AWSAccelerator-SecurityAuditStack',
        'AWSAccelerator-SecurityResourcesStack',
        'AWSAccelerator-SecurityStack',
    }
    
    @staticmethod
    def validate_file(file_path: Path) -> bool:
        """Validate a single diff file"""
        if not file_path.exists():
            return False
        
        if not file_path.is_file():
            return False
        
        if file_path.suffix.lower() not in FileValidator.VALID_EXTENSIONS:
            return False
        
        # Check if file is readable
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read first few lines to ensure it's valid
                first_lines = [f.readline() for _ in range(5)]
                
            # Basic content validation
            content = ''.join(first_lines)
            if 'Stack:' not in content and 'AWSAccelerator' not in content:
                return False
                
        except (IOError, UnicodeDecodeError):
            return False
        
        return True
    
    @staticmethod
    def validate_directory(directory: Path) -> Dict[str, Any]:
        """Validate a directory containing diff files"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_count': 0,
            'valid_files': [],
            'invalid_files': []
        }
        
        if not directory.exists():
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Directory does not exist: {directory}")
            return validation_result
        
        if not directory.is_dir():
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Path is not a directory: {directory}")
            return validation_result
        
        # Find all potential diff files
        diff_files = []
        for ext in FileValidator.VALID_EXTENSIONS:
            diff_files.extend(directory.glob(f"*{ext}"))
        
        validation_result['file_count'] = len(diff_files)
        
        if len(diff_files) == 0:
            validation_result['warnings'].append("No diff files found in directory")
        
        # Validate each file
        for file_path in diff_files:
            if FileValidator.validate_file(file_path):
                validation_result['valid_files'].append(str(file_path))
            else:
                validation_result['invalid_files'].append(str(file_path))
                validation_result['warnings'].append(f"Invalid diff file: {file_path.name}")
        
        # Check for expected LZA stack files
        found_prefixes = set()
        for file_path in validation_result['valid_files']:
            filename = Path(file_path).name
            for prefix in FileValidator.EXPECTED_STACK_PREFIXES:
                if filename.startswith(prefix):
                    found_prefixes.add(prefix)
                    break
        
        missing_prefixes = FileValidator.EXPECTED_STACK_PREFIXES - found_prefixes
        if missing_prefixes:
            validation_result['warnings'].append(
                f"Missing expected stack types: {', '.join(sorted(missing_prefixes))}"
            )
        
        return validation_result


class FileManager:
    """Manages file I/O operations for diff analysis"""
    
    @staticmethod
    def save_analysis(analysis: Union[DiffAnalysis, ComprehensiveAnalysisResult], output_path: Path, format: str = 'json') -> bool:
        """Save analysis results to file"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get the data dict from the analysis object
            if hasattr(analysis, 'dict'):
                data = analysis.dict()
            else:
                # Fallback for objects that don't have dict method
                data = analysis
            
            if format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format.lower() == 'yaml':
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return True
        except Exception as e:
            # Log the error for debugging
            print(f"Error saving analysis: {str(e)}")
            return False
    
    @staticmethod
    def load_analysis(input_path: Path) -> Optional[DiffAnalysis]:
        """Load analysis results from file"""
        try:
            if not input_path.exists():
                return None
            
            with open(input_path, 'r', encoding='utf-8') as f:
                if input_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif input_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    return None
            
            return DiffAnalysis(**data)
        except Exception:
            return None
    
    @staticmethod
    def get_diff_files(directory: Path) -> List[Path]:
        """Get all valid diff files from directory"""
        diff_files = []
        
        for ext in FileValidator.VALID_EXTENSIONS:
            potential_files = directory.glob(f"*{ext}")
            for file_path in potential_files:
                if FileValidator.validate_file(file_path):
                    diff_files.append(file_path)
        
        return sorted(diff_files)
    
    @staticmethod
    def create_output_structure(base_dir: Path) -> Dict[str, Path]:
        """Create standardized output directory structure"""
        paths = {
            'base': base_dir,
            'analysis': base_dir / 'analysis',
            'reports': base_dir / 'reports',
            'logs': base_dir / 'logs',
            'temp': base_dir / 'temp'
        }
        
        # Create directories
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        return paths
    
    @staticmethod
    def cleanup_temp_files(temp_dir: Path) -> bool:
        """Clean up temporary files"""
        try:
            if temp_dir.exists() and temp_dir.is_dir():
                for file_path in temp_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        # Recursively remove subdirectories
                        import shutil
                        shutil.rmtree(file_path)
            return True
        except Exception:
            return False

    @staticmethod
    def check_analysis_state(input_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Check if comprehensive analysis outputs exist and are recent enough to skip
        
        Args:
            input_dir: Directory containing diff log files
            output_dir: Directory containing analysis outputs
            
        Returns:
            Dict with analysis state information
        """
        state = {
            'has_previous_analysis': False,
            'analysis_is_recent': False,
            'can_skip': False,
            'comprehensive_file': None,
            'diff_analysis_file': None,
            'input_files': [],
            'analysis_age_hours': None,
            'recommendations': []
        }
        
        try:
            # Check for existing analysis files
            analysis_dir = output_dir / 'analysis'
            comprehensive_file = analysis_dir / 'comprehensive_analysis.json'
            diff_analysis_file = analysis_dir / 'diff_analysis.json'
            
            state['comprehensive_file'] = comprehensive_file
            state['diff_analysis_file'] = diff_analysis_file
            
            # Check if both files exist
            if comprehensive_file.exists() and diff_analysis_file.exists():
                state['has_previous_analysis'] = True
                
                # Check recency (within last 24 hours by default)
                analysis_time = datetime.fromtimestamp(comprehensive_file.stat().st_mtime)
                age = datetime.now() - analysis_time
                state['analysis_age_hours'] = age.total_seconds() / 3600
                
                # Consider recent if less than 24 hours old
                state['analysis_is_recent'] = age < timedelta(hours=24)
                
                # Get input files for comparison
                diff_files = FileManager.get_diff_files(input_dir)
                state['input_files'] = [str(f) for f in diff_files]
                
                # Check if input files have changed since analysis
                input_files_unchanged = True
                for diff_file in diff_files:
                    if diff_file.stat().st_mtime > comprehensive_file.stat().st_mtime:
                        input_files_unchanged = False
                        break
                
                # Can skip if analysis is recent and input hasn't changed
                state['can_skip'] = state['analysis_is_recent'] and input_files_unchanged
                
                if state['can_skip']:
                    state['recommendations'].append(
                        f"Found recent analysis from {analysis_time.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"({state['analysis_age_hours']:.1f} hours ago)"
                    )
                    state['recommendations'].append("Input files unchanged since last analysis")
                    state['recommendations'].append("Consider using --skip-comprehensive to save time")
                elif not state['analysis_is_recent']:
                    state['recommendations'].append(
                        f"Previous analysis is {state['analysis_age_hours']:.1f} hours old"
                    )
                    state['recommendations'].append("Consider re-running for fresh insights")
                elif not input_files_unchanged:
                    state['recommendations'].append("Input files have changed since last analysis")
                    state['recommendations'].append("Re-analysis recommended for accuracy")
            else:
                state['recommendations'].append("No previous comprehensive analysis found")
                state['recommendations'].append("Full analysis will be performed")
                
        except Exception as e:
            state['recommendations'].append(f"Error checking analysis state: {str(e)}")
            
        return state
    
    @staticmethod
    def load_existing_analysis(output_dir: Path) -> Optional[Any]:
        """
        Load existing comprehensive analysis results and reconstruct proper model objects
        
        Args:
            output_dir: Directory containing analysis outputs
            
        Returns:
            ComprehensiveAnalysisResult object or None if not found
        """
        try:
            analysis_dir = output_dir / 'analysis'
            comprehensive_file = analysis_dir / 'comprehensive_analysis.json'
            
            if not comprehensive_file.exists():
                return None
                
            with open(comprehensive_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Reconstruct the proper model objects from JSON
            return FileManager._reconstruct_comprehensive_analysis(data)
                
        except Exception:
            return None
    
    @staticmethod
    def _reconstruct_comprehensive_analysis(data: Dict[str, Any]) -> Optional[Any]:
        """
        Reconstruct ComprehensiveAnalysisResult object from JSON data
        
        Args:
            data: Raw JSON data dictionary
            
        Returns:
            ComprehensiveAnalysisResult object or None if reconstruction fails
        """
        try:
            from ..models.diff_models import (
                ComprehensiveAnalysisResult, DiffAnalysis, StackDiff, 
                ResourceChange, IAMStatementChange, ChangeType
            )
            from datetime import datetime
            
            # Reconstruct DiffAnalysis from input_analysis
            input_analysis_data = data.get('input_analysis', {})
            
            # Reconstruct StackDiff objects
            stack_diffs = []
            for stack_data in input_analysis_data.get('stack_diffs', []):
                # Reconstruct ResourceChange objects
                resource_changes = []
                for rc_data in stack_data.get('resource_changes', []):
                    rc = ResourceChange(
                        logical_id=rc_data.get('logical_id', ''),
                        resource_type=rc_data.get('resource_type', ''),
                        change_type=ChangeType(rc_data.get('change_type', '+')),
                        property_changes=rc_data.get('property_changes', {}),
                        before_properties=rc_data.get('before_properties', {}),
                        after_properties=rc_data.get('after_properties', {})
                    )
                    resource_changes.append(rc)
                
                # Reconstruct IAMStatementChange objects
                iam_changes = []
                for iam_data in stack_data.get('iam_statement_changes', []):
                    iam = IAMStatementChange(
                        change_type=ChangeType(iam_data.get('change_type', '+')),
                        effect=iam_data.get('effect', ''),
                        action=iam_data.get('action', ''),
                        resource=iam_data.get('resource', ''),
                        principal=iam_data.get('principal'),
                        condition=iam_data.get('condition'),
                        statement_context=iam_data.get('statement_context', {})
                    )
                    iam_changes.append(iam)
                
                # Create StackDiff object
                stack_diff = StackDiff(
                    stack_name=stack_data.get('stack_name', ''),
                    account_id=stack_data.get('account_id', ''),
                    region=stack_data.get('region', ''),
                    diff_file_path=stack_data.get('diff_file_path'),
                    resource_changes=resource_changes,
                    iam_statement_changes=iam_changes,
                    parameters_changed=stack_data.get('parameters_changed', {}),
                    outputs_changed=stack_data.get('outputs_changed', {}),
                    has_security_changes=stack_data.get('has_security_changes', False),
                    has_deletions=stack_data.get('has_deletions', False)
                )
                stack_diffs.append(stack_diff)
            
            # Create DiffAnalysis object
            diff_analysis = DiffAnalysis(
                stack_diffs=stack_diffs,
                total_stacks=input_analysis_data.get('total_stacks', 0),
                total_resources_changed=input_analysis_data.get('total_resources_changed', 0),
                total_iam_changes=input_analysis_data.get('total_iam_changes', 0),
                analysis_timestamp=datetime.fromisoformat(input_analysis_data.get('analysis_timestamp', datetime.now().isoformat())),
                summary=input_analysis_data.get('summary', {})
            )
            
            # Parse created_at timestamp if present
            created_at = data.get('created_at')
            if created_at and isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif not created_at:
                created_at = datetime.now()
            
            # Create ComprehensiveAnalysisResult object
            comprehensive_result = ComprehensiveAnalysisResult(
                analysis_id=data.get('analysis_id', 'loaded_analysis'),
                created_at=created_at,
                input_analysis=diff_analysis,
                rule_based_analysis=data.get('rule_based_analysis', {}),
                llm_analysis=data.get('llm_analysis'),
                combined_assessment=data.get('combined_assessment'),
                metadata=data.get('metadata', {})
            )
            
            return comprehensive_result
            
        except Exception as e:
            # If reconstruction fails, return the raw data as fallback
            # This ensures compatibility while we debug any issues
            print(f"Warning: Failed to reconstruct analysis models: {e}")
            return data
    
    @staticmethod
    def get_diff_file_mapping(input_dir: Path) -> Dict[str, str]:
        """
        Create a mapping of stack names to their corresponding diff file names
        
        Args:
            input_dir: Directory containing diff log files
            
        Returns:
            Dict mapping stack names to diff file names
        """
        mapping = {}
        
        try:
            diff_files = FileManager.get_diff_files(input_dir)
            
            for diff_file in diff_files:
                # Extract stack name from filename
                # Format: AWSAccelerator-StackType-AccountId-Region.diff
                filename = diff_file.name
                
                # Remove extension
                if filename.endswith('.diff'):
                    stack_name = filename[:-5]  # Remove .diff
                elif filename.endswith('.txt'):
                    stack_name = filename[:-4]  # Remove .txt
                else:
                    stack_name = filename
                
                mapping[stack_name] = filename
                
        except Exception:
            pass
            
        return mapping


class ConfigManager:
    """Manages configuration files"""
    
    DEFAULT_CONFIG = {
        'llm': {
            'provider': 'ollama',
            'model': 'qqwen3:30b-a3b',
            'temperature': 0.1,
            'max_tokens': 2048
        },
        'analysis': {
            'risk_threshold': 0.7,
            'include_low_risk': False,
            'detailed_property_analysis': True
        },
        'output': {
            'format': 'json',
            'include_raw_diffs': False,
            'generate_summary': True
        },
        'mcp': {
            'enabled': False,
            'servers': []
        }
    }
    
    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from file or return defaults"""
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.suffix.lower() == '.json':
                        user_config = json.load(f)
                    else:
                        user_config = yaml.safe_load(f)
                
                # Merge with defaults
                config = ConfigManager.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            except Exception:
                pass
        
        return ConfigManager.DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_path: Path) -> bool:
        """Save configuration to file"""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2)
                else:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get the default configuration file path"""
        home_dir = Path.home()
        config_dir = home_dir / '.lza-analyzer'
        config_dir.mkdir(exist_ok=True)
        return config_dir / 'config.yaml'