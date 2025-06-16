# Weight Setting Strategy Evolution

## Current Mock Strategy (Testing Phase)
```python
# Fixed weights for known good miners + your test miners
uids = [1, 68, 63, 172, 173, 204]
weights = [0.3, 0.25, 0.15, 0.1, 0.1, 0.1]  # 70% proven, 30% yours
```

**Pros**: Safe, predictable, supports network
**Cons**: Not responsive to actual performance

## Proposed Merit-Based Strategy (Production Phase)

### Phase 1: Hybrid Approach (Recommended Start)
```python
# Combine proven miners with merit-based scoring
base_weights = {
    1: 0.15,    # Known good miners get base allocation
    68: 0.10,
    63: 0.05
}

# Remaining 70% allocated based on actual performance
performance_weights = calculate_merit_based_weights(miner_responses)
```

### Phase 2: Full Merit-Based (Long Term)
```python
# 100% based on actual statement resolution performance
weights = calculate_weights_from_brain_api_results()
```

## Merit Calculation with Brain-API Integration

### Key Metrics from Brain-API:
1. **Accuracy vs Official Resolution**: How often miner matches brainstorm
2. **Confidence Calibration**: Appropriate confidence levels
3. **Response Speed**: Faster responses get slight bonus
4. **Source Quality**: Better reasoning gets higher scores

### Implementation:
```python
def calculate_merit_weights(validator):
    scores = {}
    
    for miner_uid, responses in validator.miner_history.items():
        accuracy = calculate_accuracy_vs_official(responses)
        confidence_cal = calculate_confidence_calibration(responses) 
        speed_bonus = calculate_speed_bonus(responses)
        quality_score = calculate_reasoning_quality(responses)
        
        total_score = (
            accuracy * 0.5 +           # 50% accuracy vs official
            confidence_cal * 0.25 +    # 25% confidence calibration  
            speed_bonus * 0.15 +       # 15% speed bonus
            quality_score * 0.10       # 10% reasoning quality
        )
        
        scores[miner_uid] = total_score
    
    return normalize_weights(scores)
```

## Recommended Transition Plan

### Week 1-2: Current Mock (Safe Start)
- Keep your current approach
- Monitor brain-api integration
- Collect performance data

### Week 3-4: Hybrid Approach  
- 30% to proven miners (fixed)
- 70% merit-based from collected data
- Gradual transition to performance

### Week 5+: Full Merit-Based
- 100% based on statement resolution accuracy
- Dynamic adjustment every epoch
- Rewards best performers

## Code Changes Needed

### 1. Update WeightsCalculator to use Brain-API data:
```python
class WeightsCalculator:
    def __init__(self):
        self.miner_performance = defaultdict(list)
        self.official_resolutions = {}  # From brain-api
    
    def record_official_resolution(self, statement_id, official_result):
        """Store official resolution from brain-api"""
        self.official_resolutions[statement_id] = official_result
    
    def calculate_merit_weights(self) -> Dict[int, float]:
        """Calculate weights based on accuracy vs official resolutions"""
        scores = {}
        
        for miner_uid, responses in self.miner_performance.items():
            correct = 0
            total = 0
            
            for response in responses:
                if response.statement_id in self.official_resolutions:
                    official = self.official_resolutions[response.statement_id]
                    if response.resolution == official.resolution:
                        correct += 1
                    total += 1
            
            accuracy = correct / total if total > 0 else 0
            scores[miner_uid] = accuracy
        
        return self._normalize_weights(scores)
```

### 2. Update Validator to collect brain-api results:
```python
async def _process_statement(self, statement: Statement):
    # ... existing code ...
    
    # After submitting to brain-api, get the official result
    success = await self.api_client.submit_miner_responses(...)
    
    if success:
        # Store official resolution for merit calculation
        self.weights_calculator.record_official_resolution(
            statement.id, 
            official_result
        )
```

## Benefits of Merit-Based Approach

1. **Incentivizes Accuracy**: Miners rewarded for correct predictions
2. **Dynamic Adaptation**: Weights adjust to actual performance  
3. **Network Health**: Best performers get most influence
4. **Decentralization**: No fixed favoritism
5. **Brain-API Integration**: Uses official resolutions as ground truth

## Migration Strategy

Start with your current approach, then gradually migrate:

```python
def calculate_hybrid_weights(self, epoch: int):
    if epoch < 10:
        # Bootstrap phase - use fixed weights
        return self.bootstrap_weights()
    elif epoch < 50:
        # Transition phase - hybrid approach
        fixed_weight = max(0.3 - (epoch - 10) * 0.01, 0.1)
        merit_weight = 1.0 - fixed_weight
        return self.combine_weights(
            self.bootstrap_weights(), fixed_weight,
            self.merit_weights(), merit_weight
        )
    else:
        # Full merit phase
        return self.merit_weights()
```

This gives you a smooth transition from safe fixed weights to dynamic performance-based weights!