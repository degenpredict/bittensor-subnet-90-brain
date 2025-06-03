"""
Miner main entry point for DegenBrain subnet.
"""
import asyncio
import signal
import sys
import time
from typing import Optional, Dict, Any
import structlog

from shared import get_config, get_task, MinerResponse, Statement
from shared.api import DegenBrainAPIClient
from miner.agents.dummy_agent import DummyAgent
from miner.agents.base_agent import BaseAgent


# Set up structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class Miner:
    """
    Main miner class that polls for tasks and processes them.
    """
    
    def __init__(self, agent: Optional[BaseAgent] = None):
        """
        Initialize the miner.
        
        Args:
            agent: The agent to use for verification. If None, uses DummyAgent.
        """
        self.config = get_config()
        self.agent = agent or self._create_default_agent()
        self.api_client = DegenBrainAPIClient()
        self.running = False
        self.tasks_processed = 0
        self.last_task_time = None
        
        logger.info("Miner initialized", 
                   agent=self.agent.name,
                   network=self.config.network,
                   miner_port=self.config.miner_port)
    
    def _create_default_agent(self) -> BaseAgent:
        """Create the default agent based on config."""
        agent_type = self.config.miner_agent
        
        if agent_type == "dummy" or agent_type == "hybrid":
            # For now, use dummy agent for both
            # In future, we'll implement hybrid agent
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
        """Set up miner components."""
        # Currently minimal setup, will expand in Phase 5
        logger.info("Miner setup complete")
    
    async def start(self):
        """Start the miner main loop."""
        self.running = True
        logger.info("Miner starting...")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            await self._main_loop()
        except Exception as e:
            logger.error("Error in main loop", error=str(e))
        finally:
            await self.shutdown()
    
    async def _main_loop(self):
        """Main polling loop."""
        poll_interval = 10  # seconds
        
        while self.running:
            try:
                # Get a task
                task = await self._get_next_task()
                
                if task:
                    # Process the task
                    response = await self._process_task(task)
                    
                    # Submit the response
                    success = await self._submit_response(response)
                    
                    if success:
                        self.tasks_processed += 1
                        self.last_task_time = time.time()
                        logger.info("Task completed successfully",
                                   tasks_processed=self.tasks_processed)
                else:
                    logger.debug("No tasks available")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                logger.info("Main loop cancelled")
                break
            except Exception as e:
                logger.error("Error in polling loop", error=str(e))
                await asyncio.sleep(poll_interval)
    
    async def _get_next_task(self) -> Optional[Statement]:
        """Get the next task to process."""
        try:
            # In production, this would get tasks from validator
            # For now, we'll use the API directly
            task = await get_task()
            
            if task:
                logger.info("Received task", 
                           statement=task.statement[:50] + "...",
                           end_date=task.end_date)
            
            return task
            
        except Exception as e:
            logger.error("Error getting task", error=str(e))
            return None
    
    async def _process_task(self, task: Statement) -> MinerResponse:
        """Process a task using the agent."""
        logger.info("Processing task", statement_id=task.id)
        
        start_time = time.time()
        
        try:
            # Use the agent to verify the statement
            response = await self.agent.process_statement(task)
            
            # Add miner metadata
            response.miner_uid = self.config.subnet_uid  # This would be actual miner UID
            
            process_time = time.time() - start_time
            logger.info("Task processed",
                       resolution=response.resolution.value,
                       confidence=response.confidence,
                       process_time=f"{process_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error("Error processing task", error=str(e))
            # Return error response
            return MinerResponse(
                statement=task.statement,
                resolution="PENDING",
                confidence=0.0,
                summary=f"Error processing: {str(e)}",
                sources=["error"]
            )
    
    async def _submit_response(self, response: MinerResponse) -> bool:
        """Submit response to validator."""
        try:
            # In production, this would submit to validator via Bittensor
            # For now, we'll just log it
            logger.info("Submitting response",
                       resolution=response.resolution,
                       confidence=response.confidence)
            
            # Simulate submission
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error("Error submitting response", error=str(e))
            return False
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down miner...")
        self.running = False
        
        # Close API client
        if hasattr(self, 'api_client'):
            await self.api_client.close()
        
        logger.info("Miner shutdown complete",
                   tasks_processed=self.tasks_processed)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get miner statistics."""
        uptime = 0
        if self.last_task_time:
            uptime = time.time() - self.last_task_time
            
        return {
            "tasks_processed": self.tasks_processed,
            "uptime_seconds": uptime,
            "agent": self.agent.get_info(),
            "is_running": self.running
        }


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