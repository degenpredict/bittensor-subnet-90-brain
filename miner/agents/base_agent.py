"""
Base agent interface for miners.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import structlog

from shared.types import Statement, MinerResponse, Resolution


logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Abstract base class for miner agents.
    
    All miner agents must inherit from this class and implement
    the verify_statement method.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.
        
        Args:
            config: Optional configuration dictionary for the agent.
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name}", config=self.config)
    
    @abstractmethod
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        """
        Verify a prediction statement and return a response.
        
        This is the main method that each agent must implement.
        It should analyze the statement and determine whether it's
        TRUE, FALSE, or PENDING.
        
        Args:
            statement: The Statement to verify.
            
        Returns:
            MinerResponse with the verification result.
        """
        pass
    
    def validate_response(self, response: MinerResponse) -> bool:
        """
        Validate that a response meets requirements.
        
        Args:
            response: The MinerResponse to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        try:
            # Check required fields
            if not response.statement:
                logger.error("Response missing statement")
                return False
                
            if response.resolution not in Resolution:
                logger.error("Invalid resolution", resolution=response.resolution)
                return False
                
            if not (0 <= response.confidence <= 100):
                logger.error("Invalid confidence", confidence=response.confidence)
                return False
                
            if not response.summary:
                logger.error("Response missing summary")
                return False
                
            if not response.sources:
                logger.error("Response missing sources")
                return False
                
            # Use the built-in validation
            return response.is_valid()
            
        except Exception as e:
            logger.error("Error validating response", error=str(e))
            return False
    
    async def process_statement(self, statement: Statement) -> MinerResponse:
        """
        Process a statement and return a validated response.
        
        This method wraps verify_statement with validation and error handling.
        
        Args:
            statement: The Statement to process.
            
        Returns:
            MinerResponse with the verification result.
        """
        try:
            # Verify the statement
            response = await self.verify_statement(statement)
            
            # Validate the response
            if not self.validate_response(response):
                logger.error("Invalid response generated", agent=self.name)
                # Return a safe default response
                response = MinerResponse(
                    statement=statement.statement,
                    resolution=Resolution.PENDING,
                    confidence=0.0,
                    summary=f"Error: {self.name} generated invalid response",
                    sources=["error"]
                )
            
            # Generate proof hash if not provided
            if not response.proof_hash:
                response.proof_hash = response.generate_proof_hash()
            
            logger.info("Statement processed", 
                       agent=self.name,
                       resolution=response.resolution.value,
                       confidence=response.confidence)
            
            return response
            
        except Exception as e:
            logger.error("Error processing statement", 
                        agent=self.name,
                        error=str(e))
            
            # Return error response
            return MinerResponse(
                statement=statement.statement,
                resolution=Resolution.PENDING,
                confidence=0.0,
                summary=f"Error processing statement: {str(e)}",
                sources=["error"]
            )
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dictionary with agent information.
        """
        return {
            "name": self.name,
            "type": self.__class__.__module__,
            "config": self.config
        }