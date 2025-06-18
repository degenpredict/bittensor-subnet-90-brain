"""
API client for DegenBrain resolve endpoint.
"""
import asyncio
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import structlog
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from shared.types import Statement, MinerResponse, Resolution
from shared.config import get_config


logger = structlog.get_logger()


class DegenBrainAPIClient:
    """
    Client for interacting with DegenBrain API.
    """
    
    def __init__(self, api_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize API client.
        
        Args:
            api_url: Base URL for the API. If None, uses config.
            timeout: Request timeout in seconds.
        """
        if api_url:
            self.api_url = api_url
        else:
            config = get_config()
            self.api_url = config.api_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Rate limiting for test endpoint (15 minute minimum between calls)
        self._last_fetch_time = 0
        self._min_fetch_interval = 15 * 60  # 15 minutes in seconds
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    async def fetch_statements(self) -> List[Statement]:
        """
        Fetch pending statements from brain-api.
        
        Fetches from /api/test/next-chunk endpoint with rate limiting.
        This endpoint can only be called once every 15 minutes.
        
        Returns:
            List of Statement objects to resolve.
        """
        try:
            # Check rate limiting
            current_time = time.time()
            time_since_last_fetch = current_time - self._last_fetch_time
            
            if time_since_last_fetch < self._min_fetch_interval:
                time_remaining = self._min_fetch_interval - time_since_last_fetch
                logger.debug("Rate limited - skipping fetch", 
                           time_remaining_minutes=time_remaining / 60)
                return []
            
            logger.info("Fetching next chunk from brain-api", api_url=self.api_url)
            
            # Get validator ID from config or generate one
            config = get_config()
            validator_id = getattr(config, 'validator_id', 'default_validator')
            
            # Fetch next chunk from brain-api with required validator_id  
            response = await self.client.get(
                f"{self.api_url}/api/test/next-chunk",
                params={"validator_id": validator_id}
            )
            response.raise_for_status()
            
            # Update last fetch time on successful request
            self._last_fetch_time = current_time
            
            data = response.json()
            chunk_id = data.get("chunk_id")
            statements_data = data.get("statements", [])
            
            logger.info("Received statement chunk", 
                       chunk_id=chunk_id,
                       count=len(statements_data))
            
            # Convert brain-api statement format to Statement objects
            statements = []
            for statement_data in statements_data:
                statement_obj = Statement(
                    id=statement_data["id"],
                    statement=statement_data["statement"],
                    end_date=statement_data["end_date"],
                    createdAt=statement_data["createdAt"],
                    initialValue=statement_data.get("initialValue"),
                    direction=statement_data.get("direction"),
                    category=statement_data.get("category")
                )
                statements.append(statement_obj)
            
            logger.info("Fetched pending statements", count=len(statements), api_url=self.api_url)
            return statements
            
        except httpx.HTTPStatusError as e:
            logger.error("API returned error status", 
                        status_code=e.response.status_code,
                        detail=e.response.text,
                        api_url=self.api_url)
            if e.response.status_code == 429:
                logger.warning("Rate limited by API - will retry in next cycle")
                # Don't update last_fetch_time on rate limit so we retry sooner
                return []
            raise
        except Exception as e:
            logger.error("Failed to fetch statements", error=str(e), api_url=self.api_url)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    async def resolve_statement(self, statement: Statement) -> Dict[str, Any]:
        """
        Call the resolve endpoint to get resolution for a statement.
        
        Args:
            statement: Statement to resolve.
            
        Returns:
            Resolution data from the API.
        """
        try:
            # Build request payload
            payload = {
                "statement": statement.statement,
                "createdAt": statement.createdAt,
                "initialValue": statement.initialValue,
                "direction": statement.direction,
                "end_date": statement.end_date
            }
            
            logger.info("Resolving statement via API", 
                       statement=statement.statement[:50] + "...",
                       endpoint=f"{self.api_url}/resolve")
            
            # Make API call
            response = await self.client.post(
                f"{self.api_url}/resolve",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Statement resolved", 
                       resolution=result.get("resolution"),
                       confidence=result.get("confidence"))
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error("API returned error status", 
                        status_code=e.response.status_code,
                        detail=e.response.text)
            raise
        except Exception as e:
            logger.error("Failed to resolve statement", error=str(e))
            raise
    
    async def submit_miner_responses(self, statement_id: str, validator_id: str, miner_responses: List[MinerResponse]) -> bool:
        """
        Submit miner responses to brain-api.
        
        Posts the consensus results from subnet validators back to brain-api
        at /api/markets/{statement_id}/responses endpoint.
        
        Args:
            statement_id: ID of the statement/market.
            validator_id: ID of the validator submitting responses.
            miner_responses: List of miner responses from the subnet.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert MinerResponse objects to brain-api format
            formatted_responses = []
            for response in miner_responses:
                formatted_responses.append({
                    "miner_id": str(response.miner_uid),
                    "resolution": response.resolution.value if hasattr(response.resolution, 'value') else str(response.resolution),
                    "confidence": float(response.confidence),
                    "summary": response.summary,
                    "sources": response.sources
                })
            
            # Build submission payload
            submission = {
                "validator_id": validator_id,
                "miner_responses": formatted_responses
            }
            
            logger.info("Submitting miner responses to brain-api", 
                       statement_id=statement_id,
                       validator_id=validator_id,
                       miner_count=len(miner_responses),
                       api_url=self.api_url)
            
            # Submit to brain-api
            response = await self.client.post(
                f"{self.api_url}/api/markets/{statement_id}/responses",
                json=submission
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Successfully submitted responses", 
                       statement_id=statement_id,
                       official_resolution=result.get("official_resolution"),
                       miner_responses_stored=result.get("miner_responses_stored"))
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error("API returned error status during submission", 
                        status_code=e.response.status_code,
                        detail=e.response.text,
                        statement_id=statement_id)
            return False
        except Exception as e:
            logger.error("Failed to submit miner responses", 
                        statement_id=statement_id,
                        error=str(e))
            return False

    async def post_consensus(self, statement_id: str, consensus: Dict[str, Any]) -> bool:
        """
        Post consensus result back to DegenBrain (legacy method).
        
        This method is kept for backward compatibility.
        Use submit_miner_responses() for new implementations.
        
        Args:
            statement_id: ID of the statement.
            consensus: Consensus data to post.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            logger.info("Posted consensus result (legacy method)", 
                       statement_id=statement_id,
                       resolution=consensus.get("resolution"))
            return True
            
        except Exception as e:
            logger.error("Failed to post consensus", 
                        statement_id=statement_id,
                        error=str(e))
            return False


# Module-level functions for compatibility with README examples

async def fetch_statements() -> List[Statement]:
    """
    Fetch unresolved statements from DegenBrain API.
    
    Returns:
        List of Statement objects.
    """
    async with DegenBrainAPIClient() as client:
        return await client.fetch_statements()


async def send_to_miners(statement: Statement, miner_responses: List[MinerResponse]) -> List[MinerResponse]:
    """
    This is a placeholder that will be implemented in the validator module.
    The actual implementation will use Bittensor to query miners.
    
    Args:
        statement: Statement to send to miners.
        miner_responses: This parameter is just for interface compatibility.
        
    Returns:
        List of miner responses.
    """
    # This will be implemented in validator/main.py
    # For now, return empty list
    return []


def score_and_set_weights(subtensor, wallet, responses: List[MinerResponse]) -> None:
    """
    This is a placeholder that will be implemented in the validator module.
    The actual implementation will calculate scores and set weights on chain.
    
    Args:
        subtensor: Bittensor subtensor instance.
        wallet: Bittensor wallet instance.
        responses: List of miner responses.
    """
    # This will be implemented in validator/weights.py
    pass


async def get_task() -> Optional[Statement]:
    """
    Get a task for miner to process.
    
    This is a simplified version that fetches statements directly.
    In production, miners would receive tasks from validators.
    
    Returns:
        A Statement to process, or None if no tasks available.
    """
    try:
        statements = await fetch_statements()
        return statements[0] if statements else None
    except Exception as e:
        logger.error("Failed to get task", error=str(e))
        return None


async def run_agent(task: Statement) -> MinerResponse:
    """
    Run the default agent to verify a statement.
    
    This function creates a temporary agent instance to process
    a single statement. For production use, miners should use
    the Miner class which maintains agent state.
    
    Args:
        task: Statement to verify.
        
    Returns:
        MinerResponse with verification result.
    """
    from miner.agents.dummy_agent import DummyAgent
    
    # Create a default agent
    agent = DummyAgent({
        "accuracy": 0.8,
        "delay": 0.1,
        "confidence_range": (70, 95)
    })
    
    # Process the statement
    return await agent.process_statement(task)


async def submit_response(response: MinerResponse) -> bool:
    """
    This is a placeholder that will be implemented in the miner module.
    The actual implementation will submit the response to the validator.
    
    Args:
        response: MinerResponse to submit.
        
    Returns:
        True if submission successful, False otherwise.
    """
    # This will be implemented in miner/main.py
    return True