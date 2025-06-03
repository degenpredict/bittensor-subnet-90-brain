# DegenPredict Subnet Implementation Plan

## Overview
This document outlines the phased implementation approach for the Bittensor Subnet 90 "brain" system, including milestones, tests, and acceptance criteria for each phase.

## Phase 1: Project Setup & Core Structure 🏗️

### Objectives
- Set up the foundational project structure
- Define core data models and configuration system
- Establish testing framework

### Tasks
1. **Create directory structure**
   ```
   validator/
   miner/
   shared/
   tests/
   ```

2. **Create requirements.txt**
   - bittensor>=6.0.0
   - aiohttp>=3.9.0
   - requests>=2.31.0
   - python-dotenv>=1.0.0
   - pytest>=7.4.0
   - pytest-asyncio>=0.21.0
   - pytest-mock>=3.12.0

3. **Create .env.example**
   ```env
   WALLET_NAME=brain
   HOTKEY_NAME=validator1
   NETWORK=finney
   API_URL=https://api.degenbrain.com/resolve
   LOG_LEVEL=INFO
   ```

4. **Implement shared/types.py**
   - Statement dataclass
   - MinerResponse dataclass
   - ValidationResult dataclass

5. **Implement shared/config.py**
   - Environment variable loading
   - Configuration validation
   - Default values

### Tests for Phase 1
```python
# test_types.py
- test_statement_creation
- test_statement_serialization
- test_response_validation
- test_invalid_response_rejection

# test_config.py
- test_env_loading
- test_missing_env_handling
- test_config_validation
```

### Acceptance Criteria
- [ ] All directories created
- [ ] Dependencies installable via pip
- [ ] Types can be instantiated and serialized
- [ ] Config loads from .env successfully
- [ ] All Phase 1 tests pass

---

## Phase 2: API Integration Layer 🔌

### Objectives
- Build robust API client for DegenPredict
- Implement mock API for testing
- Establish error handling patterns

### Tasks
1. **Implement shared/api.py**
   - `fetch_statements()` - Get unresolved statements
   - `post_consensus()` - Submit results back
   - Retry logic with exponential backoff
   - Connection pooling

2. **Create tests/mock_api.py**
   - Mock statement generator
   - Configurable response scenarios
   - Error simulation

3. **Error handling**
   - Network errors
   - Invalid JSON responses
   - Rate limiting
   - API downtime

### Tests for Phase 2
```python
# test_api_client.py
- test_fetch_statements_success
- test_fetch_statements_empty
- test_network_error_retry
- test_invalid_json_handling
- test_rate_limit_backoff
- test_connection_pooling

# test_mock_api.py
- test_mock_statement_generation
- test_error_simulation
- test_response_consistency
```

### Acceptance Criteria
- [ ] API client can fetch statements from mock
- [ ] Retry logic handles transient failures
- [ ] Error cases are logged appropriately
- [ ] Mock API provides realistic test data
- [ ] All Phase 2 tests pass

---

## Phase 3: Miner Implementation ⛏️

### Objectives
- Build miner base infrastructure
- Create agent interface for extensibility
- Implement response generation

### Tasks
1. **miner/main.py**
   - Task polling loop
   - Graceful shutdown
   - Health checks

2. **miner/agents/base_agent.py**
   - Abstract base class
   - `verify_statement()` interface
   - Confidence scoring

3. **miner/agents/dummy_agent.py**
   - Random response generation
   - Configurable accuracy
   - Source simulation

4. **Response builder**
   - JSON schema validation
   - Proof hash generation
   - Source formatting

### Tests for Phase 3
```python
# test_miner_main.py
- test_polling_loop
- test_graceful_shutdown
- test_task_processing
- test_error_recovery

# test_agents.py
- test_base_agent_interface
- test_dummy_agent_responses
- test_confidence_scoring
- test_source_validation

# test_response_builder.py
- test_json_schema_compliance
- test_proof_hash_generation
- test_invalid_response_rejection
```

### Acceptance Criteria
- [ ] Miner can poll for tasks
- [ ] Dummy agent generates valid responses
- [ ] Response format matches specification
- [ ] Miner handles errors gracefully
- [ ] All Phase 3 tests pass

---

## Phase 4: Validator Implementation ✅

### Objectives
- Build validator orchestration ✅
- Implement scoring algorithm ✅
- Create consensus mechanism ✅

