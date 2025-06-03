"""
Unit tests for shared data types.
"""
import pytest
import json
from datetime import datetime, timezone, timedelta
from shared.types import (
    Statement, 
    MinerResponse, 
    ValidationResult,
    MinerInfo,
    Resolution,
    Direction,
    SubnetConfig
)


class TestStatement:
    """Test Statement dataclass."""
    
    def test_statement_creation(self):
        """Test creating a statement."""
        stmt = Statement(
            statement="Bitcoin will cross $100,000 by December 31, 2024",
            end_date="2024-12-31T23:59:00Z",
            createdAt="2023-01-15T12:00:00Z",
            initialValue=21500.75,
            direction="increase"
        )
        
        assert stmt.statement == "Bitcoin will cross $100,000 by December 31, 2024"
        assert stmt.end_date == "2024-12-31T23:59:00Z"
        assert stmt.initialValue == 21500.75
        assert stmt.direction == "increase"
    
    def test_statement_serialization(self):
        """Test converting statement to/from dict."""
        stmt = Statement(
            statement="ETH > $5000",
            end_date="2024-06-30T00:00:00Z",
            createdAt="2024-01-01T00:00:00Z"
        )
        
        # To dict
        data = stmt.to_dict()
        assert data["statement"] == "ETH > $5000"
        assert data["end_date"] == "2024-06-30T00:00:00Z"
        assert data["initialValue"] is None
        
        # From dict
        stmt2 = Statement.from_dict(data)
        assert stmt2.statement == stmt.statement
        assert stmt2.end_date == stmt.end_date
    
    def test_statement_is_expired(self):
        """Test checking if statement is expired."""
        # Future date - not expired
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        stmt1 = Statement(
            statement="Test",
            end_date=future,
            createdAt="2024-01-01T00:00:00Z"
        )
        assert not stmt1.is_expired()
        
        # Past date - expired
        past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        stmt2 = Statement(
            statement="Test",
            end_date=past,
            createdAt="2024-01-01T00:00:00Z"
        )
        assert stmt2.is_expired()


class TestMinerResponse:
    """Test MinerResponse model."""
    
    def test_response_validation(self):
        """Test creating valid miner response."""
        response = MinerResponse(
            statement="BTC > $100k",
            resolution=Resolution.FALSE,
            confidence=95.5,
            summary="Bitcoin peaked at $98k",
            sources=["CoinGecko", "Yahoo Finance"]
        )
        
        assert response.resolution == Resolution.FALSE
        assert response.confidence == 95.5
        assert len(response.sources) == 2
        assert response.is_valid()
    
    def test_invalid_response_rejection(self):
        """Test validation rejects invalid responses."""
        # Invalid confidence (>100)
        with pytest.raises(ValueError):
            MinerResponse(
                statement="Test",
                resolution=Resolution.TRUE,
                confidence=150,  # Invalid
                summary="Test",
                sources=["Test"]
            )
        
        # Invalid confidence (<0)
        with pytest.raises(ValueError):
            MinerResponse(
                statement="Test",
                resolution=Resolution.TRUE,
                confidence=-10,  # Invalid
                summary="Test",
                sources=["Test"]
            )
    
    def test_response_proof_hash(self):
        """Test proof hash generation."""
        response = MinerResponse(
            statement="BTC > $100k",
            resolution=Resolution.FALSE,
            confidence=95.5,
            summary="Bitcoin peaked at $98k",
            sources=["CoinGecko"]
        )
        
        hash1 = response.generate_proof_hash()
        assert len(hash1) == 64  # SHA256 hex length
        
        # Same data should produce same hash
        hash2 = response.generate_proof_hash()
        assert hash1 == hash2
        
        # Different data should produce different hash
        response.confidence = 90.0
        hash3 = response.generate_proof_hash()
        assert hash1 != hash3
    
    def test_source_limit(self):
        """Test that sources are limited to 10."""
        sources = [f"Source{i}" for i in range(20)]
        response = MinerResponse(
            statement="Test",
            resolution=Resolution.PENDING,
            confidence=50,
            summary="Test",
            sources=sources
        )
        
        assert len(response.sources) == 10
        assert response.sources[0] == "Source0"
        assert response.sources[9] == "Source9"
    
    def test_summary_truncation(self):
        """Test that long summaries are truncated."""
        long_summary = "x" * 2000
        response = MinerResponse(
            statement="Test",
            resolution=Resolution.TRUE,
            confidence=80,
            summary=long_summary,
            sources=["Test"]
        )
        
        assert len(response.summary) == 1003  # 1000 + "..."
        assert response.summary.endswith("...")


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult(
            consensus_resolution=Resolution.TRUE,
            consensus_confidence=85.5,
            total_responses=10,
            valid_responses=8,
            miner_scores={1: 0.9, 2: 0.8, 3: 0.7}
        )
        
        assert result.consensus_resolution == Resolution.TRUE
        assert result.consensus_confidence == 85.5
        assert result.total_responses == 10
        assert result.valid_responses == 8
        assert len(result.miner_scores) == 3
    
    def test_consensus_summary(self):
        """Test generating consensus summary."""
        result = ValidationResult(
            consensus_resolution=Resolution.FALSE,
            consensus_confidence=92.3,
            total_responses=15,
            valid_responses=12
        )
        
        summary = result.get_consensus_summary()
        assert "FALSE" in summary
        assert "92.3%" in summary
        assert "12/15" in summary
    
    def test_validation_result_serialization(self):
        """Test converting result to dict."""
        result = ValidationResult(
            consensus_resolution=Resolution.PENDING,
            consensus_confidence=60.0,
            total_responses=5,
            valid_responses=3,
            consensus_sources=["API1", "API2"]
        )
        
        data = result.to_dict()
        assert data["consensus_resolution"] == "PENDING"
        assert data["consensus_confidence"] == 60.0
        assert len(data["consensus_sources"]) == 2


