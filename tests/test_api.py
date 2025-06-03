"""
Tests for API client functionality.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import os

from shared.api import DegenBrainAPIClient, fetch_statements, get_task
from shared.types import Statement, Resolution
from shared.config import reset_config
from tests.mock_api import get_mock_statements, mock_resolve_statement


class TestDegenBrainAPIClient:
    """Test DegenBrainAPIClient class."""
    
    @pytest.fixture
    def client(self):
        """Create API client instance."""
        return DegenBrainAPIClient(api_url="https://test.api.com")
    
    @pytest.fixture
    def mock_statements(self):
        """Get mock statements."""
        return get_mock_statements()
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization."""
        client = DegenBrainAPIClient(api_url="https://test.api.com", timeout=60)
        assert client.api_url == "https://test.api.com"
        assert client.timeout == 60
        await client.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with DegenBrainAPIClient(api_url="https://test.api.com") as client:
            assert client.client is not None
        # Client should be closed after context
    
    @pytest.mark.asyncio
    async def test_fetch_statements(self, client):
        """Test fetching statements."""
        # For now, this uses simulated data
        statements = await client.fetch_statements()
        
        assert isinstance(statements, list)
        assert len(statements) > 0
        assert all(isinstance(stmt, Statement) for stmt in statements)
        
        # Check first statement
        stmt = statements[0]
        assert stmt.statement is not None
        assert stmt.end_date is not None
        assert stmt.createdAt is not None
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_resolve_statement(self, client, mock_statements):
        """Test resolving a statement."""
        # Create a statement from mock data
        stmt_data = mock_statements[0]
        statement = Statement.from_dict(stmt_data)
        
        # Mock the HTTP response
        mock_response = mock_resolve_statement({
            "statement": statement.statement,
            "createdAt": statement.createdAt,
            "initialValue": statement.initialValue,
            "direction": statement.direction,
            "end_date": statement.end_date
        })
        
        with patch.object(client.client, 'post') as mock_post:
            # Create mock response object
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            # Configure mock to return async response
            async def async_post(*args, **kwargs):
                return mock_resp
            
            mock_post.side_effect = async_post
            
            # Call resolve_statement
            result = await client.resolve_statement(statement)
            
            # Verify result
            assert result["resolution"] in ["TRUE", "FALSE", "PENDING"]
            assert "confidence" in result
            assert "summary" in result
            assert result["statement"] == statement.statement
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_resolve_statement_error_handling(self, client):
        """Test error handling in resolve_statement."""
        statement = Statement(
            statement="Test statement",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        # Test HTTP error
        with patch.object(client.client, 'post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=MagicMock(status_code=500, text="Internal Server Error")
            )
            
            async def async_post(*args, **kwargs):
                return mock_resp
            
            mock_post.side_effect = async_post
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.resolve_statement(statement)
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, client):
        """Test retry logic on network errors."""
        statement = Statement(
            statement="Test statement",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        # Mock successful response after retries
        mock_response = {
            "statement": statement.statement,
            "resolution": "PENDING",
            "confidence": 95.0,
            "summary": "Test successful after retry"
        }
        
        with patch.object(client.client, 'post') as mock_post:
            # First two calls fail, third succeeds
            mock_resp_success = MagicMock()
            mock_resp_success.json.return_value = mock_response
            mock_resp_success.raise_for_status = MagicMock()
            
            call_count = 0
            
            async def async_post(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise httpx.RequestError("Network error")
                return mock_resp_success
            
            mock_post.side_effect = async_post
            
            # Should succeed after retries
            result = await client.resolve_statement(statement)
            assert result["resolution"] == "PENDING"
            assert call_count == 3  # Two failures + one success
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_post_consensus(self, client):
        """Test posting consensus results."""
        consensus = {
            "resolution": "TRUE",
            "confidence": 95.0,
            "miner_scores": {1: 0.9, 2: 0.8}
        }
        
        # Currently returns True (placeholder)
        result = await client.post_consensus("stmt_001", consensus)
        assert result is True
        
        await client.close()


class TestModuleFunctions:
    """Test module-level API functions."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_config()
        # Set minimal required env vars
        os.environ["WALLET_NAME"] = "test_wallet"
        os.environ["HOTKEY_NAME"] = "test_hotkey"
        os.environ["API_URL"] = "https://test.api.com"
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_config()
        # Clean up env vars
        for key in ["WALLET_NAME", "HOTKEY_NAME", "API_URL"]:
            os.environ.pop(key, None)
    
    @pytest.mark.asyncio
    async def test_fetch_statements_function(self):
        """Test fetch_statements module function."""
        statements = await fetch_statements()
        assert isinstance(statements, list)
        assert len(statements) > 0
        assert all(isinstance(stmt, Statement) for stmt in statements)
    
    @pytest.mark.asyncio
    async def test_get_task_function(self):
        """Test get_task module function."""
        task = await get_task()
        
        if task is not None:
            assert isinstance(task, Statement)
            assert task.statement is not None
    
    @pytest.mark.asyncio
    async def test_get_task_error_handling(self):
        """Test get_task error handling."""
        with patch('shared.api.fetch_statements', side_effect=Exception("API Error")):
            task = await get_task()
            assert task is None  # Should return None on error