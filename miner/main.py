"""
Miner main entry point for DegenBrain subnet.
Serves verification requests via Bittensor axon server.
"""
import asyncio
import signal
import sys
import time
import os
from typing import Optional, Dict, Any
import structlog

from shared.config import get_config
from miner.agents.dummy_agent import DummyAgent
from miner.agents.base_agent import BaseAgent
from miner.bittensor_integration import create_miner


# Set up structured logging
import logging
import sys

# Configure Python's standard logging first
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
log_file = os.environ.get("LOG_FILE")

# Set up handlers
handlers = []
if log_file:
    # File handler
    handlers.append(logging.FileHandler(log_file))
    
# Always add console handler for immediate feedback
handlers.append(logging.StreamHandler(sys.stdout))

# Configure root logger
logging.basicConfig(
    level=getattr(logging, log_level),
    handlers=handlers,
    format='%(asctime)s | %(levelname)8s | %(name)s:%(filename)s:%(lineno)d | %(message)s'
)

# Configure structlog to use standard logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class Miner:
    """
    Main miner class that serves verification requests via Bittensor axon.
    """
    
    def __init__(self, agent: Optional[BaseAgent] = None):
        """
        Initialize the miner.
        
        Args:
            agent: The agent to use for verification. If None, uses DummyAgent.
        """
        self.config = get_config()
        self.agent = agent or self._create_default_agent()
        self.running = False
        
        # Initialize Bittensor miner
        use_mock = os.getenv("USE_MOCK_MINER", "false").lower() == "true"
        self.bt_miner = create_miner(self.agent, use_mock=use_mock)
        
        logger.info("Miner initialized", 
                   agent=self.agent.name,
                   network=self.config.network,
                   miner_port=self.config.miner_port,
                   mock_mode=use_mock)
    
    def _create_default_agent(self) -> BaseAgent:
        """Create the default agent based on config."""
        agent_type = self.config.miner_agent
        strategy = os.getenv("MINER_STRATEGY", "dummy")
        
        # If strategy is set to use AI agent, create AIAgent
        if strategy in ["ai_reasoning", "hybrid"] and strategy != "dummy":
            from miner.agents.ai_agent import AIAgent
            
            # Create AI agent config from environment variables
            ai_config = {
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
                "coingecko_api_key": os.getenv("COINGECKO_API_KEY"),
                "alpha_vantage_api_key": os.getenv("ALPHA_VANTAGE_API_KEY"),
                "strategy": strategy,
                "api_url": self.config.api_url,  # Use the same API URL as the validator
                "timeout": int(os.getenv("REQUEST_TIMEOUT", "30"))
            }
            
            logger.info("Creating AI Agent", strategy=strategy, has_openai=bool(ai_config["openai_api_key"]))
            return AIAgent(ai_config)
        
        elif agent_type == "dummy" or strategy == "dummy":
            # Use dummy agent
            return DummyAgent({
                "accuracy": 0.8,
                "delay": 0.2,
                "confidence_range": (70, 95)
            })
        else:
            # Default to dummy agent
            logger.warning(f"Unknown agent type: {agent_type}, using DummyAgent")
            return DummyAgent()
    
    async def setup(self):
        """Set up Bittensor miner components."""
        try:
            # Initialize Bittensor miner
            await self.bt_miner.setup()
            logger.info("Miner setup complete")
            
        except Exception as e:
            logger.error("Failed to setup miner", error=str(e))
            raise
    
    async def start(self):
        """Start the miner axon server."""
        self.running = True
        logger.info("Miner starting...")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Setup components
            await self.setup()
            
            # Start serving requests
            await self.bt_miner.start_serving()
            
            # Keep running until shutdown
            await self._serve_forever()
            
        except Exception as e:
            logger.error("Error starting miner", error=str(e))
        finally:
            await self.shutdown()
    
    async def _serve_forever(self):
        """Keep the server running and log periodic stats."""
        logger.info("Miner serving requests via Bittensor axon")
        
        # Log stats every 5 minutes
        stats_interval = 300  # seconds
        last_stats_time = time.time()
        
        while self.running:
            try:
                # Sleep briefly
                await asyncio.sleep(10)
                
                # Log stats periodically
                current_time = time.time()
                if current_time - last_stats_time >= stats_interval:
                    stats = self.get_stats()
                    logger.info("Miner stats", **stats)
                    last_stats_time = current_time
                
            except asyncio.CancelledError:
                logger.info("Serve loop cancelled")
                break
            except Exception as e:
                logger.error("Error in serve loop", error=str(e))
                await asyncio.sleep(10)
    
    # Note: Task processing now handled by BittensorMiner.verify_statement()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down miner...")
        self.running = False
        
        # Stop Bittensor miner
        if hasattr(self, 'bt_miner'):
            await self.bt_miner.close()
        
        logger.info("Miner shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get miner statistics."""
        stats = {
            "agent": self.agent.get_info(),
            "is_running": self.running
        }
        
        # Add Bittensor miner stats
        if hasattr(self, 'bt_miner'):
            network_info = self.bt_miner.get_network_info()
            stats.update(network_info)
        
        return stats


async def main():
    """Main entry point."""
    logger.info("Starting DegenBrain miner...")
    
    # Create and start miner
    miner = Miner()
    
    try:
        await miner.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
    finally:
        await miner.shutdown()


if __name__ == "__main__":
    # Run the miner
    asyncio.run(main())