"""
Configuration manager for reading and writing config.json.
Thread-safe with atomic writes to prevent corruption.
"""

import os
import json
import asyncio
from pathlib import Path
from .models import AppConfig, RoutingConfig


class ConfigManager:
    """
    Manages the config.json file with thread-safe operations.
    Config is read fresh on every request for live reload capability.
    """
    
    def __init__(self, config_path: str | None = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to config.json. Defaults to ./config.json
        """
        self.config_path = Path(config_path or os.getenv("CONFIG_PATH", "./config.json"))
        self._write_lock = asyncio.Lock()
    
    def load(self) -> AppConfig:
        """
        Load configuration from disk.
        Called on every request for live reload.
        Creates default config if file doesn't exist.
        
        Returns:
            AppConfig: Validated configuration object
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AppConfig.model_validate(data)
        except FileNotFoundError:
            # Create default config if file doesn't exist
            default_config = self.get_default_config()
            self.save(default_config)
            return default_config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    async def save(self, config: AppConfig) -> None:
        """
        Save configuration to disk atomically.
        Uses temp file + rename to prevent corruption on concurrent writes.
        
        Args:
            config: Configuration to save
        """
        async with self._write_lock:
            # Increment version on save
            config.version += 1
            
            # Serialize to JSON
            config_dict = config.model_dump(mode='json')
            json_str = json.dumps(config_dict, indent=2, ensure_ascii=False)
            
            # Write to temp file first
            temp_path = self.config_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            # Atomic rename
            os.replace(temp_path, self.config_path)
    
    def save_sync(self, config: AppConfig) -> None:
        """
        Synchronous version of save for initialization.
        
        Args:
            config: Configuration to save
        """
        # Increment version on save
        config.version += 1
        
        # Serialize to JSON
        config_dict = config.model_dump(mode='json')
        json_str = json.dumps(config_dict, indent=2, ensure_ascii=False)
        
        # Write to temp file first
        temp_path = self.config_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        os.replace(temp_path, self.config_path)
    
    @staticmethod
    def get_default_config() -> AppConfig:
        """
        Create a default configuration with no providers.
        
        Returns:
            AppConfig: Default configuration object
        """
        return AppConfig(
            providers=[],
            routing=RoutingConfig(mode="smart", sandbox=False),
            version=0
        )


# Global instance
config_manager = ConfigManager()
