#!/usr/bin/env python3
"""
Production deployment script for Subnet 90 validator.

This script sets up and runs the validator on the live Bittensor network.
"""
import os
import sys
import asyncio
import argparse
import subprocess
from pathlib import Path
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def check_requirements():
    """Check if all requirements are met for deployment."""
    logger.info("Checking deployment requirements...")
    
    errors = []
    
    # Check Python version
    if sys.version_info < (3, 11):
        errors.append(f"Python 3.11+ required, got {sys.version_info}")
    
    # Check if wallet environment variables are set
    required_env_vars = [
        "WALLET_NAME",
        "HOTKEY_NAME", 
        "API_URL"
    ]
    
    for var in required_env_vars:
        if not os.getenv(var):
            errors.append(f"Environment variable {var} not set")
    
    # Check if bittensor is installed
    try:
        import bittensor as bt
        logger.info("Bittensor installed", version=bt.__version__)
    except ImportError:
        errors.append("Bittensor not installed. Run: pip install bittensor")
    
    # Check if wallet exists
    wallet_name = os.getenv("WALLET_NAME")
    hotkey_name = os.getenv("HOTKEY_NAME", "default")
    
    if wallet_name:
        wallet_path = Path.home() / ".bittensor" / "wallets" / wallet_name
        if not wallet_path.exists():
            errors.append(f"Wallet {wallet_name} not found at {wallet_path}")
        
        hotkey_path = wallet_path / "hotkeys" / hotkey_name
        if not hotkey_path.exists():
            errors.append(f"Hotkey {hotkey_name} not found at {hotkey_path}")
    
    if errors:
        logger.error("Deployment requirements not met", errors=errors)
        return False
    
    logger.info("All requirements met")
    return True


def check_registration(subnet_uid: int = 90):
    """Check if the hotkey is registered on the subnet."""
    try:
        import bittensor as bt
        
        wallet_name = os.getenv("WALLET_NAME")
        hotkey_name = os.getenv("HOTKEY_NAME", "default")
        network = os.getenv("NETWORK", "finney")
        
        logger.info("Checking registration", 
                   wallet=wallet_name,
                   hotkey=hotkey_name,
                   subnet=subnet_uid,
                   network=network)
        
        # Load wallet
        wallet = bt.wallet(name=wallet_name, hotkey=hotkey_name)
        
        # Connect to subtensor
        subtensor = bt.subtensor(network=network)
        
        # Check registration
        is_registered = subtensor.is_hotkey_registered(
            netuid=subnet_uid,
            hotkey_ss58=wallet.hotkey.ss58_address
        )
        
        if is_registered:
            logger.info("Hotkey is registered on subnet", 
                       hotkey=wallet.hotkey.ss58_address,
                       subnet=subnet_uid)
            
            # Get metagraph to check stake
            metagraph = subtensor.metagraph(netuid=subnet_uid)
            for neuron in metagraph.neurons:
                if neuron.hotkey == wallet.hotkey.ss58_address:
                    logger.info("Validator neuron found",
                               uid=neuron.uid,
                               stake=neuron.stake.tao,
                               active=neuron.active)
                    return True
        else:
            logger.error("Hotkey not registered on subnet",
                        hotkey=wallet.hotkey.ss58_address,
                        subnet=subnet_uid)
            logger.info("To register: btcli subnet register --netuid 90")
            return False
            
    except Exception as e:
        logger.error("Failed to check registration", error=str(e))
        return False
    
    return False


def install_dependencies():
    """Install production dependencies."""
    logger.info("Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install dependencies", error=str(e))
        return False


async def test_validator():
    """Test validator initialization and basic functionality."""
    logger.info("Testing validator initialization...")
    
    try:
        # Test imports
        from validator.main import Validator
        from validator.bittensor_integration import create_validator
        
        # Create validator with mock for testing
        test_config = {
            "api_url": os.getenv("API_URL", "https://api.degenbrain.com"),
            "subnet_uid": 90,
            "query_timeout": 30.0
        }
        
        bt_validator = create_validator(test_config, use_mock=True)
        await bt_validator.setup()
        
        logger.info("Validator test successful")
        await bt_validator.close()
        return True
        
    except Exception as e:
        logger.error("Validator test failed", error=str(e))
        return False


async def run_validator(test_mode: bool = False):
    """Run the validator."""
    try:
        from validator.main import main
        
        if test_mode:
            logger.info("Running validator in test mode...")
            # Set test environment
            os.environ["USE_MOCK_VALIDATOR"] = "true"
        else:
            logger.info("Running validator in production mode...")
            os.environ.pop("USE_MOCK_VALIDATOR", None)
        
        await main()
        
    except KeyboardInterrupt:
        logger.info("Validator stopped by user")
    except Exception as e:
        logger.error("Validator failed", error=str(e))
        raise


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Subnet 90 validator")
    parser.add_argument("--test", action="store_true", 
                       help="Run in test mode with mock Bittensor")
    parser.add_argument("--skip-checks", action="store_true",
                       help="Skip requirement checks")
    parser.add_argument("--install-deps", action="store_true",
                       help="Install dependencies before running")
    
    args = parser.parse_args()
    
    logger.info("Starting Subnet 90 validator deployment", 
               test_mode=args.test)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # Check requirements unless skipped
    if not args.skip_checks:
        if not check_requirements():
            logger.error("Requirements check failed")
            sys.exit(1)
        
        if not args.test:
            if not check_registration():
                logger.error("Registration check failed")
                sys.exit(1)
    
    # Test validator
    if not asyncio.run(test_validator()):
        logger.error("Validator test failed")
        sys.exit(1)
    
    # Run validator
    logger.info("Starting validator...")
    asyncio.run(run_validator(test_mode=args.test))


if __name__ == "__main__":
    main()