"""
Tests for validator components.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from validator.main import Validator, ValidatorStats
from validator.weights import WeightsCalculator
from shared.types import Statement, MinerResponse, Resolution, ValidationResult


class TestWeightsCalculator:
    """Test WeightsCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create a weights calculator."""
        return WeightsCalculator({
            "accuracy_weight": 0.4,
            "confidence_weight": 0.2,
            "consistency_weight": 0.3,
            "source_quality_weight": 0.1
        })
    
    @pytest.fixture
    def statement(self):
        """Create a test statement."""
        return Statement(
            statement="Bitcoin will reach $100,000",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
    
    @pytest.fixture
    def responses(self):
        """Create test miner responses."""
        return [
            MinerResponse(
                statement="Bitcoin will reach $100,000",
                resolution=Resolution.TRUE,
                confidence=90.0,
                summary="Strong bullish indicators",
                sources=["coingecko", "yahoo"],
                miner_uid=1
            ),
            MinerResponse(
                statement="Bitcoin will reach $100,000",
                resolution=Resolution.TRUE,
                confidence=85.0,
                summary="Market analysis supports this",
                sources=["coinmarketcap", "reuters"],
                miner_uid=2
            ),
            MinerResponse(
                statement="Bitcoin will reach $100,000",
                resolution=Resolution.FALSE,
                confidence=75.0,
                summary="Economic headwinds",
                sources=["bloomberg"],
                miner_uid=3
            )
        ]
    
    def test_calculator_initialization(self):
        """Test calculator initialization and weight normalization."""
        calculator = WeightsCalculator({
            "accuracy_weight": 2.0,
            "confidence_weight": 1.0,
            "consistency_weight": 1.5,
            "source_quality_weight": 0.5
        })
        
        # Should normalize to sum to 1.0
        total = (calculator.accuracy_weight + calculator.confidence_weight + 
                calculator.consistency_weight + calculator.source_quality_weight)
        assert abs(total - 1.0) < 0.001
    
    def test_calculate_consensus(self, calculator, responses):
        """Test consensus calculation."""
        consensus = calculator._calculate_consensus(responses)
        assert consensus == Resolution.TRUE  # Should be TRUE (2 vs 1)
    
    def test_calculate_consensus_empty(self, calculator):
        """Test consensus with no responses."""
        consensus = calculator._calculate_consensus([])
        assert consensus is None
    
    def test_calculate_scores(self, calculator, statement, responses):
        """Test score calculation."""
        scores = calculator.calculate_scores(statement, responses)
        
        # Should return scores for all miners
        assert len(scores) == 3
        assert 1 in scores and 2 in scores and 3 in scores
        
        # Scores should be normalized (sum to 1.0)
        total_score = sum(scores.values())
        assert abs(total_score - 1.0) < 0.001
        
        # Miners agreeing with consensus should score higher
        assert scores[1] > scores[3]  # UID 1 (TRUE) > UID 3 (FALSE)
        assert scores[2] > scores[3]  # UID 2 (TRUE) > UID 3 (FALSE)
    
    def test_accuracy_score(self, calculator):
        """Test accuracy scoring."""
        response_correct = MinerResponse(
            statement="Test", resolution=Resolution.TRUE, confidence=90.0,
            summary="Test", sources=[]
        )
        response_wrong = MinerResponse(
            statement="Test", resolution=Resolution.FALSE, confidence=90.0,
            summary="Test", sources=[]
        )
        response_pending = MinerResponse(
            statement="Test", resolution=Resolution.PENDING, confidence=50.0,
            summary="Test", sources=[]
        )
        
        # Correct answer should score 1.0
        assert calculator._calculate_accuracy_score(response_correct, Resolution.TRUE) == 1.0
        
        # Wrong answer should score 0.0
        assert calculator._calculate_accuracy_score(response_wrong, Resolution.TRUE) == 0.0
        
        # Pending should score 0.5
        assert calculator._calculate_accuracy_score(response_pending, Resolution.TRUE) == 0.5
    
    def test_confidence_score(self, calculator):
        """Test confidence scoring."""
        # High confidence on correct answer
        response_confident_correct = MinerResponse(
            statement="Test", resolution=Resolution.TRUE, confidence=95.0,
            summary="Test", sources=[]
        )
        assert calculator._calculate_confidence_score(response_confident_correct, Resolution.TRUE) == 0.95
        
        # High confidence on wrong answer (should be penalized)
        response_confident_wrong = MinerResponse(
            statement="Test", resolution=Resolution.FALSE, confidence=95.0,
            summary="Test", sources=[]
        )
        score = calculator._calculate_confidence_score(response_confident_wrong, Resolution.TRUE)
        assert abs(score - 0.05) < 0.001  # Use approximate comparison for floating point
    
    def test_source_score(self, calculator):
        """Test source quality scoring."""
        # No sources
        response_no_sources = MinerResponse(
            statement="Test", resolution=Resolution.TRUE, confidence=90.0,
            summary="Test", sources=[]
        )
        assert calculator._calculate_source_score(response_no_sources) == 0.0
        
        # Reliable sources
        response_reliable = MinerResponse(
            statement="Test", resolution=Resolution.TRUE, confidence=90.0,
            summary="Test", sources=["coingecko", "coinmarketcap", "yahoo"]
        )
        score = calculator._calculate_source_score(response_reliable)
        assert score > 0.5  # Should be high due to reliable sources
        
        # Unknown sources
        response_unknown = MinerResponse(
            statement="Test", resolution=Resolution.TRUE, confidence=90.0,
            summary="Test", sources=["unknown1", "unknown2"]
        )
        score_unknown = calculator._calculate_source_score(response_unknown)
        assert score > score_unknown  # Reliable should score higher
    
    def test_normalize_scores(self, calculator):
        """Test score normalization."""
        scores = {1: 0.5, 2: 1.0, 3: 0.3}
        normalized = calculator._normalize_scores(scores)
        
        # Should sum to 1.0
        assert abs(sum(normalized.values()) - 1.0) < 0.001
        
        # Relative ordering should be preserved
        assert normalized[2] > normalized[1] > normalized[3]
    
    def test_normalize_scores_empty(self, calculator):
        """Test normalizing empty scores."""
        result = calculator._normalize_scores({})
        assert result == {}
    
    def test_normalize_scores_all_zero(self, calculator):
        """Test normalizing when all scores are zero."""
        scores = {1: 0.0, 2: 0.0, 3: 0.0}
        normalized = calculator._normalize_scores(scores)
        
        # Should give equal weights
        for score in normalized.values():
            assert abs(score - 1/3) < 0.001
    
    def test_calculate_consensus_result(self, calculator, statement, responses):
        """Test full consensus calculation."""
        result = calculator.calculate_consensus(statement, responses)
        
        assert isinstance(result, ValidationResult)
        assert result.consensus_resolution == Resolution.TRUE
        assert result.total_responses == 3
        assert result.valid_responses == 3
        assert len(result.miner_scores) == 3
        assert result.consensus_confidence > 0


class TestValidator:
    """Test Validator class."""
    
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
    
    def test_validator_initialization(self, setup_env):
        """Test validator initialization."""
        validator = Validator()
        
        assert validator.running is False
        assert isinstance(validator.stats, ValidatorStats)
        assert validator.weights_calculator is not None
        assert validator.api_client is not None
    
    def test_validator_stats(self):
        """Test validator stats tracking."""
        stats = ValidatorStats()
        
        assert stats.statements_processed == 0
        assert stats.consensus_reached == 0
        assert stats.miners_queried == 0
        assert stats.weights_updated == 0
        assert stats.errors == 0
        
        # Test uptime calculation
        uptime = stats.get_uptime()
        assert uptime.total_seconds() >= 0
    
    @pytest.mark.asyncio
    async def test_validator_setup(self, setup_env):
        """Test validator setup."""
        validator = Validator()
        
        # Setup should complete without error (even without Bittensor)
        await validator.setup()
        
        await validator.shutdown()
    
    @pytest.mark.asyncio
    async def test_fetch_statements(self, setup_env):
        """Test fetching statements."""
        validator = Validator()
        
        # Mock the API client
        with patch.object(validator.api_client, 'fetch_statements') as mock_fetch:
            mock_statements = [
                Statement(
                    statement="Test statement",
                    end_date="2024-12-31T00:00:00Z",
                    createdAt="2024-01-01T00:00:00Z"
                )
            ]
            mock_fetch.return_value = mock_statements
            
            statements = await validator._fetch_statements()
            assert len(statements) == 1
            assert statements[0].statement == "Test statement"
        
        await validator.shutdown()
    
    @pytest.mark.asyncio
    async def test_query_miners_simulation(self, setup_env):
        """Test miner querying simulation."""
        validator = Validator()
        
        statement = Statement(
            statement="Bitcoin will reach $100,000",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        responses = await validator._query_miners(statement)
        
        # Should return multiple responses
        assert len(responses) >= 5
        assert len(responses) <= 10
        
        # All responses should be valid
        for response in responses:
            assert isinstance(response, MinerResponse)
            assert response.miner_uid is not None
            assert response.resolution in Resolution
            assert 0 <= response.confidence <= 100
        
        await validator.shutdown()
    
    @pytest.mark.asyncio
    async def test_process_statement(self, setup_env):
        """Test statement processing."""
        validator = Validator()
        
        statement = Statement(
            statement="Test statement",
            end_date="2024-12-31T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        # Mock post_consensus to avoid actual API calls
        with patch.object(validator.api_client, 'post_consensus') as mock_post:
            mock_post.return_value = True
            
            initial_consensus = validator.stats.consensus_reached
            await validator._process_statement(statement)
            
            # Stats should be updated (consensus_reached should increment)
            assert validator.stats.consensus_reached > initial_consensus
        
        await validator.shutdown()
    
    @pytest.mark.asyncio
    async def test_update_weights(self, setup_env):
        """Test weight updating."""
        validator = Validator()
        
        initial_updates = validator.stats.weights_updated
        await validator._update_weights()
        
        # Should increment update counter
        assert validator.stats.weights_updated == initial_updates + 1
        
        await validator.shutdown()
    
    def test_get_stats(self, setup_env):
        """Test getting validator stats."""
        validator = Validator()
        validator.stats.statements_processed = 10
        validator.stats.consensus_reached = 8
        
        stats = validator.get_stats()
        
        assert stats["statements_processed"] == 10
        assert stats["consensus_reached"] == 8
        assert stats["consensus_rate"] == 0.8
        assert "uptime" in stats
    
    @pytest.mark.asyncio
    async def test_validator_shutdown(self, setup_env):
        """Test validator shutdown."""
        validator = Validator()
        
        # Should shutdown gracefully
        await validator.shutdown()
        assert validator.running is False