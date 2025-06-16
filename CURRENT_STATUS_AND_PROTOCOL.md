# Subnet 90 Current Status & Protocol Definition
*Date: June 4, 2025*

## 🔍 Current Status Summary

### ✅ What's Working
- **Subnet Exists**: Subnet 90 ("brain") live on Bittensor mainnet
- **You're the Owner**: Confirmed ownership (UID 0)
- **Infrastructure Deployed**: OVH KS-4 server with validator + 3 miners
- **Validator Connects**: Successfully connects to Bittensor network
- **API Integration**: Fetching real statements from DegenPredict API
- **Miners Registered**: All 4 nodes registered on Subnet 90

### ❌ Critical Issues
- **Zero Emissions**: No TAO flowing because no validators set weights
- **Protocol Mismatch**: Validator can't parse miner responses
- **No Weight Setting**: Validator never completes the cycle to set weights
- **Miners Don't Serve**: Your miners don't implement Bittensor axon server

---

## 🏗️ Infrastructure Status

### Server: OVH KS-4 (ns562812.ip-178-33-231.eu)
```
Validator: UID 171 (5EFa44) - ✗ Inactive but connecting
Miner 1:   UID 172 (5C8bXe) - ✗ Inactive  
Miner 2:   UID 173 (5G9EJv) - ✗ Inactive
Miner 3:   UID 204 (5Deg9Q) - ✓ Active (recently registered)
```

### Current Validator Behavior
```
2025-06-04 19:35:56 [info] Fetched statements count=2
2025-06-04 19:35:56 [info] Found active miners count=6
2025-06-04 19:36:57 [warning] Failed to parse response: 'None is not a valid Resolution'
2025-06-04 19:36:57 [info] Received miner responses valid_responses=0
```

**Problem**: Validator queries miners but gets unparseable responses.

---

## 🔄 Communication Flow Analysis

### Current Flow
```
1. Validator fetches statements from DegenPredict API ✅
2. Validator queries 6 active miners on network ✅  
3. Miners respond with unknown protocol ❌
4. Validator can't parse responses ❌
5. Validator never sets weights ❌
6. No emissions flow ❌
```

### Target Flow
```
1. Validator fetches statements from API ✅
2. Validator sends DegenBrainSynapse to miners ⭕
3. Miners analyze and respond with valid format ⭕
4. Validator calculates consensus ⭕
5. Validator sets weights based on performance ⭕
6. Emissions start flowing ⭕
```

---

## 📋 Protocol Specification

### DegenBrain Subnet 90 Communication Protocol

#### Synapse Definition
```python
class DegenBrainSynapse(bt.Synapse):
    """
    Official Subnet 90 prediction market verification synapse.
    Used for validator ↔ miner communication.
    """
    
    # === REQUEST FIELDS (Validator → Miner) ===
    statement: str                    # The prediction statement to verify
    end_date: str                    # ISO format: "2024-12-31T23:59:59Z" 
    created_at: str                  # ISO format: "2024-06-04T19:35:56Z"
    initial_value: Optional[float]   # Current value if numeric prediction
    context: Optional[Dict[str, Any]] # Additional context data
    
    # === RESPONSE FIELDS (Miner → Validator) ===
    resolution: str = "PENDING"      # "TRUE" | "FALSE" | "PENDING"
    confidence: float = 0.0          # Confidence level 0.0-100.0
    summary: str = ""                # Human-readable analysis summary
    sources: List[str] = []          # Source URLs used for verification
    analysis_time: float = 0.0       # Processing time in seconds
    reasoning: str = ""              # Step-by-step reasoning
    target_value: Optional[float] = None  # Predicted/actual value if numeric
    
    # === METADATA ===
    protocol_version: str = "1.0"    # Protocol version for compatibility
    miner_version: str = ""          # Miner software version
```

#### Example Communication

**Validator Request:**
```json
{
  "statement": "Bitcoin will cross $100,000 by December 31, 2024",
  "end_date": "2024-12-31T23:59:59Z",
  "created_at": "2024-06-04T19:35:56Z", 
  "initial_value": 67000.0,
  "context": {
    "market_id": "btc_100k_2024",
    "prediction_type": "price_threshold"
  },
  "protocol_version": "1.0"
}
```

