"""
Configuration system for LLM settings
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from .base import LLMConfig, LLMProvider, BaseLLMProvider


class LLMProviderConfig(BaseModel):
    """Configuration for a specific LLM provider"""
    model_config = {"arbitrary_types_allowed": True}
    
    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = 4096
    timeout: int = 30
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None
    enabled: bool = True


class LLMConfigManager(BaseModel):
    """Manager for LLM configurations"""
    model_config = {"arbitrary_types_allowed": True}
    
    default_provider: LLMProvider = LLMProvider.OLLAMA
    providers: Dict[LLMProvider, LLMProviderConfig] = Field(default_factory=dict)
    fallback_chain: List[LLMProvider] = Field(default_factory=list)
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __init__(self, **data):
        super().__init__(**data)
        self._ensure_default_providers()
    
    def _ensure_default_providers(self):
        """Ensure default provider configurations exist"""
        default_configs = {
            LLMProvider.OLLAMA: LLMProviderConfig(
                provider=LLMProvider.OLLAMA,
                model="qwen2.5:7b",
                base_url="http://localhost:11434",
                temperature=0.1,
                max_tokens=4096,
                timeout=120
            ),
            LLMProvider.OPENAI: LLMProviderConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=4096,
                timeout=30,
                api_key=os.getenv("OPENAI_API_KEY"),
                enabled=bool(os.getenv("OPENAI_API_KEY"))
            ),
            LLMProvider.ANTHROPIC: LLMProviderConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-3-haiku-20240307",
                temperature=0.1,
                max_tokens=4096,
                timeout=30,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                enabled=bool(os.getenv("ANTHROPIC_API_KEY"))
            )
        }
        
        for provider, config in default_configs.items():
            if provider not in self.providers:
                self.providers[provider] = config
        
        # Set default fallback chain if not provided
        if not self.fallback_chain:
            self.fallback_chain = [
                LLMProvider.OLLAMA,
                LLMProvider.OPENAI,
                LLMProvider.ANTHROPIC
            ]
    
    def get_provider_config(self, provider: LLMProvider) -> LLMProviderConfig:
        """Get configuration for a specific provider"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not configured")
        return self.providers[provider]
    
    def get_llm_config(self, provider: LLMProvider) -> LLMConfig:
        """Convert provider config to LLM config"""
        provider_config = self.get_provider_config(provider)
        return LLMConfig(
            provider=provider_config.provider,
            model=provider_config.model,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens,
            timeout=provider_config.timeout,
            api_key=provider_config.api_key,
            base_url=provider_config.base_url,
            additional_params=provider_config.additional_params
        )
    
    def get_default_config(self) -> LLMConfig:
        """Get configuration for the default provider"""
        return self.get_llm_config(self.default_provider)
    
    def get_enabled_providers(self) -> List[LLMProvider]:
        """Get list of enabled providers"""
        return [
            provider for provider, config in self.providers.items()
            if config.enabled
        ]
    
    def get_fallback_configs(self) -> List[LLMConfig]:
        """Get configurations for fallback chain"""
        enabled_providers = set(self.get_enabled_providers())
        return [
            self.get_llm_config(provider)
            for provider in self.fallback_chain
            if provider in enabled_providers
        ]
    
    def update_provider_config(self, provider: LLMProvider, **kwargs):
        """Update configuration for a provider"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not configured")
        
        config_dict = self.providers[provider].dict()
        config_dict.update(kwargs)
        self.providers[provider] = LLMProviderConfig(**config_dict)
    
    def set_api_key(self, provider: LLMProvider, api_key: str):
        """Set API key for a provider"""
        self.update_provider_config(provider, api_key=api_key, enabled=True)
    
    def disable_provider(self, provider: LLMProvider):
        """Disable a provider"""
        self.update_provider_config(provider, enabled=False)
    
    def enable_provider(self, provider: LLMProvider):
        """Enable a provider"""
        self.update_provider_config(provider, enabled=True)


class ConfigLoader:
    """Utility class for loading configuration from files"""
    
    @staticmethod
    def load_from_file(config_path: Path) -> LLMConfigManager:
        """Load configuration from YAML file"""
        if not config_path.exists():
            return LLMConfigManager()
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return LLMConfigManager()
            
            return LLMConfigManager(**data)
        
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    @staticmethod
    def save_to_file(config: LLMConfigManager, config_path: Path):
        """Save configuration to YAML file"""
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.safe_dump(
                    config.dict(exclude_none=True),
                    f,
                    default_flow_style=False,
                    indent=2
                )
        
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {config_path}: {e}")
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get default configuration file path"""
        # Check for environment variable first
        if config_path := os.getenv("LZA_CONFIG_PATH"):
            return Path(config_path)
        
        # Check for project config directory
        project_root = Path(__file__).parent.parent.parent
        config_dir = project_root / "config"
        if config_dir.exists():
            return config_dir / "llm_config.yaml"
        
        # Fallback to user home directory
        home_config = Path.home() / ".config" / "lza-analyzer" / "config.yaml"
        return home_config
    
    @staticmethod
    def load_default_config() -> LLMConfigManager:
        """Load configuration from default location"""
        config_path = ConfigLoader.get_default_config_path()
        return ConfigLoader.load_from_file(config_path)
    
    @staticmethod
    def create_default_config_file():
        """Create a default configuration file"""
        config_path = ConfigLoader.get_default_config_path()
        
        if config_path.exists():
            return  # Don't overwrite existing config
        
        default_config = LLMConfigManager()
        ConfigLoader.save_to_file(default_config, config_path)
        
        print(f"Created default configuration at: {config_path}")
        print("Edit this file to customize your LLM provider settings.")


# Environment variable helpers
def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    env_config = {}
    
    # Default provider
    if default_provider := os.getenv("LZA_DEFAULT_PROVIDER"):
        try:
            env_config["default_provider"] = LLMProvider(default_provider.lower())
        except ValueError:
            pass
    
    # Ollama settings
    if ollama_url := os.getenv("OLLAMA_BASE_URL"):
        env_config.setdefault("providers", {})
        env_config["providers"].setdefault("ollama", {})
        env_config["providers"]["ollama"]["base_url"] = ollama_url
    
    if ollama_model := os.getenv("OLLAMA_MODEL"):
        env_config.setdefault("providers", {})
        env_config["providers"].setdefault("ollama", {})
        env_config["providers"]["ollama"]["model"] = ollama_model
    
    # OpenAI settings
    if openai_key := os.getenv("OPENAI_API_KEY"):
        env_config.setdefault("providers", {})
        env_config["providers"].setdefault("openai", {})
        env_config["providers"]["openai"]["api_key"] = openai_key
        env_config["providers"]["openai"]["enabled"] = True
    
    if openai_model := os.getenv("OPENAI_MODEL"):
        env_config.setdefault("providers", {})
        env_config["providers"].setdefault("openai", {})
        env_config["providers"]["openai"]["model"] = openai_model
    
    # Anthropic settings
    if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
        env_config.setdefault("providers", {})
        env_config["providers"].setdefault("anthropic", {})
        env_config["providers"]["anthropic"]["api_key"] = anthropic_key
        env_config["providers"]["anthropic"]["enabled"] = True
    
    if anthropic_model := os.getenv("ANTHROPIC_MODEL"):
        env_config.setdefault("providers", {})
        env_config["providers"].setdefault("anthropic", {})
        env_config["providers"]["anthropic"]["model"] = anthropic_model
    
    return env_config