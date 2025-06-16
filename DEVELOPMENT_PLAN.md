# Subnet 90 Development Plan
*Get Emissions Flowing & Full Protocol Working*

## 🎯 Goal: Get Emissions Flowing
**Success Metric**: Validator sets weights → Emissions > 0 TAO/day

---

## 📋 Phase 1: Fix Validator Protocol (LOCAL DEV)
*Priority: Critical - Do this first to enable emissions*

### 1.1 Create Protocol Definitions
- [ ] **File**: `shared/protocol.py`
  - [ ] Define `DegenBrainSynapse` class
  - [ ] Add validation methods
  - [ ] Export for validator and miner use

### 1.2 Update Validator Response Parsing
- [ ] **File**: `validator/bittensor_integration.py`
  - [ ] Update `VerifyStatementSynapse` → `DegenBrainSynapse`
  - [ ] Fix `parse_miner_response()` to handle protocol mismatches
  - [ ] Add fallback for `None`/empty responses
  - [ ] Ensure validator continues on parsing errors

### 1.3 Force Weight Setting
- [ ] **File**: `validator/main.py`
  - [ ] Modify `_update_weights()` to set weights even with 0 valid responses
  - [ ] Add "bootstrap mode" that sets equal weights initially
  - [ ] Reduce weight update frequency (every 1-3 statements, not 10)
  - [ ] Add logging for weight setting attempts

### 1.4 Test Validator Locally
- [ ] **Test**: Run validator with mock Bittensor
- [ ] **Verify**: Validator processes statements without errors
- [ ] **Verify**: Weight setting logic executes
- [ ] **Fix**: Any remaining parsing/protocol issues

---

## 📋 Phase 2: Implement Miner Bittensor Server (LOCAL DEV)
*Priority: High - Make miners actually serve requests*

### 2.1 Create Miner Bittensor Integration
- [ ] **File**: `miner/bittensor_integration.py`
  - [ ] Create `BittensorMiner` class
  - [ ] Initialize wallet, subtensor, axon
  - [ ] Implement synapse handler for `DegenBrainSynapse`
  - [ ] Connect agent processing to synapse responses

### 2.2 Update Miner Main
- [ ] **File**: `miner/main.py`
  - [ ] Import `BittensorMiner`
  - [ ] Replace API polling with Bittensor serving
  - [ ] Add axon startup and shutdown
  - [ ] Keep agent-based processing

### 2.3 Enhanced Agent Response
- [ ] **File**: `miner/agents/dummy_agent.py`
  - [ ] Return protocol-compliant responses
  - [ ] Add reasoning and source fields
  - [ ] Implement confidence scoring
  - [ ] Add processing time tracking

### 2.4 Test Miners Locally
- [ ] **Test**: Start miner with mock Bittensor
- [ ] **Test**: Send test synapse requests
- [ ] **Verify**: Proper protocol responses
- [ ] **Verify**: Agent integration works

---

## 📋 Phase 3: Local Integration Testing
*Priority: Medium - Verify full protocol works*

### 3.1 Local Validator ↔ Miner Testing
- [ ] **Test**: Run validator + 2 miners locally
- [ ] **Test**: Validator queries local miners
- [ ] **Verify**: Proper synapse communication
- [ ] **Verify**: Response parsing works
- [ ] **Verify**: Consensus calculation
- [ ] **Verify**: Weight setting succeeds

### 3.2 Protocol Validation
- [ ] **Test**: Various statement types
- [ ] **Test**: Different confidence levels
- [ ] **Test**: Error handling scenarios
- [ ] **Verify**: All protocol fields populated correctly

---

## 📋 Phase 4: Server Deployment (REMOTE)
*Priority: High - Deploy working code*

### 4.1 Deploy Updated Validator
- [ ] **Deploy**: Copy updated files to server
- [ ] **Deploy**: Update supervisor configs
- [ ] **Test**: Validator connects and processes statements
- [ ] **Monitor**: Check for weight setting in logs
- [ ] **Verify**: Validator shows as active on network

