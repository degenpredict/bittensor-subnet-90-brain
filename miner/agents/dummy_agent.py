"""
Dummy agent for testing purposes.
"""
import random
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from miner.agents.base_agent import BaseAgent
from shared.types import Statement, MinerResponse, Resolution


class DummyAgent(BaseAgent):
    """
    A dummy agent that generates random responses for testing.
    
    This agent is useful for:
    - Testing the miner infrastructure
    - Providing baseline responses
    - Development and debugging
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dummy agent.
        
        Config options:
            - accuracy: float (0-1) - How often to give correct responses
            - delay: float - Seconds to delay response (simulate processing)
            - confidence_range: tuple - (min, max) confidence values
        """
        super().__init__(config)
        self.accuracy = self.config.get("accuracy", 0.7)
        self.delay = self.config.get("delay", 0.5)
        self.confidence_range = self.config.get("confidence_range", (60, 95))
    
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        """
        Generate a dummy response for the statement.
        
        This implementation:
        - Randomly chooses TRUE/FALSE/PENDING based on dates
        - Generates plausible confidence scores
        - Creates simple summaries
        
        Args:
            statement: The Statement to verify.
            
        Returns:
            MinerResponse with dummy verification.
        """
        # Simulate processing time
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        # Determine resolution based on end_date
        resolution = self._determine_resolution(statement)
        
        # Generate confidence
        confidence = random.uniform(*self.confidence_range)
        
        # Generate summary
        summary = self._generate_summary(statement, resolution)
        
        # Generate fake sources
        sources = self._generate_sources()
        
        # Extract target value if present
        target_value = self._extract_target_value(statement.statement)
        
        # Generate current value (fake)
        current_value = self._generate_current_value(target_value)
        
        return MinerResponse(
            statement=statement.statement,
            resolution=resolution,
            confidence=confidence,
            summary=summary,
            sources=sources,
            target_value=target_value,
            reasoning=f"Dummy agent analysis: Resolution={resolution.value}, Confidence={confidence:.1f}%"
        )
    
    def _determine_resolution(self, statement: Statement) -> Resolution:
        """Determine resolution based on dates and randomness."""
        if not statement.end_date:
            return Resolution.PENDING
        
        try:
            # Parse end date
            end_date = datetime.fromisoformat(statement.end_date.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if end_date > now:
                # Future date - always PENDING
                return Resolution.PENDING
            else:
                # Past date - randomly TRUE or FALSE based on accuracy
                if random.random() < self.accuracy:
                    # Simulate "correct" response
                    return random.choice([Resolution.TRUE, Resolution.FALSE])
                else:
                    # Simulate "incorrect" response
                    return random.choice([Resolution.TRUE, Resolution.FALSE])
        except:
            # Error parsing date - default to PENDING
            return Resolution.PENDING
    
    def _generate_summary(self, statement: Statement, resolution: Resolution) -> str:
        """Generate a plausible summary."""
        if resolution == Resolution.PENDING:
            return f"The prediction deadline has not yet passed. Current analysis shows the statement is still pending verification."
        elif resolution == Resolution.TRUE:
            return f"The prediction has been verified as TRUE. The conditions specified in the statement have been met."
        else:
            return f"The prediction has been verified as FALSE. The conditions specified in the statement were not met by the deadline."
    
    def _generate_sources(self) -> list[str]:
        """Generate fake but plausible sources."""
        possible_sources = [
            "CoinGecko API",
            "CoinMarketCap",
            "Yahoo Finance",
            "Bloomberg Terminal",
            "Reuters Market Data",
            "Binance Exchange",
            "Kraken Exchange",
            "Historical Price Data",
            "Market Analysis",
            "Trading View"
        ]
        
        # Select 2-4 random sources
        num_sources = random.randint(2, 4)
        return random.sample(possible_sources, num_sources)
    
    def _extract_target_value(self, statement: str) -> Optional[float]:
        """Extract target value from statement (simplified)."""
        import re
        
        # Look for dollar amounts
        dollar_match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', statement)
        if dollar_match:
            value_str = dollar_match.group(1).replace(',', '')
            try:
                return float(value_str)
            except:
                pass
        
        # Look for plain numbers with context
        number_match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:dollars?|usd|points?)', statement, re.IGNORECASE)
        if number_match:
            value_str = number_match.group(1).replace(',', '')
            try:
                return float(value_str)
            except:
                pass
        
        return None
    
    def _generate_current_value(self, target_value: Optional[float]) -> Optional[float]:
        """Generate a fake current value based on target."""
        if not target_value:
            return None
        
        # Generate value within 50% of target
        min_val = target_value * 0.5
        max_val = target_value * 1.5
        
        return round(random.uniform(min_val, max_val), 2)