class TestMinerInfo:
    """Test MinerInfo dataclass."""
    
    def test_miner_info_creation(self):
        """Test creating miner info."""
        info = MinerInfo(
            uid=42,
            hotkey="5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            stake=1000.0,
            last_update=1234567890,
            ip="192.168.1.100",
            port=8091
        )
        
        assert info.uid == 42
        assert info.stake == 1000.0
        assert info.is_active
        assert info.success_rate == 0.0
    
    def test_miner_info_serialization(self):
        """Test converting miner info to dict."""
        info = MinerInfo(
            uid=1,
            hotkey="test_hotkey",
            stake=500.5,
            last_update=1000000,
            ip="127.0.0.1",
            port=8080,
            success_rate=0.95,
            total_requests=100
        )
        
        data = info.to_dict()
        assert data["uid"] == 1
        assert data["stake"] == 500.5
        assert data["success_rate"] == 0.95
        assert data["total_requests"] == 100


class TestSubnetConfig:
    """Test SubnetConfig dataclass."""
    
    def test_config_from_env(self):
        """Test creating config from environment dict."""
        env = {
            "WALLET_NAME": "test_wallet",
            "HOTKEY_NAME": "test_hotkey",
            "NETWORK": "test",
            "SUBNET_UID": "90",
            "API_URL": "https://test.api.com",
            "CONSENSUS_THRESHOLD": "0.8",
            "MIN_MINERS_REQUIRED": "5"
        }
        
        config = SubnetConfig.from_env(env)
        assert config.wallet_name == "test_wallet"
        assert config.hotkey_name == "test_hotkey"
        assert config.network == "test"
        assert config.subnet_uid == 90
        assert config.consensus_threshold == 0.8
        assert config.min_miners_required == 5
    
    def test_config_defaults(self):
        """Test config uses defaults for missing values."""
        env = {
            "WALLET_NAME": "brain",
            "HOTKEY_NAME": "default",
            "NETWORK": "finney",
            "SUBNET_UID": "90",
            "API_URL": "https://api.test.com"
        }
        
        config = SubnetConfig.from_env(env)
        assert config.validator_port == 8090  # Default
        assert config.miner_agent == "hybrid"  # Default
        assert config.cache_duration == 300  # Default