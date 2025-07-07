"""
Base LLM abstraction interface for multi-provider support
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncIterator
from pydantic import BaseModel
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMMessage(BaseModel):
    """Standardized message format for LLM interactions"""
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class LLMResponse(BaseModel):
    """Standardized response format from LLM"""
    content: str
    provider: LLMProvider
    model: str
    token_usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 30
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """Base exception for LLM-related errors"""
    def __init__(self, message: str, provider: LLMProvider, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider_name = config.provider
    
    @abstractmethod
    async def generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def stream_generate(self, messages: List[LLMMessage]) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        pass
    
    def format_system_prompt(self, task_description: str) -> str:
        """Format a system prompt for the specific task"""
        return f"""You are an expert AWS infrastructure analyst specializing in Landing Zone Accelerator (LZA) risk assessment.

Your task: {task_description}

Guidelines:
- Analyze CloudFormation changes for potential business impact
- Focus on enterprise risks: security, connectivity, operations, compliance
- Provide clear risk levels: LOW, MEDIUM, HIGH, CRITICAL
- Explain potential workload impacts
- Suggest mitigation strategies
- Be concise but thorough in your analysis

Respond in structured format with clear risk assessments."""


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create_provider(config: LLMConfig) -> BaseLLMProvider:
        """Create an LLM provider based on configuration"""
        if config.provider == LLMProvider.OLLAMA:
            from .ollama_client import OllamaClient
            return OllamaClient(config)
        elif config.provider == LLMProvider.OPENAI:
            from .openai_client import OpenAIClient
            return OpenAIClient(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            from .anthropic_client import AnthropicClient
            return AnthropicClient(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    @staticmethod
    def get_default_config(provider: LLMProvider) -> LLMConfig:
        """Get default configuration for a provider"""
        defaults = {
            LLMProvider.OLLAMA: {
                "model": "qwen2.5:7b",
                "base_url": "http://localhost:11434",
                "temperature": 0.1,
                "max_tokens": 4096
            },
            LLMProvider.OPENAI: {
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 4096
            },
            LLMProvider.ANTHROPIC: {
                "model": "claude-3-haiku-20240307",
                "temperature": 0.1,
                "max_tokens": 4096
            }
        }
        
        return LLMConfig(
            provider=provider,
            **defaults[provider]
        )