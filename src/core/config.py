"""
Configuration loader for YAML config files.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from ..core.logger import get_logger


class Config:
    """Configuration manager for loading YAML configs."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to main config file
        """
        self.logger = get_logger(__name__)
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        if self.config_path.exists():
            self.load()
        else:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
    
    def load(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            self.logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation key.
        
        Args:
            key: Config key (e.g., 'scraping.default_delay')
            default: Default value if key not found
            
        Returns:
            Config value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire config section.
        
        Args:
            section: Section name
            
        Returns:
            Section dict or empty dict
        """
        return self._config.get(section, {})
    
    @property
    def scraping(self) -> Dict[str, Any]:
        """Get scraping config section."""
        return self.get_section('scraping')
    
    @property
    def output(self) -> Dict[str, Any]:
        """Get output config section."""
        return self.get_section('output')
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging config section."""
        return self.get_section('logging')
    
    @property
    def targets(self) -> Dict[str, Any]:
        """Get targets config section."""
        return self.get_section('targets')
    
    @property
    def sns_patterns(self) -> Dict[str, Any]:
        """Get SNS patterns config section."""
        return self.get_section('sns_patterns')


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: str = "config/config.yaml") -> Config:
    """
    Get global config instance.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def load_sources(sources_path: str = "config/sources.yaml") -> Dict[str, Any]:
    """
    Load sources configuration.
    
    Args:
        sources_path: Path to sources file
        
    Returns:
        Sources dict
    """
    logger = get_logger(__name__)
    path = Path(sources_path)
    
    if not path.exists():
        logger.warning(f"Sources file not found: {sources_path}")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            sources = yaml.safe_load(f) or {}
        logger.info(f"Loaded sources from {sources_path}")
        return sources
    except Exception as e:
        logger.error(f"Failed to load sources: {e}")
        return {}
