# Subnet 90 Development Checklist
*Track progress and easily resume work*

**🎯 GOAL**: Get emissions flowing by making validator set weights

**📊 PROGRESS**: Phase 1 - 2/8 tasks complete

---

## 🔥 PHASE 1: FIX VALIDATOR PROTOCOL (CRITICAL)
*Estimated: 2-4 hours | Outcome: Emissions start flowing*

### Protocol Foundation
- [x] **1.1** Create `shared/protocol.py` with `DegenBrainSynapse` class ✅
- [x] **1.2** Add protocol validation methods and exports ✅

### Validator Updates  
- [ ] **1.3** Update `validator/bittensor_integration.py` synapse definition
- [ ] **1.4** Fix `parse_miner_response()` to handle protocol mismatches gracefully
- [ ] **1.5** Add fallback handling for `None`/empty responses

### Weight Setting Fix
- [ ] **1.6** Modify `validator/main.py` `_update_weights()` to set weights with 0 responses
- [ ] **1.7** Reduce weight update frequency (every 1-3 statements, not 10)

### Testing & Deployment
- [ ] **1.8** Test validator locally with new protocol → Deploy to server

**✅ PHASE 1 SUCCESS CRITERIA**: 
- Validator sets weights on chain (shows in participant checker)
- Subnet 90 gets first non-zero emissions

---

## 🟡 PHASE 2: IMPLEMENT MINER SERVER (HIGH)
*Estimated: 4-6 hours | Outcome: Full protocol working*

### Miner Bittensor Integration
- [ ] **2.1** Create `miner/bittensor_integration.py` with `BittensorMiner` class
- [ ] **2.2** Initialize wallet, subtensor, axon in miner
- [ ] **2.3** Implement synapse handler for `DegenBrainSynapse`
- [ ] **2.4** Connect agent processing to synapse responses

### Miner Updates
- [ ] **2.5** Update `miner/main.py` to use Bittensor serving (not API polling)
- [ ] **2.6** Add axon startup and shutdown logic
- [ ] **2.7** Update `miner/agents/dummy_agent.py` for protocol compliance

### Testing & Deployment
- [ ] **2.8** Test miners locally → Deploy to server

**✅ PHASE 2 SUCCESS CRITERIA**:
- Your miners respond to your validator queries
- End-to-end statement verification works

---

## 🟡 PHASE 3: INTEGRATION TESTING (HIGH)
*Estimated: 1-2 hours | Outcome: Stable system*

### Local Testing
- [ ] **3.1** Run validator + 2 miners locally and test communication
- [ ] **3.2** Verify synapse request/response cycle works
- [ ] **3.3** Test various statement types and error scenarios

### Server Testing  
- [ ] **3.4** Deploy and test full system on OVH server
- [ ] **3.5** Monitor 24-hour stability

**✅ PHASE 3 SUCCESS CRITERIA**:
- System operates autonomously without errors
- Consistent weight setting and emissions

---

## 🟢 PHASE 4: OPTIMIZATION (LOW PRIORITY)
*Ongoing | Outcome: Production ready*

### Performance
- [ ] **4.1** Optimize agent response times
- [ ] **4.2** Add caching for repeated statements
- [ ] **4.3** Implement performance metrics

### Documentation
- [ ] **4.4** Create external miner setup guide
- [ ] **4.5** Publish protocol documentation
- [ ] **4.6** Engage Bittensor community

---

## 📝 SESSION NOTES

### Current Session Progress:
**Date**: June 4, 2025
**Working On**: Phase 1 setup
**Next Task**: Create `shared/protocol.py`

### Issues & Decisions:
- [ ] Record any issues found during development
- [ ] Note any protocol decisions made
- [ ] Track performance improvements

### Quick Status Check:
```bash
# Run this to check current subnet status
python scripts/check_subnet_participants.py

# Check if emissions started flowing
btcli subnet list | grep "90"
```

---

## 🚀 QUICK RESUME GUIDE

### Starting a New Session:
1. **Check current phase** in progress tracker above
2. **Read session notes** for context
3. **Run status check** to see current state
4. **Continue from next unchecked task**

### Key Files to Monitor:
- `validator/bittensor_integration.py` - Protocol implementation
- `validator/main.py` - Weight setting logic  
- `miner/bittensor_integration.py` - Miner server (Phase 2)
- Server logs: `/home/subnet90/logs/validator.out.log`

### Critical Commands:
```bash
# Test validator locally
export USE_MOCK_VALIDATOR=true && python -m validator.main

# Check validator on server
sudo tail -f /home/subnet90/logs/validator.out.log

# Deploy updates to server
scp file.py ubuntu@SERVER_IP:/home/subnet90/bittensor-subnet-90-brain/path/
```

---

## 📊 SUCCESS METRICS

### ✅ Phase 1 Success (Critical):
- [ ] Validator appears in "ACTIVE WEIGHT SETTERS" list
- [ ] Subnet 90 emission changes from τ 0.0000 to > τ 0.0001
- [ ] Validator logs show "Weights set successfully"

### ✅ Phase 2 Success:
- [ ] Your miners show "Active: ✓" in participant checker
- [ ] Validator logs show valid responses from your miners
- [ ] End-to-end verification cycle completes

### ✅ Overall Success:
- [ ] Consistent daily emissions flowing to Subnet 90
- [ ] System operates autonomously for 7+ days
- [ ] External users can implement and run miners

---

**🎯 CURRENT FOCUS**: Complete Phase 1 to get emissions flowing

**⏭️ NEXT ACTION**: Create `shared/protocol.py` with DegenBrainSynapse definition