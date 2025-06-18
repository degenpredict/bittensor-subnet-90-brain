"""
Resolution API client for miners to fetch resolved statements.
"""
import aiohttp
import structlog
from typing import Dict, Any, Optional
from datetime import datetime

logger = structlog.get_logger()


class ResolutionAPIClient:
    """
    Client for fetching resolved statements from the subnet API.
    """
    
    def __init__(self, api_url: str = "https://api.subnet90.com", timeout: int = 10):
        """
        Initialize the resolution API client.
        
        Args:
            api_url: Base URL for the resolution API
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def get_resolution(self, statement_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch resolution for a specific statement ID.
        
        Args:
            statement_id: The ID of the statement to resolve
            
        Returns:
            Resolution data if found, None otherwise
        """
        if not statement_id:
            return None
            
        try:
            # Create session if not in context manager
            if not self._session:
                self._session = aiohttp.ClientSession(timeout=self.timeout)
            
            url = f"{self.api_url}/api/resolutions/{statement_id}"
            logger.debug("Fetching resolution from API", url=url, statement_id=statement_id)
            
            async with self._session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Resolution found in API", 
                               statement_id=statement_id,
                               resolution=data.get("resolution"),
                               confidence=data.get("confidence"))
                    return data
                elif response.status == 404:
                    logger.debug("Resolution not found in API", statement_id=statement_id)
                    return None
                else:
                    logger.warning("API returned error status", 
                                 status=response.status,
                                 statement_id=statement_id)
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error("API request failed", 
                        error=str(e),
                        statement_id=statement_id,
                        api_url=self.api_url)
            return None
        except Exception as e:
            logger.error("Unexpected error fetching resolution",
                        error=str(e),
                        statement_id=statement_id)
            return None
    
    def convert_to_miner_response(self, api_response: Dict[str, Any], statement: str) -> Dict[str, Any]:
        """
        Convert API response format to miner response format.
        
        Args:
            api_response: Response from the resolution API
            statement: The original statement text
            
        Returns:
            Dictionary formatted for MinerResponse
        """
        evidence = api_response.get("evidence", {})
        
        return {
            "statement": statement,
            "resolution": api_response.get("resolution", "PENDING"),
            "confidence": float(api_response.get("confidence", 0.0)),
            "summary": f"Official resolution from subnet API: {api_response.get('reasoning', 'No reasoning provided')}",
            "sources": evidence.get("sources", ["subnet_api"]),
            "reasoning": api_response.get("reasoning", ""),
            "target_value": evidence.get("target_price"),  # May not be present in actual API
            "current_value": evidence.get("final_price"),  # May not be present in actual API
            "timestamp": api_response.get("resolved_at", datetime.utcnow().isoformat())
        }