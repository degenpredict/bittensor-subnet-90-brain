"""
Unit tests for configuration management.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from shared.config import ConfigManager, get_config, reset_config
from shared.types import SubnetConfig


class TestConfigManager:
    """Test ConfigManager class."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_env_loading(self):
        """Test loading configuration from environment."""
        # Set environment variables
        env_vars = {
            "WALLET_NAME": "test_wallet",
            "HOTKEY_NAME": "test_hotkey",
            "NETWORK": "test",
            "SUBNET_UID": "90",
            "API_URL": "https://test.api.com",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            config = manager.load()
            
            assert config.wallet_name == "test_wallet"
            assert config.hotkey_name == "test_hotkey"
            assert config.network == "test"
            assert config.api_url == "https://test.api.com"
    
    def test_env_file_loading(self):
        """Test loading from .env file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("WALLET_NAME=file_wallet\n")
            f.write("HOTKEY_NAME=file_hotkey\n")
            f.write("NETWORK=local\n")
            f.write("API_URL=https://file.api.com\n")
            f.write("CONSENSUS_THRESHOLD=0.75\n")
            env_file = f.name
        
        try:
            manager = ConfigManager(env_file=env_file)
            config = manager.load()
            
            assert config.wallet_name == "file_wallet"
            assert config.hotkey_name == "file_hotkey"
            assert config.network == "local"
            assert config.consensus_threshold == 0.75
        finally:
            os.unlink(env_file)
    
    def test_missing_env_handling(self):
        """Test handling of missing environment variables."""
        # Only provide minimum required
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            config = manager.load()
            
            # Should use defaults
            assert config.network == "finney"  # Default
            assert config.subnet_uid == 90  # Default
            assert config.validator_port == 8090  # Default
    
    def test_config_validation_errors(self):
        """Test configuration validation catches errors."""
        # Missing required field
        with patch.dict(os.environ, {"HOTKEY_NAME": "test"}, clear=True):
            manager = ConfigManager()
            with pytest.raises(ValueError, match="WALLET_NAME is required"):
                manager.load()
        
        # Invalid network
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "NETWORK": "invalid_network"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            with pytest.raises(ValueError, match="NETWORK must be one of"):
                manager.load()
        
        # Invalid consensus threshold
        env_vars["NETWORK"] = "test"
        env_vars["CONSENSUS_THRESHOLD"] = "1.5"  # > 1
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            with pytest.raises(ValueError, match="CONSENSUS_THRESHOLD must be between"):
                manager.load()
    
    def test_get_api_keys(self):
        """Test retrieving API keys."""
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "OPENAI_API_KEY": "sk-test123",
            "ANTHROPIC_API_KEY": "ant-test456"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()  # Load config first
            
            api_keys = manager.get_api_keys()
            assert api_keys["openai"] == "sk-test123"
            assert api_keys["anthropic"] == "ant-test456"
            assert api_keys["coingecko"] is None
    
    def test_get_logging_config(self):
        """Test retrieving logging configuration."""
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
            "LOG_FILE": "/var/log/subnet.log"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()
            
            log_config = manager.get_logging_config()
            assert log_config["level"] == "DEBUG"
            assert log_config["format"] == "text"
            assert log_config["file"] == "/var/log/subnet.log"
    
    def test_get_wandb_config(self):
        """Test retrieving W&B configuration."""
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "WANDB_API_KEY": "wandb-key-123",
            "WANDB_PROJECT": "my-project",
            "WANDB_ENTITY": "my-team"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()
            
            wandb_config = manager.get_wandb_config()
            assert wandb_config["api_key"] == "wandb-key-123"
            assert wandb_config["project"] == "my-project"
            assert wandb_config["entity"] == "my-team"
    
    def test_is_production(self):
        """Test production mode detection."""
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "NETWORK": "finney"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()
            assert manager.is_production()
        
        # Change to test network
        env_vars["NETWORK"] = "test"
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()
            assert not manager.is_production()
    
    def test_is_test_mode(self):
        """Test test mode detection."""
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "TEST_MODE": "true"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()
            assert manager.is_test_mode()
        
        # Without TEST_MODE
        del env_vars["TEST_MODE"]
        with patch.dict(os.environ, env_vars, clear=True):
            manager = ConfigManager()
            manager.load()
            assert not manager.is_test_mode()
    
    def test_save_example(self):
        """Test saving configuration example."""
        env_vars = {
            "WALLET_NAME": "wallet",
            "HOTKEY_NAME": "hotkey",
            "API_URL": "https://api.com",
            "OPENAI_API_KEY": "sk-secret",
            "SOME_PASSWORD": "password123"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            example_path = Path(tmpdir) / ".env.example"
            
            with patch.dict(os.environ, env_vars, clear=True):
                manager = ConfigManager()
                manager.load()
                manager.save_example(str(example_path))
            
            assert example_path.exists()
            content = example_path.read_text()
            
            # Should mask sensitive values
            assert "# OPENAI_API_KEY=your_openai_api_key_here" in content
            assert "# SOME_PASSWORD=your_some_password_here" in content
            # Should include non-sensitive values
            assert "API_URL=https://api.com" in content


class TestGlobalConfig:
    """Test global configuration functions."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_get_config(self):
        """Test getting global config."""
        env_vars = {
            "WALLET_NAME": "global_wallet",
            "HOTKEY_NAME": "global_hotkey",
            "API_URL": "https://global.api.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_config()
            assert config.wallet_name == "global_wallet"
            
            # Should return same instance
            config2 = get_config()
            assert config is config2
    
    def test_reset_config(self):
        """Test resetting global config."""
        env_vars = {
            "WALLET_NAME": "wallet1",
            "HOTKEY_NAME": "hotkey1",
            "API_URL": "https://api1.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config1 = get_config()
            assert config1.wallet_name == "wallet1"
        
        reset_config()
        
        # Change environment
        env_vars["WALLET_NAME"] = "wallet2"
        with patch.dict(os.environ, env_vars, clear=True):
            config2 = get_config()
            assert config2.wallet_name == "wallet2"
            assert config1 is not config2