# Shared Resolution API Architecture

## Overview

The DegenBrain subnet uses `api.subnet90.com` for validators to fetch pending statements. This document describes the resolution API that provides resolved statements to miners as a **temporary training mechanism** to help them develop and validate their resolution processes before transitioning to real-time market analysis.

## Current Architecture

```
Validators → api.subnet90.com/api/test/next-chunk → Get statement batches (every 15+ min)
Miners → api.subnet90.com/api/resolutions/{id} → Get resolved statements (when available)
       → Independent verification → Return responses to validators
```

## Benefits as Training Infrastructure

### 1. Miner Development Aid
- New miners can compare their resolution logic against known correct answers
- Identify weaknesses in their analysis before real market deployment
- Build confidence in their systems with verified test cases

### 2. Gradual Transition Path
- Phase 1: Use official resolutions to validate miner logic
- Phase 2: Miners develop independent verification capabilities  
- Phase 3: Pure real-time analysis without resolution assistance
- Phase 4: Miners handle completely novel statement types

### 3. Quality Assurance
- Validators can measure miner accuracy against ground truth
- Miners can self-assess their performance and improve
- Network can maintain quality standards during development

### 4. Network Stability
- Ensures subnet functionality while miners develop capabilities
- Provides baseline performance for comparison
- Reduces risk of poor consensus during early phases

## API Design

### Endpoint: GET /api/resolutions/{statement_id}
```json
{
  "statement_id": "858",
  "statement": "Will the betting favorite win the 2024 Belmont Stakes?",
  "resolution": "TRUE",
  "resolved_at": "2024-04-09T23:59:59Z",
  "confidence": 95.0,
  "evidence": {
    "sources": ["Verified Test Data"]
  },
  "reasoning": "The betting favorite won the 2024 Belmont Stakes."
}
```

**Example for Bitcoin price prediction:**
```json
{
  "statement_id": "296",
  "statement": "Will Bitcoin close above $50,000 by July 24, 2025?",
  "resolution": "TRUE", 
  "resolved_at": "2025-06-13T23:59:59Z",
  "confidence": 95.0,
  "evidence": {
    "sources": ["Verified Test Data"]
  },
  "reasoning": "Resolved early based on projected or actual price movement for Bitcoin."
}
```

**Note**: With the protocol update, miners now receive the `statement_id` from validators, making it easy to query this endpoint.

### Endpoint: POST /api/resolve
```json
// Request
{
  "statement": "Bitcoin will reach $100,000 by December 31, 2024",
  "end_date": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-01T00:00:00Z"
}

// Response
{
  "resolution": "FALSE",
  "confidence": 99.5,
  "reasoning": "Bitcoin closed at $95,432.21 on the deadline"
}
```

## Implementation Considerations

### 1. Rate Limiting
- Implement per-miner rate limits
- Different limits for validators vs miners
- Consider API key authentication for higher limits

### 2. Caching
- Cache resolved statements indefinitely
- Cache pending resolutions for short periods
- Use CDN for global distribution

### 3. Data Freshness
- Real-time updates for recently resolved statements
- Batch updates for historical data
- WebSocket support for live updates

### 4. Security
- Public read access for resolved statements
- No authentication required for basic queries
- Optional API keys for advanced features

## Evolution Timeline

### Phase 1: Training Mode (Current)
- Resolution API provides known answers for development
- Miners use hybrid mode to validate their logic
- Focus on building robust verification systems

### Phase 2: Mixed Statements
- Introduce new statements without pre-resolved answers
- Miners must provide independent analysis for unknowns
- Resolution API becomes backup validation tool

### Phase 3: Real-Time Markets
- Transition to live prediction markets
- No pre-resolved data available
- Miners rely entirely on independent verification

### Phase 4: Novel Statement Types  
- Introduce completely new prediction categories
- Test miner adaptability and generalization
- Full decentralized consensus without training wheels

## Example Miner Implementation

```python
class ResolutionAPIMiner:
    def __init__(self, api_url="https://api.subnet90.com"):
        self.api_url = api_url
        self.session = aiohttp.ClientSession()
    
    async def verify_statement(self, synapse: DegenBrainSynapse) -> MinerResponse:
        # Check if we have a statement_id to query
        if synapse.statement_id:
            try:
                resolution = await self.get_resolution(synapse.statement_id)
                if resolution:
                    return self.convert_to_response(resolution)
            except:
                pass
        
        # Fall back to independent verification
        return await self.verify_independently(synapse)
    
    async def get_resolution(self, statement_id: str):
        async with self.session.get(f"{self.api_url}/api/resolutions/{statement_id}") as resp:
            if resp.status == 200:
                return await resp.json()
        return None
```

## Development Considerations

1. **Scoring Evolution**: Gradually reduce rewards for API-reliant responses
2. **Transition Metrics**: Track miner independence and accuracy over time  
3. **New Statement Injection**: Regularly introduce statements without resolutions
4. **Deprecation Timeline**: Clear communication about API phase-out schedule

## Conclusion

The resolution API serves as crucial training infrastructure for the subnet's evolution toward fully independent prediction market analysis. By providing known correct answers initially, it enables miners to develop and validate their resolution capabilities before transitioning to real-time market analysis. This approach ensures network stability while fostering genuine decentralized intelligence rather than permanent reliance on centralized resolution.