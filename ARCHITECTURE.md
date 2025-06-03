# DegenBrain Subnet 90 Architecture Documentation

## Overview

DegenBrain Subnet 90 ("brain") is a decentralized prediction market resolution system built on the Bittensor network. The subnet enables automated verification of prediction statements by distributing verification tasks to a network of miners who provide evidence-based resolution decisions.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DegenBrain    │    │   Bittensor      │    │   Subnet 90     │
│   API Service   │◄──►│   Network        │◄──►│   Validators    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Subnet 90      │    │   Consensus     │
                       │   Miners         │    │   & Scoring     │
                       │                  │    │                 │
                       └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. Validators (`validator/`)

Validators are the orchestrators of the subnet. They:

- **Fetch unresolved statements** from the DegenBrain API
- **Distribute tasks** to miners across the network
- **Collect and score responses** based on multiple quality factors
- **Calculate consensus** using confidence-weighted voting
- **Set weights** on the Bittensor network to reward good miners

#### Key Files:
- `validator/main.py` - Main validator loop and orchestration
- `validator/weights.py` - Scoring algorithm and consensus calculation

### 2. Miners (`miner/`)

Miners are the workers that verify prediction statements. They:

- **Receive statements** from validators
- **Analyze and research** the statement's verifiability
- **Provide resolution** (TRUE/FALSE/PENDING) with confidence scores
- **Supply evidence** through sources and reasoning

#### Key Files:
- `miner/main.py` - Main miner loop and task processing
- `miner/agents/` - Different verification agent implementations
- `miner/agents/dummy_agent.py` - Reference implementation

### 3. Shared Infrastructure (`shared/`)

Common components used by both validators and miners:

- **Data Types** (`shared/types.py`) - Core data structures
- **API Client** (`shared/api.py`) - DegenBrain API integration
- **Configuration** (`shared/config.py`) - Environment-based settings

## Data Flow

### 1. Statement Processing Flow

```
1. Validator fetches unresolved statements from DegenBrain API
   ↓
2. Validator sends statements to miners via Bittensor dendrite
   ↓
3. Miners analyze statements using their verification agents
   ↓
4. Miners return responses with resolution + confidence + evidence
   ↓
5. Validator collects responses and calculates consensus
   ↓
6. Validator scores miners based on response quality
   ↓
7. Validator sets weights on Bittensor network
   ↓
8. (Optional) Consensus posted back to DegenBrain API
```

### 2. Data Structures

#### Statement
```python
@dataclass
class Statement:
    statement: str           # "Bitcoin will reach $100,000 by Dec 31, 2024"
    end_date: str           # "2024-12-31T23:59:59Z"
    createdAt: str          # "2024-01-15T12:00:00Z"
    initialValue: float     # 42000.0 (starting price)
    direction: str          # "increase"/"decrease"
    id: str                 # Unique identifier
```

#### MinerResponse
```python
class MinerResponse(BaseModel):
    statement: str          # Original statement
    resolution: Resolution  # TRUE/FALSE/PENDING
    confidence: float       # 0-100 confidence score
    summary: str           # Reasoning explanation
    sources: List[str]     # Evidence sources
    target_value: float    # Extracted target (e.g., 100000)
    proof_hash: str        # Cryptographic proof
    miner_uid: int         # Miner identifier
```

#### ValidationResult
```python
@dataclass
class ValidationResult:
    consensus_resolution: Resolution    # Final consensus
    consensus_confidence: float        # Average confidence
    total_responses: int              # Total miners queried
    valid_responses: int              # Valid responses received
    miner_scores: Dict[int, float]    # UID -> normalized score
    consensus_sources: List[str]      # Top evidence sources
```

## Scoring Algorithm

The validator uses a multi-dimensional scoring system to evaluate miner responses:

### Scoring Components (validator/weights.py)

1. **Accuracy Score (40% weight)**
   - `1.0` - Matches consensus resolution
   - `0.5` - PENDING (appropriately uncertain)
   - `0.0` - Contradicts consensus

2. **Confidence Score (20% weight)**
   - Rewards appropriate confidence levels
   - High confidence on correct answers: `confidence / 100`
   - High confidence on wrong answers: `1 - confidence`
   - Moderate confidence on PENDING: distance from 0.5

3. **Consistency Score (30% weight)**
   - Agreement with other high-confidence (>80%) miners
   - Calculated as: `agreements / total_high_confidence_peers`

4. **Source Quality Score (10% weight)**
   - Number of sources (max benefit at 3 sources)
   - Reliability bonus for known sources (CoinGecko, Yahoo, etc.)
   - Combined: `(source_count_score + reliability_score) / 2`

### Consensus Calculation

Consensus uses **confidence-weighted voting**:

```python
vote_weights = defaultdict(float)
for response in responses:
    weight = response.confidence / 100.0
    vote_weights[response.resolution] += weight

consensus = max(vote_weights.items(), key=lambda x: x[1])[0]
```

### Weight Normalization

Final scores are normalized to sum to 1.0 for Bittensor weight setting:

```python
total = sum(scores.values())
normalized_weights = {uid: score / total for uid, score in scores.items()}
```

## Agent System

Miners use an **agent-based architecture** for statement verification:

