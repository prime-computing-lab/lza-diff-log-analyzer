"""
Standardized error handling for LZA Diff Analyzer
"""

from typing import Optional, Any, Dict
from enum import Enum


class ErrorCategory(str, Enum):
    """Categories of errors in the system"""
    VALIDATION = "validation"
    PARSING = "parsing"
    ANALYSIS = "analysis"
    LLM = "llm"
    IO = "io"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class LZAError(Exception):
    """Base exception for all LZA Diff Analyzer errors"""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/reporting"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }


class ValidationError(LZAError):
    """Errors during input validation"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, **kwargs)
        if field:
            self.details["field"] = field


class ParseError(LZAError):
    """Errors during diff file parsing"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, line_number: Optional[int] = None, **kwargs):
        super().__init__(message, ErrorCategory.PARSING, **kwargs)
        if file_path:
            self.details["file_path"] = file_path
        if line_number:
            self.details["line_number"] = line_number


class AnalysisError(LZAError):
    """Errors during risk analysis"""
    
    def __init__(self, message: str, analyzer: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.ANALYSIS, **kwargs)
        if analyzer:
            self.details["analyzer"] = analyzer


class LLMError(LZAError):
    """Errors related to LLM operations"""
    
    def __init__(self, message: str, provider: Optional[str] = None, model: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.LLM, **kwargs)
        if provider:
            self.details["provider"] = provider
        if model:
            self.details["model"] = model


class ConfigurationError(LZAError):
    """Configuration-related errors"""
    
    def __init__(self, message: str, config_path: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.CONFIGURATION, **kwargs)
        if config_path:
            self.details["config_path"] = config_path


class ErrorHandler:
    """Centralized error handling utilities"""
    
    @staticmethod
    def handle_with_fallback(operation_name: str, primary_func, fallback_func, *args, **kwargs):
        """Execute operation with fallback on error"""
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            try:
                return fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                raise LZAError(
                    f"{operation_name} failed (both primary and fallback)",
                    details={
                        "primary_error": str(e),
                        "fallback_error": str(fallback_error)
                    },
                    cause=e
                )
    
    @staticmethod
    async def handle_async_with_fallback(operation_name: str, primary_func, fallback_func, *args, **kwargs):
        """Execute async operation with fallback on error"""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            try:
                return await fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                raise LZAError(
                    f"{operation_name} failed (both primary and fallback)",
                    details={
                        "primary_error": str(e),
                        "fallback_error": str(fallback_error)
                    },
                    cause=e
                )
    
    @staticmethod
    def safe_operation(operation_name: str, func, default_return=None, log_errors: bool = True):
        """Execute operation safely with error logging"""
        try:
            return func()
        except Exception as e:
            if log_errors:
                # In production, this would use proper logging
                print(f"Warning: {operation_name} failed: {e}")
            return default_return
    
    @staticmethod
    def validate_required(value: Any, field_name: str, error_message: Optional[str] = None):
        """Validate required field"""
        if value is None or (isinstance(value, str) and not value.strip()):
            message = error_message or f"{field_name} is required"
            raise ValidationError(message, field=field_name)
        return value
    
    @staticmethod
    def validate_path(path: Any, field_name: str = "path", must_exist: bool = True):
        """Validate file/directory path"""
        if not path:
            raise ValidationError(f"{field_name} is required", field=field_name)
        
        from pathlib import Path
        try:
            path_obj = Path(path)
            if must_exist and not path_obj.exists():
                raise ValidationError(f"{field_name} does not exist: {path}", field=field_name)
            return path_obj
        except Exception as e:
            raise ValidationError(f"Invalid {field_name}: {e}", field=field_name, cause=e)


def handle_cli_errors(func):
    """Decorator for CLI functions to handle errors gracefully"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LZAError as e:
            from rich.console import Console
            console = Console()
            
            console.print(f"[red]Error ({e.category.value}): {e.message}[/red]")
            
            if e.details:
                console.print("[yellow]Details:[/yellow]")
                for key, value in e.details.items():
                    console.print(f"  {key}: {value}")
            
            if e.cause:
                console.print(f"[dim]Caused by: {e.cause}[/dim]")
                
            return False
            
        except Exception as e:
            from rich.console import Console
            console = Console()
            
            console.print(f"[red]Unexpected error: {e}[/red]")
            console.print("[dim]Please report this issue if it persists[/dim]")
            return False
    
    return wrapper


async def handle_async_cli_errors(func):
    """Async version of CLI error handler"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except LZAError as e:
            from rich.console import Console
            console = Console()
            
            console.print(f"[red]Error ({e.category.value}): {e.message}[/red]")
            
            if e.details:
                console.print("[yellow]Details:[/yellow]")
                for key, value in e.details.items():
                    console.print(f"  {key}: {value}")
            
            if e.cause:
                console.print(f"[dim]Caused by: {e.cause}[/dim]")
                
            return False
            
        except Exception as e:
            from rich.console import Console
            console = Console()
            
            console.print(f"[red]Unexpected error: {e}[/red]")
            console.print("[dim]Please report this issue if it persists[/dim]")
            return False
    
    return wrapper