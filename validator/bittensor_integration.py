"""
Bittensor integration for production validator deployment.
This module handles the actual Bittensor network communication.
"""
import asyncio
import sys
from typing import List, Dict, Optional, Tuple
import structlog

try:
    import bittensor as bt
    import torch
    BITTENSOR_AVAILABLE = True
except ImportError:
    BITTENSOR_AVAILABLE = False
    bt = None
    torch = None

from shared.types import Statement, MinerResponse, Resolution
from shared.config import get_config
from shared.protocol import DegenBrainSynapse, ProtocolValidator, LegacyProtocolHandler

logger = structlog.get_logger()


class BittensorValidator:
    """
    Production Bittensor validator for Subnet 90.
    Handles actual network communication and weight setting.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Bittensor validator."""
        if not BITTENSOR_AVAILABLE:
            raise ImportError(
                "Bittensor not available. Install with: pip install bittensor"
            )
        
        self.config = get_config()
        if config:
            for key, value in config.items():
                setattr(self.config, key, value)
        
        # Initialize Bittensor components
        self.wallet = None
        self.subtensor = None
        self.dendrite = None
        self.metagraph = None
        self.axon = None
        
        logger.info("BittensorValidator initialized", 
                   network=self.config.network,
                   netuid=self.config.subnet_uid)
    
    async def setup(self):
        """Set up Bittensor components."""
        try:
            # Initialize wallet with special handling for validator setup
            # Validators only need hotkey for signing; coldkey is for identification only
            try:
                self.wallet = bt.wallet(
                    name=self.config.wallet_name,
                    hotkey=self.config.hotkey_name
                )
                coldkey_address = self.wallet.coldkey.ss58_address
            except Exception as e:
                # If coldkey file doesn't exist, try to read from coldkeypub.txt
                import json
                import os
                coldkeypub_path = os.path.expanduser(
                    f"~/.bittensor/wallets/{self.config.wallet_name}/coldkeypub.txt"
                )
                if os.path.exists(coldkeypub_path):
                    with open(coldkeypub_path, 'r') as f:
                        coldkey_data = json.load(f)
                        coldkey_address = coldkey_data.get('ss58Address', 'Unknown')
                    logger.info("Using coldkeypub.txt for coldkey address")
                    
                    # Still need to load wallet for hotkey
                    self.wallet = bt.wallet(
                        name=self.config.wallet_name,
                        hotkey=self.config.hotkey_name,
                        _ignore_coldkey=True  # This might not work, depends on bittensor version
                    )
                else:
                    raise Exception(f"Neither coldkey nor coldkeypub.txt found: {str(e)}")
            
            logger.info("Wallet loaded", 
                       coldkey=coldkey_address,
                       hotkey=self.wallet.hotkey.ss58_address)
            
            # Initialize subtensor
            self.subtensor = bt.subtensor(network=self.config.network)
            logger.info("Connected to subtensor", 
                       network=self.config.network,
                       chain_endpoint=self.subtensor.chain_endpoint)
            
            # Initialize dendrite for querying miners
            self.dendrite = bt.dendrite(wallet=self.wallet)
            logger.info("Dendrite initialized")
            
            # Get metagraph
            self.metagraph = self.subtensor.metagraph(netuid=self.config.subnet_uid)
            logger.info("Metagraph synced", 
                       neurons=len(self.metagraph.neurons),
                       netuid=self.config.subnet_uid)
            
            # Check if registered
            if not self.subtensor.is_hotkey_registered(
                netuid=self.config.subnet_uid, 
                hotkey_ss58=self.wallet.hotkey.ss58_address
            ):
                logger.error("Hotkey not registered on subnet")
                raise ValueError(f"Hotkey not registered on subnet {self.config.subnet_uid}")
            
            logger.info("Bittensor setup complete")
            
        except Exception as e:
            logger.error("Failed to setup Bittensor components", error=str(e))
            raise
    
    async def query_miners(self, statement: Statement) -> List[MinerResponse]:
        """
        Query miners on the Bittensor network for statement verification.
        
        Args:
            statement: Statement to verify
            
        Returns:
            List of miner responses
        """
        if not self.dendrite or not self.metagraph:
            raise ValueError("Bittensor components not initialized")
        
        logger.info("Querying miners on network", 
                   statement=statement.statement[:50] + "...",
                   num_miners=len(self.metagraph.neurons))
        
        try:
            # Sync metagraph to get latest state
            self.metagraph.sync(subtensor=self.subtensor)
            
            # Get all active miners (including own hotkey if serving)
            miner_axons = []
            miner_uids = []
            
            for uid, neuron in enumerate(self.metagraph.neurons):
                # Skip if neuron is not active
                if not neuron.axon_info.is_serving:
                    continue
                
                # Log if this is our own neuron (but still include it)
                if neuron.hotkey == self.wallet.hotkey.ss58_address:
                    logger.info("Including own hotkey as miner", 
                               uid=uid, 
                               hotkey=neuron.hotkey[:8] + "...")
                
                # Add to query list
                miner_axons.append(neuron.axon_info)
                miner_uids.append(uid)
            
            if not miner_axons:
                logger.warning("No active miners found")
                return []
            
            logger.info("Miner discovery complete", 
                       total_neurons=len(self.metagraph.neurons),
                       serving_neurons=len(miner_axons),
                       own_hotkey_included=any(
                           self.metagraph.neurons[uid].hotkey == self.wallet.hotkey.ss58_address 
                           for uid in miner_uids
                       ))
            
            # Create synapse using official Subnet 90 protocol
            synapse = ProtocolValidator.create_request_synapse(
                statement=statement.statement,
                end_date=statement.end_date,
                created_at=statement.createdAt,
                initial_value=statement.initialValue,
                statement_id=statement.id
            )
            
            # Query miners
            responses = await self.dendrite(
                axons=miner_axons,
                synapse=synapse,
                timeout=self.config.query_timeout
            )
            
            # Convert responses to MinerResponse objects with protocol handling
            miner_responses = []
            for i, response in enumerate(responses):
                parsed_response = self.parse_miner_response(response, miner_uids[i])
                if parsed_response:
                    miner_responses.append(parsed_response)
            
            logger.info("Received miner responses", 
                       total_queried=len(miner_axons),
                       valid_responses=len(miner_responses))
            
            return miner_responses
            
        except Exception as e:
            logger.error("Failed to query miners", error=str(e))
            return []
    
    async def set_weights(self, scores: Dict[int, float], force_equal_weights: bool = False) -> bool:
        """
        Set weights on the Bittensor network based on miner scores.
        
        Args:
            scores: Dictionary mapping miner UID to normalized score
            force_equal_weights: If True, set equal weights to bootstrap emissions
            
        Returns:
            True if weights were set successfully
        """
        if not self.subtensor or not self.wallet:
            raise ValueError("Bittensor components not initialized")
        
        try:
            # Prepare weights tensor
            num_neurons = len(self.metagraph.neurons)
            weights = torch.zeros(num_neurons)
            
            if force_equal_weights or len(scores) == 0:
                # Bootstrap mode: set equal weights to start emissions
                logger.info("Using bootstrap equal weights to start emissions")
                active_miners = []
                for uid, neuron in enumerate(self.metagraph.neurons):
                    # Include all registered miners for bootstrap (including own if mining)
                    active_miners.append(uid)
                
                if active_miners:
                    equal_weight = 1.0 / len(active_miners)
                    for uid in active_miners:
                        weights[uid] = equal_weight
                    logger.info("Set equal weights for bootstrap", 
                               active_miners=len(active_miners))
                else:
                    logger.warning("No miners found for bootstrap weights")
                    return False
            else:
                # Normal mode: use performance-based scores
                for uid, score in scores.items():
                    if 0 <= uid < num_neurons:
                        weights[uid] = score
                
                # Normalize weights
                if weights.sum() > 0:
                    weights = weights / weights.sum()
            
            logger.info("Setting weights on network", 
                       num_weights=len(scores) if scores else len([w for w in weights if w > 0]),
                       total_weight=weights.sum().item(),
                       bootstrap=force_equal_weights or len(scores) == 0)
            
            # Set weights on chain
            success = self.subtensor.set_weights(
                wallet=self.wallet,
                netuid=self.config.subnet_uid,
                uids=torch.arange(num_neurons),
                weights=weights,
                wait_for_inclusion=True,
                wait_for_finalization=False
            )
            
            if success:
                logger.info("Weights set successfully")
            else:
                logger.error("Failed to set weights")
            
            return success
            
        except Exception as e:
            logger.error("Failed to set weights", error=str(e))
            return False
    
    def get_network_info(self) -> Dict:
        """Get current network information."""
        if not self.metagraph:
            return {}
        
        return {
            "netuid": self.config.subnet_uid,
            "network": self.config.network,
            "total_neurons": len(self.metagraph.neurons),
            "registered": self.subtensor.is_hotkey_registered(
                netuid=self.config.subnet_uid,
                hotkey_ss58=self.wallet.hotkey.ss58_address
            ) if self.subtensor and self.wallet else False,
            "stake": self.metagraph.total_stake.sum().item() if self.metagraph.total_stake is not None else 0,
            "block": self.subtensor.block if self.subtensor else 0
        }
    
    async def close(self):
        """Clean up Bittensor connections."""
        if self.dendrite:
            # Close any open connections
            pass
        
        logger.info("Bittensor validator closed")
    
    def parse_miner_response(self, response, miner_uid: int) -> Optional[MinerResponse]:
        """
        Parse miner response with graceful handling of protocol mismatches.
        
        Args:
            response: Raw response from miner
            miner_uid: UID of the responding miner
            
        Returns:
            MinerResponse object or None if unparseable
        """
        if response is None:
            logger.warning(f"Received None response from miner {miner_uid}")
            return None
        
        try:
            # First try to parse as proper DegenBrainSynapse
            if isinstance(response, DegenBrainSynapse) and ProtocolValidator.is_valid_synapse(response):
                return MinerResponse(
                    statement=response.statement,
                    resolution=Resolution(response.resolution),
                    confidence=response.confidence,
                    summary=response.summary or "No summary provided",
                    sources=response.sources or [],
                    miner_uid=miner_uid,
                    target_value=response.target_value
                )
            
            # Try legacy protocol parsing
            legacy_data = LegacyProtocolHandler.try_parse_legacy_response(response)
            if legacy_data:
                logger.info(f"Parsed legacy response from miner {miner_uid}")
                return MinerResponse(
                    statement=legacy_data.get("statement", "Unknown statement"),
                    resolution=Resolution(legacy_data["resolution"]),
                    confidence=legacy_data["confidence"],
                    summary=legacy_data["summary"],
                    sources=legacy_data["sources"],
                    miner_uid=miner_uid,
                    target_value=legacy_data.get("target_value")
                )
            
            # If all parsing fails, log the issue but continue
            logger.warning(f"Could not parse response from miner {miner_uid}", 
                         response_type=type(response).__name__,
                         has_resolution=hasattr(response, 'resolution'))
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse response from miner {miner_uid}", 
                         error=str(e))
            return None


