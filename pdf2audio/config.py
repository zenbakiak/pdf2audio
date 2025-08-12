#!/usr/bin/env python3

import yaml
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Singleton configuration manager for PDF to Audio converter."""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls, config_path: Optional[str] = None) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.user_config_dir = Path.home() / ".pdf2audio"
            cls._instance._setup_user_directory()
            cls._instance._load_config(config_path)
        return cls._instance
    
    def _setup_user_directory(self) -> None:
        """Setup user configuration directory if it doesn't exist."""
        if not self.user_config_dir.exists():
            print(f"Creating PDF2Audio configuration directory: {self.user_config_dir}")
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy default configuration files
            self._copy_default_files()
    
    def _copy_default_files(self) -> None:
        """Copy default configuration files to user directory."""
        package_dir = Path(__file__).parent
        data_dir = package_dir / "data"
        
        # Copy default config if it doesn't exist
        user_config = self.user_config_dir / "config.yml"
        if not user_config.exists():
            default_config = data_dir / "default_config.yml"
            if default_config.exists():
                shutil.copy2(default_config, user_config)
                print(f"Created default config: {user_config}")
        
        # Copy .env.example if it doesn't exist
        user_env = self.user_config_dir / ".env"
        user_env_example = self.user_config_dir / ".env.example"
        if not user_env_example.exists():
            env_example = data_dir / ".env.example"
            if env_example.exists():
                shutil.copy2(env_example, user_env_example)
                print(f"Created environment template: {user_env_example}")
                
                # Also create .env if it doesn't exist
                if not user_env.exists():
                    shutil.copy2(env_example, user_env)
                    print(f"Created environment file: {user_env}")
                    print("Please edit ~/.pdf2audio/.env with your API keys")
    
    def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from YAML file or use default config file."""
        # Determine config path
        if config_path is None:
            config_path = str(self.user_config_dir / "config.yml")
        
        try:
            with open(config_path, 'r') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}.")
            print("Using default configuration. To customize, create a config.yml file.")
            self._config = self._load_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from default_config.yml file."""
        # Try user directory first, then package data directory
        user_default = self.user_config_dir / "config.yml"
        package_default = Path(__file__).parent / "data" / "default_config.yml"
        
        default_config_path = str(user_default if user_default.exists() else package_default)
        
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
    def ssml_prompt(self) -> str:
        """Get SSML prompt."""
        return self.get('llm.ssml_prompt', 'Add SSML tags to this text:')
    
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
    
    # Deprecated legacy flags for saving artifacts were removed; artifacts are always saved.