### Base Agent Interface
```python
class BaseAgent(ABC):
    @abstractmethod
    async def verify_statement(self, statement: Statement) -> MinerResponse:
        """Verify a statement and return resolution with evidence."""
        pass
```

### Agent Implementations

1. **DummyAgent** (`miner/agents/dummy_agent.py`)
   - Reference implementation for testing
   - Simulates realistic verification behavior
   - Configurable accuracy and response patterns

2. **Future Agents** (Phase 6)
   - **WebAgent** - Web scraping and research
   - **APIAgent** - Financial data APIs integration
   - **HybridAgent** - Multi-source verification

## Configuration System

Environment-based configuration with validation:

### Required Variables
```bash
WALLET_NAME=validator_wallet    # Bittensor wallet name
HOTKEY_NAME=default            # Bittensor hotkey name
API_URL=https://api.degenbrain.com/resolve
```

### Optional Variables
```bash
NETWORK=finney                 # Bittensor network
SUBNET_UID=90                 # Subnet number
VALIDATOR_PORT=8090           # Validator API port
MINER_PORT=8091              # Miner API port
```

## Testing Framework

Comprehensive test suite with 71 tests covering:

### Test Categories
- **Unit Tests** - Individual component testing
- **Integration Tests** - Component interaction testing
- **Async Tests** - Asynchronous operation testing

### Key Test Files
- `tests/test_validator.py` - Validator and scoring logic (20 tests)
- `tests/test_miner.py` - Miner agents and processing (16 tests)
- `tests/test_api.py` - API client functionality (10 tests)
- `tests/test_types.py` - Data validation and serialization (15 tests)
- `tests/test_config.py` - Configuration management (10 tests)

## Error Handling & Resilience

### Validator Resilience
- **Retry Logic** - Exponential backoff for API calls
- **Graceful Degradation** - Continues with partial responses
- **Signal Handling** - Clean shutdown on interrupts
- **Statistics Tracking** - Performance monitoring

### Miner Resilience
- **Timeout Protection** - Configurable verification timeouts
- **Error Recovery** - Returns PENDING on failures
- **Validation** - Input/output validation at all boundaries

## Performance Characteristics

### Validator Performance
- **Concurrent Processing** - Async/await throughout
- **Scalable Queries** - Handles 10+ miners simultaneously
- **Memory Efficient** - Streaming processing, no large buffers
- **Rate Limited** - Respects API rate limits

### Miner Performance
- **Fast Response** - Sub-second verification for simple cases
- **Resource Bounded** - Configurable timeouts and limits
- **Stateless Design** - No inter-request dependencies

## Security Features

### Data Integrity
- **Cryptographic Proofs** - SHA-256 hashes for response verification
- **Input Validation** - Pydantic models prevent injection
- **Timeout Protection** - Prevents hanging operations

### Network Security
- **HTTPS Only** - All external communications encrypted
- **Authentication** - Bittensor cryptographic authentication
- **Rate Limiting** - Protection against abuse

## Deployment Architecture

### Validator Deployment
```bash
# Set environment variables
export WALLET_NAME=my_validator
export HOTKEY_NAME=default
export API_URL=https://api.degenbrain.com

# Run validator
python run_validator.py
```

### Miner Deployment
```bash
# Set environment variables
export WALLET_NAME=my_miner
export HOTKEY_NAME=default
export MINER_AGENT=dummy

# Run miner
python run_miner.py
```

## Monitoring & Observability

### Structured Logging
- **Component-based** - Each component has dedicated logger
- **Structured Output** - JSON-formatted logs with metadata
- **Performance Metrics** - Request timing and success rates

### Statistics Tracking
```python
# Validator Stats
{
    "statements_processed": 150,
    "consensus_reached": 142,
    "miners_queried": 1500,
    "weights_updated": 15,
    "errors": 3,
    "uptime": "2:45:30",
    "consensus_rate": 0.947
}

# Miner Stats
{
    "tasks_processed": 89,
    "agent": "DummyAgent",
    "is_running": true,
    "success_rate": 0.966,
    "avg_response_time": 1.2
}
```

## Future Enhancements (Phases 5-6)

### Phase 5: Bittensor Integration
- Real miner querying via Bittensor dendrite
- On-chain weight setting
- Wallet and hotkey management
- Network synchronization

### Phase 6: Production Features
- Advanced verification agents
- Caching and optimization
- Monitoring dashboard
- Load balancing

## API Integration

### DegenBrain API Integration
The system integrates with DegenBrain's resolve endpoint:

```python
# Fetch unresolved statements
statements = await api_client.fetch_statements()

# Resolve individual statement
result = await api_client.resolve_statement(statement)

# Post consensus result (optional)
success = await api_client.post_consensus(statement_id, consensus)
```

## Getting Started

### Prerequisites
- Python 3.11+
- Virtual environment
- Environment variables configured

### Quick Start
```bash
# Clone and setup
git clone <repository>
cd bittensor-subnet-90-brain
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start validator
WALLET_NAME=test HOTKEY_NAME=test API_URL=https://test.api.com python run_validator.py

# Start miner (in another terminal)
WALLET_NAME=test HOTKEY_NAME=test API_URL=https://test.api.com python run_miner.py
```

This architecture provides a robust, scalable foundation for decentralized prediction market resolution on Bittensor, with clear separation of concerns and comprehensive testing.