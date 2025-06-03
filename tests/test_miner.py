"""
Tests for miner components.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone

from miner.agents.base_agent import BaseAgent
from miner.agents.dummy_agent import DummyAgent
from miner.main import Miner
from shared.types import Statement, MinerResponse, Resolution
from shared.api import run_agent


class TestBaseAgent:
    """Test BaseAgent abstract class."""
    
    def test_cannot_instantiate_base_agent(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent()
    
    class ConcreteAgent(BaseAgent):
        """Concrete implementation for testing."""
        async def verify_statement(self, statement: Statement) -> MinerResponse:
            return MinerResponse(
                statement=statement.statement,
                resolution=Resolution.TRUE,
                confidence=90.0,
                summary="Test response",
                sources=["test"]
            )
    
    @pytest.mark.asyncio
    async def test_process_statement(self):
        """Test process_statement wrapper."""
        agent = self.ConcreteAgent()
        statement = Statement(
            statement="Test statement",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        response = await agent.process_statement(statement)
        
        assert response.resolution == Resolution.TRUE
        assert response.confidence == 90.0
        assert response.proof_hash is not None  # Should generate hash
    
    @pytest.mark.asyncio
    async def test_process_statement_error_handling(self):
        """Test error handling in process_statement."""
        class ErrorAgent(BaseAgent):
            async def verify_statement(self, statement: Statement) -> MinerResponse:
                raise Exception("Test error")
        
        agent = ErrorAgent()
        statement = Statement(
            statement="Test statement",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        response = await agent.process_statement(statement)
        
        # Should return error response
        assert response.resolution == Resolution.PENDING
        assert response.confidence == 0.0
        assert "Error processing statement" in response.summary
    
    def test_validate_response(self):
        """Test response validation."""
        agent = self.ConcreteAgent()
        
        # Valid response
        valid_response = MinerResponse(
            statement="Test",
            resolution=Resolution.TRUE,
            confidence=90.0,
            summary="Test summary",
            sources=["source1"]
        )
        assert agent.validate_response(valid_response) is True
        
        # Test validation catches invalid responses
        # Create a response object directly to bypass Pydantic validation
        from unittest.mock import Mock
        invalid_response = Mock(spec=MinerResponse)
        invalid_response.statement = "Test"
        invalid_response.resolution = Resolution.TRUE
        invalid_response.confidence = 150.0  # Invalid
        invalid_response.summary = "Test summary"
        invalid_response.sources = ["source1"]
        invalid_response.is_valid = Mock(return_value=False)
        
        assert agent.validate_response(invalid_response) is False


class TestDummyAgent:
    """Test DummyAgent implementation."""
    
    @pytest.fixture
    def agent(self):
        """Create a dummy agent."""
        return DummyAgent({
            "accuracy": 0.9,
            "delay": 0,  # No delay for tests
            "confidence_range": (80, 95)
        })
    
    @pytest.mark.asyncio
    async def test_verify_statement_pending(self, agent):
        """Test verification of future statement (should be PENDING)."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        statement = Statement(
            statement="Bitcoin will reach $100,000",
            end_date=future_date,
            createdAt=datetime.now(timezone.utc).isoformat()
        )
        
        response = await agent.verify_statement(statement)
        
        assert response.resolution == Resolution.PENDING
        assert response.confidence >= 80 and response.confidence <= 95
        assert len(response.sources) >= 2
        assert response.target_value == 100000.0  # Should extract from statement
    
    @pytest.mark.asyncio
    async def test_verify_statement_past(self, agent):
        """Test verification of past statement."""
        past_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        statement = Statement(
            statement="Ethereum crossed $5,000",
            end_date=past_date,
            createdAt=(datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        )
        
        response = await agent.verify_statement(statement)
        
        assert response.resolution in [Resolution.TRUE, Resolution.FALSE]
        assert response.confidence >= 80 and response.confidence <= 95
        assert response.target_value == 5000.0
    
    def test_extract_target_value(self, agent):
        """Test target value extraction."""
        # Test various formats
        assert agent._extract_target_value("Bitcoin will reach $100,000") == 100000.0
        assert agent._extract_target_value("BTC to hit $50,000.50") == 50000.50
        assert agent._extract_target_value("Price will exceed 5000 dollars") == 5000.0
        assert agent._extract_target_value("S&P 500 will reach 4,500 points") == 4500.0
        assert agent._extract_target_value("No price mentioned") is None
    
    @pytest.mark.asyncio
    async def test_delay_configuration(self):
        """Test that delay configuration works."""
        agent = DummyAgent({"delay": 0.5})
        statement = Statement(
            statement="Test",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        start_time = asyncio.get_event_loop().time()
        await agent.verify_statement(statement)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        assert elapsed >= 0.5  # Should have delayed


class TestMiner:
    """Test Miner class."""
    
    @pytest.fixture
    def setup_env(self):
        """Set up test environment."""
        import os
        os.environ["WALLET_NAME"] = "test_wallet"
        os.environ["HOTKEY_NAME"] = "test_hotkey"
        os.environ["API_URL"] = "https://test.api.com"
        yield
        # Cleanup
        for key in ["WALLET_NAME", "HOTKEY_NAME", "API_URL"]:
            os.environ.pop(key, None)
    
    def test_miner_initialization(self, setup_env):
        """Test miner initialization."""
        miner = Miner()
        assert miner.agent is not None
        assert isinstance(miner.agent, DummyAgent)
        assert miner.tasks_processed == 0
        assert miner.running is False
    
    def test_miner_with_custom_agent(self, setup_env):
        """Test miner with custom agent."""
        custom_agent = DummyAgent({"accuracy": 1.0})
        miner = Miner(agent=custom_agent)
        assert miner.agent is custom_agent
    
    @pytest.mark.asyncio
    async def test_get_next_task(self, setup_env):
        """Test getting next task."""
        miner = Miner()
        
        # Mock get_task at the module level where it's imported
        with patch('miner.main.get_task') as mock_get_task:
            mock_statement = Statement(
                statement="Test statement",
                end_date="2024-12-31T00:00:00Z",
                createdAt="2024-01-01T00:00:00Z"
            )
            mock_get_task.return_value = mock_statement
            
            task = await miner._get_next_task()
            assert task == mock_statement
            mock_get_task.assert_called_once()
        
        await miner.shutdown()
    
    @pytest.mark.asyncio
    async def test_process_task(self, setup_env):
        """Test processing a task."""
        miner = Miner()
        statement = Statement(
            statement="Bitcoin will reach $100,000",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        response = await miner._process_task(statement)
        
        assert isinstance(response, MinerResponse)
        assert response.resolution in Resolution
        assert response.confidence >= 0 and response.confidence <= 100
        assert response.miner_uid is not None
        
        await miner.shutdown()
    
    def test_get_stats(self, setup_env):
        """Test getting miner stats."""
        miner = Miner()
        miner.tasks_processed = 5
        
        stats = miner.get_stats()
        
        assert stats["tasks_processed"] == 5
        assert "agent" in stats
        assert stats["is_running"] is False


class TestAPIFunctions:
    """Test API module miner functions."""
    
    @pytest.mark.asyncio
    async def test_run_agent(self):
        """Test run_agent function."""
        statement = Statement(
            statement="Test statement with $50,000 target",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        response = await run_agent(statement)
        
        assert isinstance(response, MinerResponse)
        assert response.resolution in Resolution
        assert response.confidence >= 0 and response.confidence <= 100
        assert response.target_value == 50000.0