**Miner Response:**
```json
{
  "resolution": "TRUE",
  "confidence": 85.5,
  "summary": "Bitcoin crossed $100,000 on December 15, 2024, reaching $105,432",
  "sources": [
    "https://coinmarketcap.com/currencies/bitcoin/",
    "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
  ],
  "analysis_time": 2.3,
  "reasoning": "Checked multiple exchanges. BTC peaked at $105,432 on Dec 15.",
  "target_value": 105432.0,
  "protocol_version": "1.0",
  "miner_version": "subnet90-miner-v1.0"
}
```

#### Resolution States
- **"TRUE"**: Statement is verified as correct/will happen
- **"FALSE"**: Statement is verified as incorrect/won't happen  
- **"PENDING"**: Cannot determine yet (future event, insufficient data)

#### Confidence Scoring
- **90-100**: Very high confidence, multiple sources confirm
- **70-89**: High confidence, strong evidence
- **50-69**: Moderate confidence, some uncertainty
- **30-49**: Low confidence, conflicting signals
- **0-29**: Very low confidence, insufficient data

---

## 🔧 Required Implementation Changes

### 1. Validator Updates
**File: `validator/bittensor_integration.py`**
```python
# Update VerifyStatementSynapse to match protocol
class VerifyStatementSynapse(bt.Synapse):
    # Use exact fields from protocol spec above
    
# Update response parsing
def parse_miner_response(response, miner_uid):
    # Handle protocol_version compatibility
    # Validate required fields
    # Convert to internal MinerResponse format
```

### 2. Miner Implementation  
**File: `miner/bittensor_integration.py` (NEW)**
```python
class BittensorMiner:
    """Bittensor-integrated miner that serves DegenBrainSynapse requests."""
    
    def __init__(self, config, agent):
        self.wallet = bt.wallet(...)
        self.subtensor = bt.subtensor(...)
        self.axon = bt.axon(...)
        self.agent = agent
        
    async def verify_statement(self, synapse: DegenBrainSynapse) -> DegenBrainSynapse:
        """Handle incoming verification requests from validators."""
        # Use agent to analyze statement
        # Fill response fields
        # Return synapse with results
```

### 3. New Files Needed
```
miner/
├── bittensor_integration.py  # NEW - Bittensor axon server
├── protocol.py              # NEW - Synapse definitions
└── main.py                   # UPDATE - Use Bittensor integration

validator/
├── protocol.py              # NEW - Same synapse definitions
└── bittensor_integration.py  # UPDATE - Use new protocol
```

---

## 🎯 Next Steps

### Phase 1: Fix Validator (Priority 1)
1. **Update protocol** to use DegenBrainSynapse specification
2. **Add fallback handling** for miners with different protocols
3. **Force weight setting** even with 0 valid responses initially
4. **Test with existing network** miners

### Phase 2: Implement Miner Server (Priority 2)  
1. **Create Bittensor axon server** in miners
2. **Implement DegenBrainSynapse handler**
3. **Connect agent processing** to synapse responses
4. **Deploy updated miners** to server

### Phase 3: Test & Iterate (Priority 3)
1. **Deploy validator updates** to server
2. **Verify validator sets weights** successfully
3. **Deploy miner updates** when ready
4. **Monitor emission flow** and performance

### Phase 4: Documentation & Community
1. **Publish protocol specification** on GitHub
2. **Create miner setup guides** for external participants  
3. **Engage Bittensor community** about subnet utility
4. **Scale infrastructure** based on adoption

---

## 💻 Handoff to Server Work

### Current Server State
- **Validator running** but stuck on response parsing
- **Miners registered** but not serving Bittensor requests
- **All code deployed** in `/home/subnet90/bittensor-subnet-90-brain/`
- **Virtual environments** set up for each component

### Immediate Server Tasks
1. **Update validator protocol** to handle current miner responses
2. **Add weight setting logic** that works with 0 valid responses
3. **Implement miner axon servers** to actually serve requests
4. **Test full request/response cycle** between your validator and miners

### Key Files to Modify on Server
```
validator/bittensor_integration.py  # Fix synapse and response parsing
validator/main.py                   # Ensure weight setting happens
miner/main.py                      # Add Bittensor axon server
shared/protocol.py                 # Add protocol definitions
```

### Success Criteria
- ✅ Validator successfully sets weights on chain
- ✅ Emissions start flowing to Subnet 90
- ✅ Your miners respond to validator queries
- ✅ Full prediction verification cycle works

The protocol specification above provides the clear contract both validator and miners need to implement. Focus on getting the validator to set weights first (even with the current broken responses), then implement the full protocol on the miner side.