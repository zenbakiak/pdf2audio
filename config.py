#!/usr/bin/env python3

import yaml
import os
from typing import Dict, Any, Optional


class Config:
    """Singleton configuration manager for PDF to Audio converter."""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls, config_path: str = "config.yml") -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from YAML file or use default config file."""
        try:
            with open(config_path, 'r') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            self._config = self._load_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from default_config.yml file."""
        default_config_path = os.path.join(os.path.dirname(__file__), 'default_config.yml')
        
        try:
            with open(default_config_path, 'r') as file:
                config = yaml.safe_load(file)
                if config is None:
                    raise ValueError("Default config file is empty or invalid")
                return config
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Default configuration file not found at {default_config_path}. "
                "Please ensure default_config.yml exists in the same directory as config.py"
            )
        except Exception as e:
            raise RuntimeError(f"Error loading default configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'tts.provider')."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def tts_provider(self) -> str:
        """Get TTS provider."""
        return self.get('tts.provider', 'gtts')
    
    @property
    def llm_provider(self) -> str:
        """Get LLM provider."""
        return self.get('llm.provider', 'openai')
    
    @property
    def speaking_rate(self) -> float:
        """Get speaking rate."""
        return self.get('tts.speaking_rate', 1.0)
    
    @property
    def default_language(self) -> str:
        """Get default language."""
        return self.get('tts.default_language', 'en')
    
    @property
    def cleaning_prompt(self) -> str:
        """Get cleaning prompt."""
        return self.get('llm.cleaning_prompt', 'Please clean this PDF text for text-to-speech conversion:')
    
    @property
    def verbose(self) -> bool:
        """Get verbose setting."""
        return self.get('output.verbose', True)
    
    def get_tts_config(self, provider: str) -> Dict[str, Any]:
        """Get TTS configuration for specific provider."""
        return self.get(f'tts.voice.{provider}', {})
    
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get LLM configuration for specific provider."""
        return self.get(f'llm.api.{provider}', {})
    
    def get_language_mapping(self, lang_code: str) -> str:
        """Get mapped language code."""
        mappings = self.get('tts.language_mappings', {})
        return mappings.get(lang_code, lang_code)
    
    def should_save_raw_text(self) -> bool:
        """Check if raw text should be saved."""
        return self.get('output.save_raw_text', False)
    
    def should_save_cleaned_text(self) -> bool:
        """Check if cleaned text should be saved."""
        return self.get('output.save_cleaned_text', False)