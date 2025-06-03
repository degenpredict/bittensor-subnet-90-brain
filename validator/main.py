"""
Main entry point for the DegenBrain validator.

The validator:
1. Fetches unresolved statements from the API
2. Sends statements to miners for verification
3. Collects and scores miner responses
4. Calculates consensus and sets weights on the Bittensor network
"""
import asyncio
import signal
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass, field

from shared.types import Statement, MinerResponse, ValidationResult
from shared.config import get_config
from shared.api import DegenBrainAPIClient
from validator.weights import WeightsCalculator


logger = structlog.get_logger()


@dataclass
class ValidatorStats:
    """Track validator performance metrics."""
    statements_processed: int = 0
    consensus_reached: int = 0
    miners_queried: int = 0
    weights_updated: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    def get_uptime(self) -> timedelta:
        """Get validator uptime."""
        return datetime.now() - self.start_time


class Validator:
    """
    Main validator class that orchestrates the validation process.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize validator.
        
        Args:
            config: Optional configuration overrides
        """
        self.config = get_config()
        if config:
            # Override config with provided values
            for key, value in config.items():
                setattr(self.config, key, value)
        
        # Initialize components
        self.api_client = DegenBrainAPIClient(self.config.api_url)
        self.weights_calculator = WeightsCalculator({
            "accuracy_weight": 0.4,
            "confidence_weight": 0.2,
            "consistency_weight": 0.3,
            "source_quality_weight": 0.1
        })
        
        # State management
        self.running = False
        self.stats = ValidatorStats()
        self.active_miners: Set[int] = set()
        
        # Bittensor components (will be initialized in setup)
        self.wallet = None
        self.subtensor = None
        self.dendrite = None
        self.metagraph = None
        
        logger.info("Validator initialized", config=self.config.__dict__)
    
    async def setup(self):
        """
        Set up Bittensor components and connections.
        """
        try:
            # TODO: Initialize Bittensor components in Phase 5
            # self.wallet = bt.wallet(name=self.config.wallet_name, hotkey=self.config.hotkey_name)
            # self.subtensor = bt.subtensor(network=self.config.network_uid)
            # self.dendrite = bt.dendrite(wallet=self.wallet)
            # self.metagraph = self.subtensor.metagraph(self.config.netuid)
            
            logger.info("Validator setup complete")
            
        except Exception as e:
            logger.error("Failed to setup validator", error=str(e))
            raise
    
    async def run(self):
        """
        Main validator loop.
        """
        logger.info("Starting validator")
        self.running = True
        
        try:
            await self.setup()
            
            while self.running:
                try:
                    # Fetch statements to validate
                    statements = await self._fetch_statements()
                    
                    if not statements:
                        logger.debug("No statements to process, waiting...")
                        await asyncio.sleep(10)
                        continue
                    
                    # Process each statement
                    for statement in statements:
                        if not self.running:
                            break
                        
                        await self._process_statement(statement)
                        self.stats.statements_processed += 1
                    
                    # Update weights periodically
                    if self.stats.statements_processed % 10 == 0:
                        await self._update_weights()
                    
                    # Brief pause between cycles
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error("Error in validator loop", error=str(e))
                    self.stats.errors += 1
                    await asyncio.sleep(5)  # Back off on error
            
        finally:
            await self.shutdown()
    
    async def _fetch_statements(self) -> List[Statement]:
        """
        Fetch unresolved statements from the API.
        """
        try:
            statements = await self.api_client.fetch_statements()
            logger.info("Fetched statements", count=len(statements))
            return statements
        except Exception as e:
            logger.error("Failed to fetch statements", error=str(e))
            return []
    
    async def _process_statement(self, statement: Statement):
        """
        Process a single statement by querying miners and calculating consensus.
        """
        logger.info("Processing statement", 
                   statement=statement.statement[:50] + "...",
                   end_date=statement.end_date)
        
        try:
            # Get miner responses
            responses = await self._query_miners(statement)
            
            if not responses:
                logger.warning("No miner responses received")
                return
            
            # Calculate consensus
            validation_result = self.weights_calculator.calculate_consensus(
                statement, responses
            )
            
            # Log results
            logger.info("Statement validation complete",
                       consensus=validation_result.consensus_resolution.value,
                       confidence=validation_result.consensus_confidence,
                       valid_responses=validation_result.valid_responses,
                       total_responses=validation_result.total_responses)
            
            # Update stats
            if validation_result.consensus_resolution.value != "PENDING":
                self.stats.consensus_reached += 1
            
            # Post consensus back to API (optional)
            if hasattr(statement, 'id') and statement.id:
                await self.api_client.post_consensus(
                    statement.id,
                    validation_result.to_dict()
                )
            
        except Exception as e:
            logger.error("Failed to process statement", 
                        statement=statement.statement[:50] + "...",
                        error=str(e))
            self.stats.errors += 1
    
    async def _query_miners(self, statement: Statement) -> List[MinerResponse]:
        """
        Query miners for their responses to a statement.
        
        For now, this simulates miner responses. In Phase 5, this will
        use Bittensor to actually query miners on the network.
        """
        # TODO: Implement actual Bittensor miner querying in Phase 5
        # For now, simulate with mock responses
        
        logger.info("Querying miners", statement=statement.statement[:50] + "...")
        
        # Simulate 5-10 miners responding
        import random
        from shared.types import Resolution
        
        num_miners = random.randint(5, 10)
        responses = []
        
        for i in range(num_miners):
            # Simulate different miner behaviors
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
        
        self.stats.miners_queried += num_miners
        logger.info("Received miner responses", count=len(responses))
        
        return responses
    
    async def _update_weights(self):
        """
        Update miner weights on the Bittensor network.
        
        This is called periodically to update weights based on
        accumulated miner performance.
        """
        try:
            # TODO: Implement actual weight setting in Phase 5
            # For now, just log
            logger.info("Updating miner weights", 
                       statements_processed=self.stats.statements_processed)
            
            self.stats.weights_updated += 1
            
        except Exception as e:
            logger.error("Failed to update weights", error=str(e))
            self.stats.errors += 1
    
    async def shutdown(self):
        """
        Gracefully shutdown the validator.
        """
        logger.info("Shutting down validator", stats=self.get_stats())
        self.running = False
        
        # Close API client
        await self.api_client.close()
        
        # TODO: Clean up Bittensor components in Phase 5
    
    def get_stats(self) -> Dict:
        """
        Get current validator statistics.
        """
        return {
            "statements_processed": self.stats.statements_processed,
            "consensus_reached": self.stats.consensus_reached,
            "miners_queried": self.stats.miners_queried,
            "weights_updated": self.stats.weights_updated,
            "errors": self.stats.errors,
            "uptime": str(self.stats.get_uptime()),
            "consensus_rate": (
                self.stats.consensus_reached / self.stats.statements_processed
                if self.stats.statements_processed > 0 else 0
            )
        }


# Global validator instance
validator: Optional[Validator] = None


async def main():
    """
    Main entry point for the validator.
    """
    global validator
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, shutting down...")
        if validator:
            validator.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and run validator
        validator = Validator()
        await validator.run()
        
    except Exception as e:
        logger.error("Validator failed", error=str(e))
        raise
    finally:
        if validator:
            await validator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())