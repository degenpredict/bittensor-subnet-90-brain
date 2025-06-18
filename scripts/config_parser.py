#!/usr/bin/env python3
"""
Configuration parser for Bittensor Subnet 90
Reads YAML configuration and provides utilities for process management
"""

import yaml
import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class SubnetConfig:
    """Handles parsing and access to subnet configuration"""
    
    def __init__(self, config_path: str = "subnet_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse YAML configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_global_env(self) -> Dict[str, str]:
        """Get global environment variables"""
        global_config = self.config.get('global', {})
        return {
            'NETWORK': global_config.get('network', 'finney'),
            'SUBNET_UID': str(global_config.get('subnet_uid', 90)),
            'API_URL': global_config.get('api_url', 'https://api.degenbrain.com'),
            'LOG_LEVEL': global_config.get('log_level', 'INFO'),
            'LOG_FORMAT': global_config.get('log_format', 'json'),
            'LOG_DIR': global_config.get('log_dir', './logs'),
            'MAX_WORKERS': str(global_config.get('max_workers', 4)),
            'REQUEST_TIMEOUT': str(global_config.get('request_timeout', 30)),
        }
    
    def get_validator_env(self) -> Optional[Dict[str, str]]:
        """Get validator-specific environment variables"""
        validator = self.config.get('validator', {})
        if not validator.get('enabled', False):
            return None
            
        env = self.get_global_env()
        env.update({
            'WALLET_NAME': validator['wallet_name'],
            'HOTKEY_NAME': validator['hotkey_name'],
            'VALIDATOR_PORT': str(validator.get('port', 8090)),
            'VALIDATOR_ID': validator.get('validator_id', ''),
            'BOOTSTRAP_MODE': str(validator.get('bootstrap_mode', True)).lower(),
            'MIN_STAKE_THRESHOLD': str(validator.get('min_stake_threshold', 1000)),
        })
        return env
    
    def get_miner_env(self, miner_id: str) -> Optional[Dict[str, str]]:
        """Get miner-specific environment variables"""
        miners = self.config.get('miners', [])
        miner = next((m for m in miners if m['id'] == miner_id), None)
        
        if not miner or not miner.get('enabled', False):
            return None
            
        env = self.get_global_env()
        env.update({
            'WALLET_NAME': miner['wallet_name'],
            'HOTKEY_NAME': miner['hotkey_name'],
            'MINER_PORT': str(miner.get('port', 8091)),
            'MINER_STRATEGY': miner.get('strategy', 'dummy'),
            'MINER_ID': miner['id'],
        })
        
        # Add strategy-specific configuration
        if 'model_config' in miner:
            env['MODEL_CONFIG'] = json.dumps(miner['model_config'])
        if 'strategy_weights' in miner:
            env['STRATEGY_WEIGHTS'] = json.dumps(miner['strategy_weights'])
            
        return env
    
    def get_enabled_miners(self) -> List[Dict[str, Any]]:
        """Get list of enabled miners"""
        miners = self.config.get('miners', [])
        return [m for m in miners if m.get('enabled', False)]
    
    def get_pm2_config(self) -> Dict[str, Any]:
        """Get PM2-specific configuration"""
        return self.config.get('pm2', {})
    
    def generate_pm2_ecosystem(self) -> Dict[str, Any]:
        """Generate PM2 ecosystem configuration"""
        apps = []
        pm2_config = self.get_pm2_config()
        global_config = self.config.get('global', {})
        
        # Add validator if enabled
        validator = self.config.get('validator', {})
        if validator.get('enabled', False):
            apps.append({
                'name': 'validator',
                'script': 'run_validator.py',
                'interpreter': f"{validator['venv_path']}/bin/python3",
                'cwd': '/home/subnet90/bittensor-subnet-90-brain',
                'env': self.get_validator_env(),
                'error_file': f"{global_config.get('log_dir', './logs')}/validator.error.log",
                'out_file': f"{global_config.get('log_dir', './logs')}/validator.log",
                'log_date_format': 'YYYY-MM-DD HH:mm:ss',
                'max_restarts': validator.get('max_restarts', global_config.get('max_restarts', 10)),
                'min_uptime': global_config.get('min_uptime', '10s'),
                'restart_delay': global_config.get('restart_delay', 4000),
                'autorestart': True,
                'watch': False,
            })
        
        # Add enabled miners
        for miner in self.get_enabled_miners():
            miner_env = self.get_miner_env(miner['id'])
            if miner_env:
                apps.append({
                    'name': miner['id'],
                    'script': 'run_miner.py',
                    'interpreter': f"{miner['venv_path']}/bin/python3",
                    'cwd': '/home/subnet90/bittensor-subnet-90-brain',
                    'env': miner_env,
                    'error_file': f"{global_config.get('log_dir', './logs')}/{miner['id']}.error.log",
                    'out_file': f"{global_config.get('log_dir', './logs')}/{miner['id']}.log",
                    'log_date_format': 'YYYY-MM-DD HH:mm:ss',
                    'max_restarts': miner.get('max_restarts', global_config.get('max_restarts', 10)),
                    'min_uptime': global_config.get('min_uptime', '10s'),
                    'restart_delay': global_config.get('restart_delay', 4000),
                    'autorestart': True,
                    'watch': False,
                })
        
        return {'apps': apps}
    
    def write_pm2_ecosystem(self, output_path: str = "ecosystem.config.js"):
        """Write PM2 ecosystem configuration to file"""
        ecosystem = self.generate_pm2_ecosystem()
        
        # Convert Python dict to JavaScript module.exports
        js_content = "module.exports = " + json.dumps(ecosystem, indent=2)
        
        with open(output_path, 'w') as f:
            f.write(js_content)
        
        print(f"PM2 ecosystem config written to {output_path}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required fields
        if 'global' not in self.config:
            issues.append("Missing 'global' section")
            
        # Check validator
        validator = self.config.get('validator', {})
        if validator.get('enabled', False):
            if 'wallet_name' not in validator:
                issues.append("Validator missing 'wallet_name'")
            if 'hotkey_name' not in validator:
                issues.append("Validator missing 'hotkey_name'")
        
        # Check miners
        miners = self.config.get('miners', [])
        used_ports = set()
        used_hotkeys = set()
        
        for miner in miners:
            if not miner.get('enabled', False):
                continue
                
            if 'id' not in miner:
                issues.append("Miner missing 'id'")
            if 'wallet_name' not in miner:
                issues.append(f"Miner {miner.get('id', 'unknown')} missing 'wallet_name'")
            if 'hotkey_name' not in miner:
                issues.append(f"Miner {miner.get('id', 'unknown')} missing 'hotkey_name'")
            
            # Check for port conflicts
            port = miner.get('port')
            if port in used_ports:
                issues.append(f"Port {port} used by multiple miners")
            used_ports.add(port)
            
            # Check for hotkey conflicts (within same wallet)
            wallet_hotkey = (miner.get('wallet_name'), miner.get('hotkey_name'))
            if wallet_hotkey in used_hotkeys:
                issues.append(f"Hotkey {wallet_hotkey[1]} already used with wallet {wallet_hotkey[0]}")
            used_hotkeys.add(wallet_hotkey)
        
        return issues


def main():
    """CLI for configuration management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Subnet configuration manager')
    parser.add_argument('--config', default='subnet_config.yaml', help='Path to configuration file')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--generate-pm2', action='store_true', help='Generate PM2 ecosystem config')
    parser.add_argument('--show-env', help='Show environment for specific process (validator, miner1, etc.)')
    
    args = parser.parse_args()
    
    try:
        config = SubnetConfig(args.config)
        
        if args.validate:
            issues = config.validate_config()
            if issues:
                print("Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("Configuration is valid!")
        
        elif args.generate_pm2:
            config.write_pm2_ecosystem()
            
        elif args.show_env:
            if args.show_env == 'validator':
                env = config.get_validator_env()
            else:
                env = config.get_miner_env(args.show_env)
            
            if env:
                print(f"Environment for {args.show_env}:")
                for key, value in sorted(env.items()):
                    print(f"  {key}={value}")
            else:
                print(f"Process {args.show_env} not found or not enabled")
        
        else:
            # Show summary
            validator = config.config.get('validator', {})
            miners = config.get_enabled_miners()
            
            print("Subnet Configuration Summary:")
            print(f"  Network: {config.config['global']['network']}")
            print(f"  Subnet UID: {config.config['global']['subnet_uid']}")
            print(f"  API URL: {config.config['global']['api_url']}")
            print(f"  Validator: {'Enabled' if validator.get('enabled') else 'Disabled'}")
            print(f"  Active Miners: {len(miners)}")
            for miner in miners:
                print(f"    - {miner['id']}: {miner['wallet_name']}/{miner['hotkey_name']} (strategy: {miner.get('strategy', 'unknown')})")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())