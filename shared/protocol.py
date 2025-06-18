"""
Subnet 90 (DegenBrain) Protocol Definition

This module defines the communication protocol between validators and miners
for prediction market statement verification on Bittensor Subnet 90.
"""
from typing import Optional, List, Dict, Any
from enum import Enum
import time
from pydantic import BaseModel, Field, validator

try:
    import bittensor as bt
    BITTENSOR_AVAILABLE = True
except ImportError:
    BITTENSOR_AVAILABLE = False
    # Create mock bt.Synapse for development
    class _MockSynapse:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class _MockBT:
        Synapse = _MockSynapse
    
    bt = _MockBT()


class Resolution(str, Enum):
    """Valid resolution states for prediction statements."""
    TRUE = "TRUE"
    FALSE = "FALSE" 
    PENDING = "PENDING"


class DegenBrainSynapse(bt.Synapse):
    """
    Official Subnet 90 prediction market verification synapse.
    
    Used for validator ↔ miner communication to verify prediction market statements.
    Validators send statements to miners, miners respond with analysis.
    """
    
    # === REQUEST FIELDS (Validator → Miner) ===
    statement: str = ""
    end_date: str = ""
    created_at: str = ""
    statement_id: Optional[str] = None
    
    initial_value: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    
    # === RESPONSE FIELDS (Miner → Validator) ===
    resolution: str = "PENDING"
    confidence: float = 0.0
    summary: str = ""
    sources: List[str] = Field(default_factory=list)
    analysis_time: float = 0.0
    reasoning: str = ""
    target_value: Optional[float] = None
    
    # === METADATA ===
    protocol_version: str = "1.0"
    miner_version: str = ""
    
    # === VALIDATORS ===
    # Removed Pydantic validators for Bittensor 9.7.0 compatibility


class ProtocolValidator:
    """Utility class for protocol validation and conversion."""
    
    @staticmethod
    def is_valid_synapse(synapse: DegenBrainSynapse) -> bool:
        """Check if synapse has valid response fields."""
        try:
            # Check required response fields are populated
            if not synapse.resolution or synapse.resolution == "":
                return False
            
            # Validate resolution enum
            Resolution(synapse.resolution)
            
            # Check confidence is in valid range
            if not (0.0 <= synapse.confidence <= 100.0):
                return False
                
            return True
            
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def create_request_synapse(
        statement: str,
        end_date: str,
        created_at: Optional[str] = None,
        initial_value: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        statement_id: Optional[str] = None
    ) -> DegenBrainSynapse:
        """Create a request synapse with proper validation."""
        if created_at is None:
            from datetime import datetime
            created_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return DegenBrainSynapse(
            statement=statement,
            end_date=end_date,
            created_at=created_at,
            initial_value=initial_value,
            context=context or {},
            protocol_version="1.0",
            statement_id=statement_id
        )
    
    @staticmethod
    def create_response_synapse(
        request_synapse: DegenBrainSynapse,
        resolution: str,
        confidence: float,
        summary: str = "",
        sources: Optional[List[str]] = None,
        reasoning: str = "",
        target_value: Optional[float] = None,
        miner_version: str = ""
    ) -> DegenBrainSynapse:
        """Create a response synapse from a request."""
        # Start with request data
        response = DegenBrainSynapse(
            # Copy request fields
            statement=request_synapse.statement,
            end_date=request_synapse.end_date,
            created_at=request_synapse.created_at,
            initial_value=request_synapse.initial_value,
            context=request_synapse.context,
            protocol_version=request_synapse.protocol_version,
            
            # Add response fields
            resolution=resolution,
            confidence=confidence,
            summary=summary,
            sources=sources or [],
            reasoning=reasoning,
            target_value=target_value,
            miner_version=miner_version,
            analysis_time=0.0  # Will be set by miner
        )
        
        return response


class LegacyProtocolHandler:
    """Handle responses from miners using different protocols."""
    
    @staticmethod
    def try_parse_legacy_response(response) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse responses from miners using unknown protocols.
        Returns standardized dict or None if unparseable.
        """
        if response is None:
            return None
        
        try:
            # Try to extract common fields
            parsed = {
                "resolution": "PENDING",
                "confidence": 0.0,
                "summary": "Legacy response",
                "sources": [],
                "reasoning": "",
                "target_value": None
            }
            
            # Check for various field names miners might use
            if hasattr(response, 'resolution') and response.resolution:
                parsed["resolution"] = str(response.resolution).upper()
            elif hasattr(response, 'prediction') and response.prediction:
                # Convert prediction to resolution
                pred = str(response.prediction).upper()
                if pred in ["TRUE", "1", "YES", "POSITIVE"]:
                    parsed["resolution"] = "TRUE"
                elif pred in ["FALSE", "0", "NO", "NEGATIVE"]:
                    parsed["resolution"] = "FALSE"
            
            # Check for confidence fields
            if hasattr(response, 'confidence') and response.confidence is not None:
                parsed["confidence"] = float(response.confidence)
            elif hasattr(response, 'score') and response.score is not None:
                parsed["confidence"] = float(response.score) * 100  # Convert 0-1 to 0-100
            
            # Check for text fields
            if hasattr(response, 'summary') and response.summary:
                parsed["summary"] = str(response.summary)
            elif hasattr(response, 'explanation') and response.explanation:
                parsed["summary"] = str(response.explanation)
            
            return parsed
            
        except Exception:
            return None


# Export main classes for easy importing
__all__ = [
    'DegenBrainSynapse',
    'Resolution', 
    'ProtocolValidator',
    'LegacyProtocolHandler'
]