### 4.2 Deploy Updated Miners
- [ ] **Deploy**: Copy miner updates to server
- [ ] **Deploy**: Update supervisor configs with axon ports
- [ ] **Test**: Miners start and serve requests
- [ ] **Test**: Validator can query local miners
- [ ] **Verify**: Miners show as active on network

### 4.3 Full System Test
- [ ] **Test**: End-to-end statement processing
- [ ] **Monitor**: Validator weight setting frequency
- [ ] **Check**: Emissions start flowing (run participant checker)
- [ ] **Verify**: System stability over 24 hours

---

## 📋 Phase 5: Optimization & Scale (ONGOING)
*Priority: Low - Improve after basic functionality works*

### 5.1 Performance Optimization
- [ ] **Optimize**: Agent response times
- [ ] **Optimize**: Validator query batching
- [ ] **Add**: Caching for repeated statements
- [ ] **Add**: Performance metrics logging

### 5.2 Advanced Features
- [ ] **Add**: Multi-agent support in miners
- [ ] **Add**: Dynamic confidence adjustment
- [ ] **Add**: Source verification
- [ ] **Add**: Reputation tracking

### 5.3 Documentation & Community
- [ ] **Create**: Miner setup guide for external users
- [ ] **Create**: Protocol documentation for GitHub
- [ ] **Engage**: Bittensor community outreach
- [ ] **Publish**: Performance metrics and case studies

---

## 🛠️ Development Workflow

### Local Development Setup
```bash
# Work in your existing repo
cd /Users/nobi/Projects/Solana/bittensor-subnet-90-brain

# Create feature branch for protocol updates
git checkout -b protocol-implementation

# Test locally with mock Bittensor
export USE_MOCK_VALIDATOR=true
python -m validator.main
```

### File Structure Plan
```
shared/
├── protocol.py              # NEW - DegenBrainSynapse definition
└── types.py                 # UPDATE - Add protocol types

validator/
├── bittensor_integration.py # UPDATE - Use new protocol
└── main.py                  # UPDATE - Force weight setting

miner/
├── bittensor_integration.py # NEW - Axon server implementation
├── main.py                  # UPDATE - Use Bittensor serving
└── agents/
    └── dummy_agent.py       # UPDATE - Protocol-compliant responses
```

### Testing Strategy
1. **Unit Tests**: Test protocol parsing and response generation
2. **Integration Tests**: Local validator ↔ miner communication
3. **Mock Network Tests**: Test with simulated Bittensor network
4. **Live Network Tests**: Deploy to server and test with real network

---

## 🚨 Critical Success Factors

### Phase 1 Success = Emissions Start
- Validator successfully sets weights on chain
- Shows up in "active weight setters" when running participant checker
- Subnet 90 gets first non-zero emissions

### Phase 2 Success = Full Protocol
- Your miners respond to your validator queries
- End-to-end statement verification works
- System operates autonomously

### Phase 3 Success = Community Ready
- External miners can implement protocol
- Documentation supports onboarding
- Subnet provides real value to prediction markets

---

## ⏱️ Time Estimates

| Phase | Tasks | Estimated Time | Priority |
|-------|--------|----------------|----------|
| **Phase 1** | Fix validator protocol | 2-4 hours | 🔥 Critical |
| **Phase 2** | Implement miner server | 4-6 hours | 🟡 High |
| **Phase 3** | Local integration testing | 1-2 hours | 🟡 High |
| **Phase 4** | Server deployment | 1-2 hours | 🟡 High |
| **Phase 5** | Optimization & scale | Ongoing | 🟢 Low |

**Total to basic functionality**: ~8-12 hours of focused development

---

## 🎯 Immediate Next Steps

### Start Here (Next 30 minutes):
1. **Create** `shared/protocol.py` with `DegenBrainSynapse`
2. **Update** `validator/bittensor_integration.py` to use new synapse
3. **Test** validator can import and use new protocol

### This Session Goals:
- [ ] Complete Phase 1.1 and 1.2 (protocol + validator updates)
- [ ] Test validator with new protocol locally
- [ ] Identify any remaining validator issues

Let's start with creating the protocol definition - want to begin with `shared/protocol.py`?