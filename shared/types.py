"""
Core data types for the DegenBrain subnet.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from enum import Enum
import hashlib
import json
from pydantic import BaseModel, Field, validator


class Resolution(str, Enum):
    """Possible statement resolutions."""
    TRUE = "TRUE"
    FALSE = "FALSE"
    PENDING = "PENDING"


class Direction(str, Enum):
    """Market direction for predictions."""
    INCREASE = "increase"
    DECREASE = "decrease"
    NEUTRAL = "neutral"


@dataclass
class Statement:
    """
    Represents a prediction statement from DegenBrain API.
    """
    statement: str
    end_date: str  # ISO format: "2024-12-31T23:59:00Z"
    createdAt: str  # ISO format
    initialValue: Optional[float] = None
    direction: Optional[str] = None
    id: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "statement": self.statement,
            "end_date": self.end_date,
            "createdAt": self.createdAt,
            "initialValue": self.initialValue,
            "direction": self.direction,
            "id": self.id,
            "category": self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Statement":
        """Create Statement from dictionary."""
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if statement deadline has passed."""
        try:
            end_datetime = datetime.fromisoformat(self.end_date.replace('Z', '+00:00'))
            return datetime.now(end_datetime.tzinfo) > end_datetime
        except:
            return False


class MinerResponse(BaseModel):
    """
    Structured response from a miner.
    Uses Pydantic for validation.
    """
    statement: str
    resolution: Resolution
    confidence: float = Field(ge=0, le=100)  # 0-100
    summary: str
    sources: List[str] = Field(default_factory=list)
    reasoning: str = ""
    target_date: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    direction_inferred: Optional[str] = None
    proof_hash: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    miner_uid: Optional[int] = None
    
    @validator('sources')
    def validate_sources(cls, v):
        """Ensure sources list has reasonable size."""
        if len(v) > 10:
            return v[:10]  # Limit to 10 sources
        return v
    
    @validator('summary')
    def validate_summary(cls, v):
        """Ensure summary is not too long."""
        if len(v) > 1000:
            return v[:1000] + "..."
        return v
    
    def generate_proof_hash(self) -> str:
        """Generate a proof hash from response data."""
        data = {
            "statement": self.statement,
            "resolution": self.resolution.value,
            "confidence": self.confidence,
            "sources": self.sources,
            "timestamp": self.timestamp
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if response meets minimum requirements."""
        return (
            self.resolution in Resolution and
            0 <= self.confidence <= 100 and
            len(self.summary) > 0 and
            len(self.sources) > 0
        )


@dataclass
class ValidationResult:
    """
    Result of validating miner responses.
    """
    consensus_resolution: Resolution
    consensus_confidence: float
    total_responses: int
    valid_responses: int
    miner_scores: Dict[int, float] = field(default_factory=dict)
    consensus_sources: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/storage."""
        return {
            "consensus_resolution": self.consensus_resolution.value,
            "consensus_confidence": self.consensus_confidence,
            "total_responses": self.total_responses,
            "valid_responses": self.valid_responses,
            "miner_scores": self.miner_scores,
            "consensus_sources": self.consensus_sources,
            "timestamp": self.timestamp
        }
    
    def get_consensus_summary(self) -> str:
        """Generate a summary of the consensus."""
        return (
            f"Consensus: {self.consensus_resolution.value} "
            f"(confidence: {self.consensus_confidence:.1f}%) "
            f"based on {self.valid_responses}/{self.total_responses} responses"
        )


@dataclass 
class MinerInfo:
    """
    Information about a miner in the subnet.
    """
    uid: int
    hotkey: str
    stake: float
    last_update: int
    ip: str
    port: int
    is_active: bool = True
    success_rate: float = 0.0
    total_requests: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "uid": self.uid,
            "hotkey": self.hotkey,
            "stake": self.stake,
            "last_update": self.last_update,
            "ip": self.ip,
            "port": self.port,
            "is_active": self.is_active,
            "success_rate": self.success_rate,
            "total_requests": self.total_requests
        }


@dataclass
class SubnetConfig:
    """
    Configuration for subnet operations.
    """
    wallet_name: str
    hotkey_name: str
    network: str
    subnet_uid: int
    api_url: str
    validator_id: str = "default_validator"
    
    # Validator settings
    validator_port: int = 8090
    query_timeout: int = 60
    min_miners_required: int = 3
    consensus_threshold: float = 0.7
    
    # Miner settings
    miner_agent: str = "hybrid"
    miner_port: int = 8091
    verification_timeout: int = 30
    cache_duration: int = 300
    
    # Performance settings
    max_concurrent_requests: int = 10
    request_rate_limit: int = 100
    response_cache_size: int = 1000
    
    @classmethod
    def from_env(cls, env_dict: dict) -> "SubnetConfig":
        """Create config from environment variables."""
        return cls(
            wallet_name=env_dict.get("WALLET_NAME", "brain"),
            hotkey_name=env_dict.get("HOTKEY_NAME", "default"),
            network=env_dict.get("NETWORK", "finney"),
            subnet_uid=int(env_dict.get("SUBNET_UID", "90")),
            api_url=env_dict.get("API_URL", "https://api.subnet90.com"),
            validator_id=env_dict.get("VALIDATOR_ID", "default_validator"),
            validator_port=int(env_dict.get("VALIDATOR_PORT", "8090")),
            query_timeout=int(env_dict.get("QUERY_TIMEOUT", "60")),
            min_miners_required=int(env_dict.get("MIN_MINERS_REQUIRED", "3")),
            consensus_threshold=float(env_dict.get("CONSENSUS_THRESHOLD", "0.7")),
            miner_agent=env_dict.get("MINER_AGENT", "hybrid"),
            miner_port=int(env_dict.get("MINER_PORT", "8091")),
            verification_timeout=int(env_dict.get("VERIFICATION_TIMEOUT", "30")),
            cache_duration=int(env_dict.get("CACHE_DURATION", "300")),
            max_concurrent_requests=int(env_dict.get("MAX_CONCURRENT_REQUESTS", "10")),
            request_rate_limit=int(env_dict.get("REQUEST_RATE_LIMIT", "100")),
            response_cache_size=int(env_dict.get("RESPONSE_CACHE_SIZE", "1000"))
        )