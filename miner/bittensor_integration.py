"""
Bittensor integration for production miner deployment.
This module handles actual Bittensor network serving and synapse handling.
"""
import asyncio
import time
from typing import Optional, Dict, Any
import structlog

try:
    import bittensor as bt
    import torch
    BITTENSOR_AVAILABLE = True
except ImportError:
    BITTENSOR_AVAILABLE = False
    bt = None
    torch = None

from shared.config import get_config
from shared.protocol import DegenBrainSynapse, ProtocolValidator, Resolution
from miner.agents.base_agent import BaseAgent
from miner.agents.dummy_agent import DummyAgent

logger = structlog.get_logger()


def blacklist(synapse):
    """Standalone blacklist function for Bittensor."""
    try:
        # Check if synapse has required fields
        if not hasattr(synapse, 'statement') or not hasattr(synapse, 'end_date'):
            return True, "Missing required fields"
        if not synapse.statement or not synapse.end_date:
            return True, "Missing required fields"
        
        # Check statement length
        if len(synapse.statement) < 10 or len(synapse.statement) > 1000:
            return True, f"Invalid statement length: {len(synapse.statement)}"
        
        return False, "Request accepted"
        
    except Exception as e:
        return True, f"Blacklist error: {str(e)}"


def priority(synapse):
    """Standalone priority function for Bittensor."""
    return 1.0


class BittensorMiner:
    """
    Production Bittensor miner for Subnet 90.
    Serves DegenBrainSynapse requests via axon server.
    """
    
    def __init__(self, agent: Optional[BaseAgent] = None, config: Optional[Dict] = None):
        """Initialize Bittensor miner."""
        if not BITTENSOR_AVAILABLE:
            raise ImportError(
                "Bittensor not available. Install with: pip install bittensor"
            )
        
        self.config = get_config()
        if config:
            for key, value in config.items():
                setattr(self.config, key, value)
        
        # Initialize agent
        self.agent = agent or DummyAgent()
        
        # Initialize Bittensor components
        self.wallet = None
        self.subtensor = None
        self.axon = None
        self.metagraph = None
        
        # Stats
        self.requests_processed = 0
        self.start_time = time.time()
        
        logger.info("BittensorMiner initialized",
                   agent=self.agent.name,
                   network=self.config.network,
                   netuid=self.config.subnet_uid)
    
    async def setup(self):
        """Set up Bittensor components."""
        try:
            # Initialize wallet
            self.wallet = bt.wallet(
                name=self.config.wallet_name,
                hotkey=self.config.hotkey_name
            )
            logger.info("Wallet loaded",
                       hotkey=self.wallet.hotkey.ss58_address)
            
            # Initialize subtensor
            self.subtensor = bt.subtensor(network=self.config.network)
            logger.info("Connected to subtensor",
                       network=self.config.network,
                       chain_endpoint=self.subtensor.chain_endpoint)
            
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
            
            # Initialize axon
            self.axon = bt.axon(
                wallet=self.wallet,
                port=self.config.miner_port
            )
            
            # Attach synapse handler  
            self.axon.attach(
                forward_fn=self.verify_statement
            )
            
            logger.info("Axon initialized", port=self.config.miner_port)
            
        except Exception as e:
            logger.error("Failed to setup Bittensor components", error=str(e))
            raise
    
    async def verify_statement(self, synapse: DegenBrainSynapse) -> DegenBrainSynapse:
        """
        Handle incoming statement verification requests from validators.
        
        Args:
            synapse: DegenBrainSynapse with statement to verify
            
        Returns:
            DegenBrainSynapse with verification results
        """
        start_time = time.time()
        
        logger.info("Processing verification request",
                   statement=synapse.statement[:50] + "...",
                   end_date=synapse.end_date)
        
        try:
            # Convert synapse to Statement for agent processing
            from shared.types import Statement
            statement = Statement(
                statement=synapse.statement,
                end_date=synapse.end_date,
                createdAt=synapse.created_at,
                initialValue=synapse.initial_value,
                id=None  # Not needed for processing
            )
            
            # Process using agent
            miner_response = await self.agent.process_statement(statement)
            
            # Calculate processing time
            analysis_time = time.time() - start_time
            
            # Create response synapse
            response = ProtocolValidator.create_response_synapse(
                request_synapse=synapse,
                resolution=miner_response.resolution.value,
                confidence=miner_response.confidence,
                summary=miner_response.summary,
                sources=miner_response.sources,
                reasoning=getattr(miner_response, 'reasoning', ''),
                target_value=miner_response.target_value,
                miner_version=f"subnet90-miner-v1.0-{self.agent.name}"
            )
            
            # Set analysis time
            response.analysis_time = analysis_time
            
            # Update stats
            self.requests_processed += 1
            
            logger.info("Verification complete",
                       resolution=response.resolution,
                       confidence=response.confidence,
                       analysis_time=f"{analysis_time:.2f}s",
                       requests_processed=self.requests_processed)
            
            return response
            
        except Exception as e:
            logger.error("Error processing verification request", error=str(e))
            
            # Return error response
            error_response = ProtocolValidator.create_response_synapse(
                request_synapse=synapse,
                resolution="PENDING",
                confidence=0.0,
                summary=f"Processing error: {str(e)}",
                sources=[],
                reasoning="Error occurred during processing",
                miner_version=f"subnet90-miner-v1.0-{self.agent.name}"
            )
            error_response.analysis_time = time.time() - start_time
            
            return error_response
    
    def blacklist(self, synapse: DegenBrainSynapse) -> tuple[bool, str]:
        """
        Determine if a request should be blacklisted.
        
        Args:
            synapse: Incoming synapse
            
        Returns:
            Tuple of (blacklist_flag, reason)
        """
        # Basic blacklist logic
        try:
            # Check if synapse has required fields
            if not synapse.statement or not synapse.end_date:
                logger.warning("Blacklisting request with missing fields")
                return True, "Missing required fields"
            
            # Check statement length
            if len(synapse.statement) < 10 or len(synapse.statement) > 1000:
                logger.warning("Blacklisting request with invalid statement length",
                             length=len(synapse.statement))
                return True, f"Invalid statement length: {len(synapse.statement)}"
            
            # Could add more sophisticated blacklisting here
            # e.g., rate limiting, validator reputation, etc.
            
            return False, "Request accepted"
            
        except Exception as e:
            logger.warning("Error in blacklist check", error=str(e))
            return True, f"Blacklist error: {str(e)}"
    
    def priority(self, synapse: DegenBrainSynapse) -> float:
        """
        Determine the priority of a request.
        
        Args:
            synapse: Incoming synapse
            
        Returns:
            Priority score (higher = more priority)
        """
        try:
            # Basic priority logic
            base_priority = 1.0
            
            # Could implement priority based on:
            # - Validator stake
            # - Request complexity
            # - Current load
            # etc.
            
            return base_priority
            
        except Exception as e:
            logger.warning("Error calculating priority", error=str(e))
            return 0.0
    
    async def start_serving(self):
        """Start serving requests via axon."""
        try:
            # Start axon
            self.axon.start()
            logger.info("Axon started, serving requests",
                       port=self.config.miner_port,
                       external_ip=self.axon.external_ip)
            
            # Serve on the subnet
            self.axon.serve(netuid=self.config.subnet_uid, subtensor=self.subtensor)
            logger.info("Serving on subnet", netuid=self.config.subnet_uid)
            
        except Exception as e:
            logger.error("Failed to start serving", error=str(e))
            raise
    
    async def stop_serving(self):
        """Stop serving requests."""
        try:
            if self.axon:
                self.axon.stop()
                logger.info("Axon stopped")
                
        except Exception as e:
            logger.error("Error stopping axon", error=str(e))
    
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
            "serving": self.axon is not None,
            "port": self.config.miner_port,
            "requests_processed": self.requests_processed,
            "uptime": time.time() - self.start_time
        }
    
    async def close(self):
        """Clean up Bittensor connections."""
        await self.stop_serving()
        logger.info("Bittensor miner closed")


