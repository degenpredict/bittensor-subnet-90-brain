#!/usr/bin/env python3
"""
Configuration loader for Bittensor Subnet 90
This module provides a simple interface for existing code to access YAML configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Backwards-compatible configuration loader that reads from YAML"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        # Try multiple possible locations for the config file
        possible_paths = [
            Path(os.getcwd()) / "subnet_config.yaml",
            Path(__file__).parent / "subnet_config.yaml",
            Path("/home/subnet90/bittensor-subnet-90-brain/subnet_config.yaml"),
            Path(os.environ.get("SUBNET_CONFIG_PATH", "")) if os.environ.get("SUBNET_CONFIG_PATH") else None
        ]
        
        config_path = None
        for path in possible_paths:
            if path and path.exists():
                config_path = path
                break
        
        if not config_path:
            # Fallback to environment variables if no YAML found
            print("Warning: No subnet_config.yaml found, falling back to environment variables")
            return self._create_env_fallback()
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            return self._create_env_fallback()
    
    def _create_env_fallback(self) -> Dict[str, Any]:
        """Create config structure from environment variables (backwards compatibility)"""
        return {
            'global': {
                'network': os.getenv('NETWORK', 'finney'),
                'subnet_uid': int(os.getenv('SUBNET_UID', '90')),
                'api_url': os.getenv('API_URL', 'https://api.degenbrain.com'),
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'log_format': os.getenv('LOG_FORMAT', 'json'),
                'log_dir': os.getenv('LOG_DIR', './logs'),
            }
        }
    
    def get_env_var(self, key: str, default: str = "") -> str:
        """
        Get environment variable with YAML config fallback
        This maintains backwards compatibility with existing code
        """
        # First check actual environment variables (highest priority)
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        
        # Then check YAML config based on current process type
        process_type = self._detect_process_type()
        
        # Map common environment variables to YAML paths
        yaml_mappings = {
            'NETWORK': ['global', 'network'],
            'SUBNET_UID': ['global', 'subnet_uid'],
            'API_URL': ['global', 'api_url'],
            'LOG_LEVEL': ['global', 'log_level'],
            'LOG_FORMAT': ['global', 'log_format'],
            'LOG_DIR': ['global', 'log_dir'],
            'WALLET_NAME': [process_type, 'wallet_name'] if process_type else None,
            'HOTKEY_NAME': [process_type, 'hotkey_name'] if process_type else None,
            'VALIDATOR_PORT': ['validator', 'port'] if process_type == 'validator' else None,
            'VALIDATOR_ID': ['validator', 'validator_id'] if process_type == 'validator' else None,
            'MINER_PORT': [process_type, 'port'] if process_type and 'miner' in process_type else None,
            'MINER_STRATEGY': [process_type, 'strategy'] if process_type and 'miner' in process_type else None,
        }
        
        if key in yaml_mappings and yaml_mappings[key]:
            yaml_path = yaml_mappings[key]
            value = self._get_nested_value(self._config, yaml_path)
            if value is not None:
                return str(value)
        
        return default
    
    def _detect_process_type(self) -> Optional[str]:
        """Detect if we're running as validator or a specific miner"""
        # Check environment variables first
        hotkey = os.getenv('HOTKEY_NAME', '')
        if hotkey == 'validator':
            return 'validator'
        elif hotkey.startswith('miner'):
            # For miners, we need to find the specific miner config
            miners = self._config.get('miners', [])
            for miner in miners:
                if miner.get('hotkey_name') == hotkey:
                    return miner['id']
        
        # Try to detect from command line or script name
        import sys
        script_name = Path(sys.argv[0]).name if sys.argv else ''
        if 'validator' in script_name:
            return 'validator'
        elif 'miner' in script_name:
            # Default to miner1 if we can't determine specific miner
            return 'miner1'
        
        return None
    
    def _get_nested_value(self, config: Dict[str, Any], path: list) -> Any:
        """Get nested value from config dict using path list"""
        current = config
        try:
            for key in path:
                if isinstance(current, list):
                    # Handle miner arrays
                    miner_id = os.getenv('MINER_ID') or os.getenv('HOTKEY_NAME', 'miner1')
                    current = next((m for m in current if m.get('id') == miner_id), current[0] if current else {})
                else:
                    current = current[key]
            return current
        except (KeyError, IndexError, TypeError):
            return None
    
    def get_process_config(self, process_type: str, process_id: str = None) -> Dict[str, str]:
        """Get complete configuration for a specific process"""
        if process_type == 'validator':
            validator = self._config.get('validator', {})
            global_config = self._config.get('global', {})
            
            config = {}
            # Add global settings
            for key, value in global_config.items():
                env_key = key.upper()
                config[env_key] = str(value)
            
            # Add validator-specific settings
            config.update({
                'WALLET_NAME': validator.get('wallet_name', ''),
                'HOTKEY_NAME': validator.get('hotkey_name', 'validator'),
                'VALIDATOR_PORT': str(validator.get('port', 8090)),
                'VALIDATOR_ID': validator.get('validator_id', ''),
                'BOOTSTRAP_MODE': str(validator.get('bootstrap_mode', True)).lower(),
                'MIN_STAKE_THRESHOLD': str(validator.get('min_stake_threshold', 1000)),
            })
            
            return config
            
        elif process_type.startswith('miner'):
            miners = self._config.get('miners', [])
            miner = next((m for m in miners if m['id'] == process_id), None)
            if not miner:
                return {}
            
            global_config = self._config.get('global', {})
            
            config = {}
            # Add global settings
            for key, value in global_config.items():
                env_key = key.upper()
                config[env_key] = str(value)
            
            # Add miner-specific settings
            config.update({
                'WALLET_NAME': miner.get('wallet_name', ''),
                'HOTKEY_NAME': miner.get('hotkey_name', ''),
                'MINER_PORT': str(miner.get('port', 8091)),
                'MINER_STRATEGY': miner.get('strategy', 'dummy'),
                'MINER_ID': miner.get('id', ''),
            })
            
            return config
        
        return {}


# Global instance for backwards compatibility
_config_loader = ConfigLoader()

def get_env(key: str, default: str = "") -> str:
    """
    Drop-in replacement for os.getenv() that reads from YAML config
    Existing code can simply replace os.getenv() calls with this function
    """
    return _config_loader.get_env_var(key, default)

def load_config_for_process(process_type: str, process_id: str = None) -> Dict[str, str]:
    """Load complete configuration for a specific process"""
    return _config_loader.get_process_config(process_type, process_id)


# Example usage for existing code:
# Instead of: api_url = os.getenv('API_URL', 'default')
# Use: api_url = get_env('API_URL', 'default')

if __name__ == '__main__':
    # Test the configuration loader
    loader = ConfigLoader()
    
    print("Testing configuration loader:")
    print(f"API_URL: {get_env('API_URL')}")
    print(f"NETWORK: {get_env('NETWORK')}")
    print(f"WALLET_NAME: {get_env('WALLET_NAME')}")
    
    print("\nValidator config:")
    validator_config = load_config_for_process('validator')
    for key, value in sorted(validator_config.items()):
        print(f"  {key}={value}")
    
    print("\nMiner1 config:")
    miner_config = load_config_for_process('miner', 'miner1')
    for key, value in sorted(miner_config.items()):
        print(f"  {key}={value}")