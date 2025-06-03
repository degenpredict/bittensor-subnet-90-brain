"""
Mock API responses for testing.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import random


class MockDegenBrainAPI:
    """
    Mock implementation of DegenBrain API for testing.
    """
    
    def __init__(self):
        """Initialize mock API with sample data."""
        self.statements = self._generate_sample_statements()
        self.resolve_cache = {}
        
    def _generate_sample_statements(self) -> List[Dict[str, Any]]:
        """Generate sample statements for testing."""
        now = datetime.now(timezone.utc)
        
        return [
            # Past statements (should resolve to TRUE/FALSE)
            {
                "statement": "Bitcoin will cross $50,000 by March 1, 2024",
                "end_date": "2024-03-01T00:00:00Z",
                "createdAt": "2024-01-01T00:00:00Z",
                "initialValue": 42000.0,
                "id": "past_true_001"
            },
            {
                "statement": "Ethereum will reach $10,000 by April 1, 2024",
                "end_date": "2024-04-01T00:00:00Z",
                "createdAt": "2024-01-15T00:00:00Z",
                "initialValue": 2200.0,
                "id": "past_false_001"
            },
            
            # Future statements (should resolve to PENDING)
            {
                "statement": "Bitcoin will exceed $100,000 by December 31, 2025",
                "end_date": (now + timedelta(days=365)).isoformat(),
                "createdAt": now.isoformat(),
                "initialValue": 65000.0,
                "id": "future_001"
            },
            {
                "statement": "Solana will reach $500 before June 2025",
                "end_date": "2025-06-01T00:00:00Z",
                "createdAt": "2024-12-01T00:00:00Z",
                "initialValue": 150.0,
                "id": "future_002"
            },
            
            # Edge cases
            {
                "statement": "Gold price will stay above $2000/oz through 2024",
                "end_date": "2024-12-31T23:59:59Z",
                "createdAt": "2024-01-01T00:00:00Z",
                "initialValue": 2050.0,
                "direction": "maintain",
                "id": "edge_001"
            },
            {
                "statement": "S&P 500 will hit 5000 points",
                "end_date": None,  # No explicit end date
                "createdAt": "2024-06-01T00:00:00Z",
                "initialValue": 4800.0,
                "id": "edge_002"
            }
        ]
    
    def get_unresolved_statements(self) -> List[Dict[str, Any]]:
        """
        Get statements that haven't been resolved yet.
        
        Returns:
            List of unresolved statement dictionaries.
        """
        # In a real implementation, this would filter for unresolved only
        # For testing, return all statements
        return self.statements
    
    def resolve_statement(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock resolve endpoint.
        
        Args:
            request: Request payload with statement details.
            
        Returns:
            Resolution response.
        """
        statement = request.get("statement", "")
        end_date = request.get("end_date")
        created_at = request.get("createdAt")
        initial_value = request.get("initialValue")
        
        # Check cache first
        cache_key = f"{statement}_{end_date}"
        if cache_key in self.resolve_cache:
            return self.resolve_cache[cache_key]
        
        # Mock resolution logic
        resolution = self._mock_resolve(statement, end_date)
        
        # Build response
        response = {
            "statement": statement,
            "resolution": resolution["resolution"],
            "confidence": resolution["confidence"],
            "summary": resolution["summary"],
            "target_date": end_date,
            "target_value": resolution.get("target_value"),
            "current_value": resolution.get("current_value"),
            "direction_inferred": resolution.get("direction"),
            "sources": resolution.get("sources", [])
        }
        
        # Cache the result
        self.resolve_cache[cache_key] = response
        
        return response
    
    def _mock_resolve(self, statement: str, end_date: str) -> Dict[str, Any]:
        """
        Mock resolution logic based on statement patterns.
        
        Args:
            statement: The prediction statement.
            end_date: The deadline for the prediction.
            
        Returns:
            Resolution data.
        """
        now = datetime.now(timezone.utc)
        
        # Parse end date if provided
        if end_date:
            try:
                deadline = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                is_past = deadline < now
            except:
                is_past = False
        else:
            is_past = False
        
        # Mock different resolution scenarios
        if "Bitcoin will cross $50,000" in statement and is_past:
            return {
                "resolution": "TRUE",
                "confidence": 99.5,
                "summary": "Bitcoin successfully crossed $50,000 on February 15, 2024.",
                "target_value": 50000.0,
                "current_value": 65000.0,
                "direction": "increase",
                "sources": ["CoinGecko", "Binance"]
            }
        
        elif "Ethereum will reach $10,000" in statement and is_past:
            return {
                "resolution": "FALSE",
                "confidence": 99.0,
                "summary": "Ethereum peaked at $3,800 but did not reach $10,000 by the deadline.",
                "target_value": 10000.0,
                "current_value": 3500.0,
                "direction": "increase",
                "sources": ["CoinMarketCap", "Kraken"]
            }
        
        elif not is_past:
            # Future predictions are PENDING
            return {
                "resolution": "PENDING",
                "confidence": 95.0,
                "summary": "The prediction deadline has not yet passed.",
                "target_value": self._extract_target_value(statement),
                "current_value": random.uniform(50000, 70000) if "Bitcoin" in statement else random.uniform(2000, 4000),
                "direction": "increase",
                "sources": ["Market data"]
            }
        
        else:
            # Default resolution for past statements
            resolution = random.choice(["TRUE", "FALSE"])
            return {
                "resolution": resolution,
                "confidence": random.uniform(85, 99),
                "summary": f"Statement resolved as {resolution} based on historical data.",
                "sources": ["Historical data"]
            }
    
    def _extract_target_value(self, statement: str) -> Optional[float]:
        """Extract target value from statement."""
        import re
        
        # Look for dollar amounts
        match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', statement)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                return float(value_str)
            except:
                pass
        
        return None


# Global mock instance for testing
mock_api = MockDegenBrainAPI()


def get_mock_statements() -> List[Dict[str, Any]]:
    """Get mock statements for testing."""
    return mock_api.get_unresolved_statements()


def mock_resolve_statement(request: Dict[str, Any]) -> Dict[str, Any]:
    """Mock resolve endpoint for testing."""
    return mock_api.resolve_statement(request)