# Mock version for testing without Bittensor
class MockBittensorMiner:
    """Mock miner for testing without Bittensor network."""
    
    def __init__(self, agent: Optional[BaseAgent] = None, config: Optional[Dict] = None):
        """Initialize mock miner."""
        # Use a minimal config for testing
        class MockConfig:
            def __init__(self):
                self.subnet_uid = 90
                self.network = "mock"
                self.miner_port = 8091
        
        self.config = MockConfig()
        if config:
            for key, value in config.items():
                setattr(self.config, key, value)
        
        self.agent = agent or DummyAgent()
        self.requests_processed = 0
        self.start_time = time.time()
        
        logger.info("MockBittensorMiner initialized (testing mode)")
    
    async def setup(self):
        """Mock setup."""
        logger.info("Mock Bittensor setup complete")
    
    async def verify_statement(self, synapse: DegenBrainSynapse) -> DegenBrainSynapse:
        """Mock statement verification."""
        # Simulate the real verification process
        from shared.types import Statement
        statement = Statement(
            statement=synapse.statement,
            end_date=synapse.end_date,
            createdAt=synapse.created_at,
            initialValue=synapse.initial_value,
            id=None
        )
        
        # Process using agent
        miner_response = await self.agent.process_statement(statement)
        
        # Create mock response
        response = ProtocolValidator.create_response_synapse(
            request_synapse=synapse,
            resolution=miner_response.resolution.value,
            confidence=miner_response.confidence,
            summary=miner_response.summary,
            sources=miner_response.sources,
            reasoning=getattr(miner_response, 'reasoning', ''),
            target_value=miner_response.target_value,
            miner_version=f"mock-subnet90-miner-v1.0-{self.agent.name}"
        )
        response.analysis_time = 0.5  # Mock processing time
        
        self.requests_processed += 1
        logger.info("Mock verification complete", resolution=response.resolution)
        
        return response
    
    def blacklist(self, synapse: DegenBrainSynapse):
        """Mock blacklist check."""
        if len(synapse.statement) < 10:
            return True, "Statement too short"
        return False, "Request accepted"
    
    def priority(self, synapse: DegenBrainSynapse) -> float:
        """Mock priority calculation."""
        return 1.0
    
    async def start_serving(self):
        """Mock serving start."""
        logger.info("Mock axon started")
    
    async def stop_serving(self):
        """Mock serving stop."""
        logger.info("Mock axon stopped")
    
    def get_network_info(self) -> Dict:
        """Mock network info."""
        return {
            "netuid": self.config.subnet_uid,
            "network": "mock",
            "total_neurons": 10,
            "registered": True,
            "serving": True,
            "port": self.config.miner_port,
            "requests_processed": self.requests_processed,
            "uptime": time.time() - self.start_time
        }
    
    async def close(self):
        """Mock cleanup."""
        logger.info("Mock Bittensor miner closed")


def create_miner(agent: Optional[BaseAgent] = None, config: Optional[Dict] = None, use_mock: bool = False) -> BittensorMiner:
    """
    Factory function to create the appropriate miner.
    
    Args:
        agent: Agent to use for verification
        config: Optional configuration
        use_mock: If True, use mock miner for testing
        
    Returns:
        Miner instance
    """
    if use_mock or not BITTENSOR_AVAILABLE:
        if not use_mock:
            logger.warning("Bittensor not available, using mock miner")
        return MockBittensorMiner(agent, config)
    else:
        return BittensorMiner(agent, config)