"""
Unit tests for file utilities
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.parsers.file_utils import FileValidator, FileManager, ConfigManager
from src.models.diff_models import DiffAnalysis, StackDiff


class TestFileValidator:
    """Test cases for FileValidator class"""
    
    def test_validate_valid_diff_file(self):
        """Test validation of a valid diff file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as f:
            f.write("Stack: AWSAccelerator-TestStack-123456789012-us-east-1\n")
            f.write("Template\n")
            f.write("Resources\n")
            temp_path = Path(f.name)
        
        try:
            assert FileValidator.validate_file(temp_path) == True
        finally:
            temp_path.unlink()
    
    def test_validate_invalid_file_extension(self):
        """Test validation fails for invalid file extension"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.invalid', delete=False) as f:
            f.write("Stack: AWSAccelerator-TestStack-123456789012-us-east-1\n")
            temp_path = Path(f.name)
        
        try:
            assert FileValidator.validate_file(temp_path) == False
        finally:
            temp_path.unlink()
    
    def test_validate_nonexistent_file(self):
        """Test validation fails for non-existent file"""
        fake_path = Path("/nonexistent/file.diff")
        assert FileValidator.validate_file(fake_path) == False
    
    def test_validate_directory_with_valid_files(self):
        """Test directory validation with valid diff files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid diff files
            (temp_path / "AWSAccelerator-SecurityStack-123456789012-us-east-1.diff").write_text(
                "Stack: AWSAccelerator-SecurityStack-123456789012-us-east-1\nTemplate\nResources\n"
            )
            (temp_path / "AWSAccelerator-LoggingStack-123456789012-us-east-1.diff").write_text(
                "Stack: AWSAccelerator-LoggingStack-123456789012-us-east-1\nTemplate\nResources\n"
            )
            
            result = FileValidator.validate_directory(temp_path)
            
            assert result['is_valid'] == True
            assert result['file_count'] == 2
            assert len(result['valid_files']) == 2
            assert len(result['invalid_files']) == 0
    
    def test_validate_empty_directory(self):
        """Test directory validation with no diff files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = FileValidator.validate_directory(temp_path)
            
            assert result['file_count'] == 0
            assert len(result['warnings']) > 0
            assert "No diff files found" in result['warnings'][0]


class TestFileManager:
    """Test cases for FileManager class"""
    
    def test_save_and_load_analysis_json(self):
        """Test saving and loading analysis in JSON format"""
        # Create test analysis
        analysis = DiffAnalysis(
            total_stacks=2,
            total_resources_changed=5,
            total_iam_changes=3
        )
        analysis.stack_diffs.append(StackDiff(
            stack_name="TestStack",
            account_id="123456789012",
            region="us-east-1"
        ))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "analysis.json"
            
            # Save analysis
            success = FileManager.save_analysis(analysis, output_path, "json")
            assert success == True
            assert output_path.exists()
            
            # Load analysis
            loaded_analysis = FileManager.load_analysis(output_path)
            assert loaded_analysis is not None
            assert loaded_analysis.total_stacks == 2
            assert len(loaded_analysis.stack_diffs) == 1
    
    def test_get_diff_files(self):
        """Test getting diff files from directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "valid1.diff").write_text("Stack: AWSAccelerator-Test1\nTemplate\n")
            (temp_path / "valid2.diff").write_text("Stack: AWSAccelerator-Test2\nTemplate\n")
            (temp_path / "invalid.txt").write_text("Not a diff file")
            (temp_path / "README.md").write_text("Documentation")
            
            diff_files = FileManager.get_diff_files(temp_path)
            
            assert len(diff_files) == 2
            assert all(f.suffix == '.diff' for f in diff_files)
    
    def test_create_output_structure(self):
        """Test creation of output directory structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "output"
            
            paths = FileManager.create_output_structure(base_path)
            
            assert paths['base'] == base_path
            assert paths['analysis'].exists()
            assert paths['reports'].exists()
            assert paths['logs'].exists()
            assert paths['temp'].exists()


class TestConfigManager:
    """Test cases for ConfigManager class"""
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        config = ConfigManager.load_config()
        
        assert 'llm' in config
        assert 'analysis' in config
        assert 'output' in config
        assert config['llm']['provider'] == 'ollama'
        assert config['llm']['model'] == 'qwen2.5:7b'
    
    def test_save_and_load_config(self):
        """Test saving and loading custom configuration"""
        custom_config = {
            'llm': {
                'provider': 'openai',
                'model': 'gpt-4',
                'temperature': 0.2
            },
            'analysis': {
                'risk_threshold': 0.8
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            
            # Save config
            success = ConfigManager.save_config(custom_config, config_path)
            assert success == True
            assert config_path.exists()
            
            # Load config
            loaded_config = ConfigManager.load_config(config_path)
            assert loaded_config['llm']['provider'] == 'openai'
            assert loaded_config['llm']['model'] == 'gpt-4'
            assert loaded_config['analysis']['risk_threshold'] == 0.8
    
    def test_get_default_config_path(self):
        """Test getting default config path"""
        config_path = ConfigManager.get_default_config_path()
        
        assert config_path.name == 'config.yaml'
        assert '.lza-analyzer' in str(config_path)