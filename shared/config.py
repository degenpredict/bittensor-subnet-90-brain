"""
Configuration management for the DegenBrain subnet.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import structlog
from shared.types import SubnetConfig


logger = structlog.get_logger()


class ConfigManager:
    """
    Manages configuration loading and validation.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_file: Path to .env file. If None, searches for .env in project root.
        """
        self.env_file = env_file or self._find_env_file()
        self._env_dict: Dict[str, str] = {}
        self._config: Optional[SubnetConfig] = None
        
    def _find_env_file(self) -> str:
        """Find .env file in project root or current directory."""
        # Try current directory first
        if Path(".env").exists():
            return ".env"
        
        # Try parent directories up to 3 levels
        current = Path.cwd()
        for _ in range(3):
            env_path = current / ".env"
            if env_path.exists():
                return str(env_path)
            current = current.parent
            
        # Default to current directory
        return ".env"
    
    def load(self) -> SubnetConfig:
        """
        Load configuration from environment.
        
        Returns:
            SubnetConfig object with all settings.
        """
        if self._config:
            return self._config
            
        # Load from .env file if it exists
        if Path(self.env_file).exists():
            load_dotenv(self.env_file)
            logger.info("Loaded configuration from file", env_file=self.env_file)
        else:
            logger.warning("No .env file found, using environment variables only")
        
        # Build environment dictionary
        self._env_dict = {
            key: value
            for key, value in os.environ.items()
            if self._is_relevant_env_var(key) and value
        }
        
        # Validate required fields before creating config
        self._validate_required_fields()
        
        # Create and validate config
        try:
            self._config = SubnetConfig.from_env(self._env_dict)
            self._validate_config()
            logger.info("Configuration loaded successfully", 
                       network=self._config.network,
                       subnet_uid=self._config.subnet_uid)
            return self._config
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            raise
    
    def _validate_required_fields(self) -> None:
        """Validate that required fields are present in environment."""
        if "WALLET_NAME" not in self._env_dict:
            raise ValueError("WALLET_NAME is required")
        if "HOTKEY_NAME" not in self._env_dict:
            raise ValueError("HOTKEY_NAME is required")
        if "API_URL" not in self._env_dict:
            raise ValueError("API_URL is required")
    
    def _is_relevant_env_var(self, key: str) -> bool:
        """Check if environment variable is relevant to our config."""
        relevant_prefixes = [
            "WALLET_", "HOTKEY_", "NETWORK", "SUBNET_", "API_",
            "VALIDATOR_", "MINER_", "LOG_", "WANDB_",
            "MAX_", "REQUEST_", "RESPONSE_", "CACHE_",
            "OPENAI_", "ANTHROPIC_", "COINGECKO_", "ALPHAAVANTAGE_",
            "CONSENSUS_", "MIN_", "QUERY_", "VERIFICATION_"
        ]
        # Also include anything with PASSWORD, KEY, or SECRET for save_example test
        sensitive_keywords = ["PASSWORD", "KEY", "SECRET"]
        return (any(key.startswith(prefix) for prefix in relevant_prefixes) or 
                any(keyword in key.upper() for keyword in sensitive_keywords))
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        if not self._config:
            raise ValueError("No configuration loaded")
            
        # Validate network
        valid_networks = ["finney", "test", "local"]
        if self._config.network not in valid_networks:
            raise ValueError(f"NETWORK must be one of {valid_networks}")
            
        # Validate numeric ranges
        if self._config.consensus_threshold < 0 or self._config.consensus_threshold > 1:
            raise ValueError("CONSENSUS_THRESHOLD must be between 0 and 1")
        if self._config.min_miners_required < 1:
            raise ValueError("MIN_MINERS_REQUIRED must be at least 1")
        if self._config.query_timeout < 1:
            raise ValueError("QUERY_TIMEOUT must be at least 1 second")
            
        logger.info("Configuration validation passed")
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """
        Get available API keys for miners.
        
        Returns:
            Dictionary of API service names to keys.
        """
        return {
            "openai": os.environ.get("OPENAI_API_KEY"),
            "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
            "coingecko": os.environ.get("COINGECKO_API_KEY"),
            "alphaavantage": os.environ.get("ALPHAAVANTAGE_API_KEY"),
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Dictionary with logging settings.
        """
        return {
            "level": os.environ.get("LOG_LEVEL", "INFO"),
            "format": os.environ.get("LOG_FORMAT", "json"),
            "file": os.environ.get("LOG_FILE", None),
        }
    
    def get_wandb_config(self) -> Dict[str, Optional[str]]:
        """
        Get Weights & Biases configuration.
        
        Returns:
            Dictionary with W&B settings.
        """
        return {
            "api_key": os.environ.get("WANDB_API_KEY"),
            "project": os.environ.get("WANDB_PROJECT", "degenbrain-subnet"),
            "entity": os.environ.get("WANDB_ENTITY"),
        }
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self._config.network == "finney" if self._config else False
    
    def is_test_mode(self) -> bool:
        """Check if running in test mode."""
        return os.environ.get("TEST_MODE", "").lower() == "true"
    
    def save_example(self, path: str = ".env.example") -> None:
        """
        Save current configuration as an example file.
        
        Args:
            path: Path to save the example file.
        """
        example_content = []
        
        # Add all current environment variables as examples
        for key, value in sorted(self._env_dict.items()):
            if any(secret in key.upper() for secret in ["KEY", "SECRET", "PASSWORD"]):
                # Mask sensitive values
                example_content.append(f"# {key}=your_{key.lower()}_here")
            else:
                example_content.append(f"{key}={value}")
        
        with open(path, "w") as f:
            f.write("\n".join(example_content))
        
        logger.info("Saved configuration example", path=path)


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> SubnetConfig:
    """
    Get the global configuration.
    
    Returns:
        SubnetConfig object.
    """
    global _config_manager
    if not _config_manager:
        _config_manager = ConfigManager()
    return _config_manager.load()


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager.
    
    Returns:
        ConfigManager instance.
    """
    global _config_manager
    if not _config_manager:
        _config_manager = ConfigManager()
    return _config_manager


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config_manager
    _config_manager = None