### Tasks
1. **validator/main.py** ✅
   - Statement fetching loop ✅
   - Miner query orchestration ✅
   - Result aggregation ✅

2. **validator/weights.py** ✅
   - Accuracy scoring ✅
   - Confidence weighting ✅
   - Source reliability scoring ✅
   - Weight normalization ✅

3. **Consensus logic** ✅
   - Majority voting ✅
   - Confidence-weighted consensus ✅
   - Tie-breaking rules ✅

### Tests for Phase 4
```python
# test_validator_main.py
- test_statement_processing_loop
- test_miner_query_timeout
- test_response_aggregation
- test_empty_response_handling

# test_weights.py
- test_accuracy_scoring
- test_confidence_weighting
- test_source_reliability
- test_weight_normalization
- test_edge_cases

# test_consensus.py
- test_majority_voting
- test_weighted_consensus
- test_tie_breaking
- test_insufficient_responses
```

### Acceptance Criteria
- [x] Validator processes statements continuously
- [x] Scoring algorithm produces fair weights
- [x] Consensus matches expected outcomes
- [x] Edge cases handled properly
- [x] All Phase 4 tests pass

---

## Phase 5: Bittensor Integration 🧠

### Objectives
- Connect to Bittensor network
- Implement Axon/Dendrite communication
- Enable weight setting on chain

### Tasks
1. **Wallet initialization**
   - Load from config
   - Validate credentials
   - Check stake requirements

2. **Subnet connection**
   - Connect to specified network
   - Register on subnet 90
   - Sync with metagraph

3. **Weight setting**
   - Format weights for chain
   - Submit transactions
   - Handle failures

4. **Axon/Dendrite setup**
   - Miner serves via Axon
   - Validator queries via Dendrite
   - Protocol implementation

### Tests for Phase 5
```python
# test_bittensor_integration.py
- test_wallet_loading
- test_subnet_connection
- test_metagraph_sync
- test_weight_submission
- test_axon_serving
- test_dendrite_querying

# Local testnet tests
- test_full_communication_flow
- test_weight_propagation
- test_stake_requirements
```

### Acceptance Criteria
- [ ] Can connect to local testnet
- [ ] Miners register successfully
- [ ] Validators can query miners
- [ ] Weights update on chain
- [ ] All Phase 5 tests pass

---

## Phase 6: Production Features 🚀

### Objectives
- Add production-grade features
- Implement monitoring and logging
- Create deployment infrastructure

### Tasks
1. **Comprehensive logging**
   - Structured logging
   - Log rotation
   - Performance metrics

2. **Monitoring integration**
   - Wandb setup
   - Custom dashboards
   - Alert configuration

3. **Docker containers**
   - Validator Dockerfile
   - Miner Dockerfile
   - docker-compose.yml

4. **Deployment scripts**
   - Health checks
   - Auto-restart
   - Update procedures

### Tests for Phase 6
```python
# test_logging.py
- test_structured_output
- test_log_rotation
- test_performance_logging

# test_monitoring.py
- test_metric_collection
- test_wandb_integration
- test_alert_triggers

# test_deployment.py
- test_docker_builds
- test_container_communication
- test_health_endpoints
```

### Acceptance Criteria
- [ ] Logs are structured and searchable
- [ ] Metrics visible in monitoring
- [ ] Docker containers build and run
- [ ] Deployment is reproducible
- [ ] All Phase 6 tests pass

---

## Testing Strategy

### Unit Tests
- Run after each component implementation
- Mock external dependencies
- Aim for >80% coverage

### Integration Tests
- Run after each phase completion
- Test component interactions
- Use realistic test data

### System Tests
- End-to-end validation
- Performance benchmarks
- Stress testing with multiple miners

### Test Commands
```bash
# Run all tests
pytest

# Run specific phase tests
pytest tests/test_phase1_*.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests
pytest tests/integration/ -m integration
```

---

## Success Metrics

1. **Phase 1-2**: Core infrastructure works reliably
2. **Phase 3-4**: Miner/Validator communicate successfully
3. **Phase 5**: Integrates with Bittensor network
4. **Phase 6**: Production-ready with <1% downtime

---

## Risk Mitigation

1. **API Changes**: Abstract API calls, version endpoints
2. **Network Issues**: Implement robust retry logic
3. **Scoring Bias**: Regular algorithm audits
4. **Security**: No private keys in code, use .env