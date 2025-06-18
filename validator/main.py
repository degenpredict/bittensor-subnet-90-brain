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
import os
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass, field

from shared.types import Statement, MinerResponse, ValidationResult
from shared.config import get_config
from shared.api import DegenBrainAPIClient
from validator.weights import WeightsCalculator
from validator.bittensor_integration import create_validator


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
        
        # Bittensor integration
        use_mock = os.getenv("USE_MOCK_VALIDATOR", "false").lower() == "true"
        self.bt_validator = create_validator(config, use_mock=use_mock)
        
        logger.info("Validator initialized", config=self.config.__dict__)
    
    async def setup(self):
        """
        Set up Bittensor components and connections.
        """
        try:
            # Initialize Bittensor validator
            await self.bt_validator.setup()
            
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
                        # Wait longer since API has rate limiting (16 min recommended interval)
                        await asyncio.sleep(60)  # Wait 1 minute before trying again
                        continue
                    
                    # Process each statement
                    for statement in statements:
                        if not self.running:
                            break
                        
                        await self._process_statement(statement)
                        self.stats.statements_processed += 1
                    
                    # Update weights more frequently (every 2 statements) to start emissions
                    if self.stats.statements_processed % 2 == 0:
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
            
            # Submit miner responses to brain-api
            if hasattr(statement, 'id') and statement.id:
                # Get validator ID from wallet hotkey
                validator_id = str(self.bt_validator.wallet.hotkey.ss58_address)
                
                # Submit all miner responses to brain-api
                success = await self.api_client.submit_miner_responses(
                    statement.id,
                    validator_id,
                    responses
                )
                
                if success:
                    logger.info("Successfully submitted responses to brain-api",
                               statement_id=statement.id,
                               miner_count=len(responses))
                else:
                    logger.warning("Failed to submit responses to brain-api",
                                  statement_id=statement.id)
            
        except Exception as e:
            logger.error("Failed to process statement", 
                        statement=statement.statement[:50] + "...",
                        error=str(e))
            self.stats.errors += 1
    
    async def _query_miners(self, statement: Statement) -> List[MinerResponse]:
        """
        Query miners for their responses to a statement.
        
        Uses Bittensor network to actually query miners.
        """
        logger.info("Querying miners", statement=statement.statement[:50] + "...")
        
        try:
            # Query miners through Bittensor network
            responses = await self.bt_validator.query_miners(statement)
            
            self.stats.miners_queried += len(responses)
            logger.info("Received miner responses", count=len(responses))
            
            return responses
            
        except Exception as e:
            logger.error("Failed to query miners", error=str(e))
            return []
    
    async def _update_weights(self):
        """
        Update miner weights on the Bittensor network.
        
        This is called periodically to update weights based on
        accumulated miner performance. If no scores available,
        uses bootstrap mode to start emissions.
        """
        try:
            # Calculate weights based on miner performance
            scores = self.weights_calculator.get_miner_scores()
            
            # Force weight setting to enable emissions
            if scores:
                # Normal mode: use performance-based scores
                success = await self.bt_validator.set_weights(scores)
                logger.info("Set performance-based weights", 
                           statements_processed=self.stats.statements_processed,
                           num_weights=len(scores))
            else:
                # Bootstrap mode: set equal weights to start emissions
                logger.info("No performance scores available, using bootstrap weights")
                success = await self.bt_validator.set_weights({}, force_equal_weights=True)
            
            if success:
                self.stats.weights_updated += 1
                logger.info("Weights updated successfully", 
                           mode="performance" if scores else "bootstrap",
                           statements_processed=self.stats.statements_processed)
            else:
                logger.warning("Failed to set weights on network")
                self.stats.errors += 1
            
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
        
        # Clean up Bittensor components
        await self.bt_validator.close()
    
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