# Mock version for testing without Bittensor
class MockBittensorValidator:
    """Mock validator for testing without Bittensor network."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize mock validator."""
        self.config = get_config()
        if config:
            for key, value in config.items():
                setattr(self.config, key, value)
        
        logger.info("MockBittensorValidator initialized (testing mode)")
    
    async def setup(self):
        """Mock setup."""
        logger.info("Mock Bittensor setup complete")
    
    async def query_miners(self, statement: Statement) -> List[MinerResponse]:
        """Mock miner querying."""
        # Return simulated responses (same as current implementation)
        import random
        
        num_miners = random.randint(5, 10)
        responses = []
        
        for i in range(num_miners):
            if random.random() < 0.7:  # 70% agree on resolution
                resolution = Resolution.TRUE if random.random() < 0.5 else Resolution.FALSE
                confidence = random.uniform(70, 95)
            else:  # 30% are uncertain
                resolution = Resolution.PENDING
                confidence = random.uniform(30, 60)
            
            response = MinerResponse(
                statement=statement.statement,
                resolution=resolution,
                confidence=confidence,
                summary=f"Mock analysis from miner {i}",
                sources=[f"source_{i}_1", f"source_{i}_2"],
                miner_uid=i,
                target_value=100000.0 if "100,000" in statement.statement else None
            )
            responses.append(response)
        
        logger.info("Mock miner responses generated", count=len(responses))
        return responses
    
    async def set_weights(self, scores: Dict[int, float]) -> bool:
        """Mock weight setting."""
        logger.info("Mock weights set", num_weights=len(scores))
        return True
    
    def get_network_info(self) -> Dict:
        """Mock network info."""
        return {
            "netuid": self.config.subnet_uid,
            "network": "mock",
            "total_neurons": 10,
            "registered": True,
            "stake": 1000.0,
            "block": 12345
        }
    
    async def close(self):
        """Mock cleanup."""
        logger.info("Mock Bittensor validator closed")


def create_validator(config: Optional[Dict] = None, use_mock: bool = False) -> BittensorValidator:
    """
    Factory function to create the appropriate validator.
    
    Args:
        config: Optional configuration
        use_mock: If True, use mock validator for testing
        
    Returns:
        Validator instance
    """
    if use_mock or not BITTENSOR_AVAILABLE:
        if not use_mock:
            logger.warning("Bittensor not available, using mock validator")
        return MockBittensorValidator(config)
    else:
        return BittensorValidator(config)