# Subnet 90 Emissions Guide

## Understanding Bittensor Emissions

Emissions are the rewards (TAO tokens) distributed to participants in your subnet. For emissions to flow:

1. **Validators must set weights** - This is the #1 requirement
2. **Weights must be non-zero** - Zero weights = no emissions
3. **Weights must be updated regularly** - Every ~100 blocks (tempo)
4. **Miners must be active** - To receive the weighted emissions

## Why Your Subnet Has No Emissions

If you created Subnet 90 weeks ago but see no emissions, it's because:
- No validators are running and setting weights
- Without weights, Bittensor doesn't know how to distribute rewards
- The subnet appears "dead" to the network

## Quick Start: Enable Emissions

### Step 1: Bootstrap Your Subnet
```bash
# Run the bootstrap script to check status and set initial weights
python scripts/bootstrap_subnet.py
```

This script will:
- ✅ Check if your subnet exists
- ✅ Verify your registration
- ✅ Set initial weights to start emissions
- ✅ Monitor emission flow

### Step 2: Run Your Validator
```bash
# As subnet owner, run the first validator
export WALLET_NAME="your_owner_wallet"
export HOTKEY_NAME="your_hotkey"
export API_URL="https://api.degenbrain.com"

python deploy_validator.py
```

### Step 3: Deploy Initial Miners
You need at least 1-2 miners for the system to work:
```bash
# Deploy a test miner
python run_miner.py
```

## Emission Flow Diagram

```
Bittensor Network
    ↓
Subnet 90 (TAO emissions)
    ↓
Validators (18% of emissions)
    ↓ (set weights)
Miners (82% of emissions)
```

## Common Issues & Solutions

### "No emissions after weeks"
**Problem**: No validators setting weights
**Solution**: Run bootstrap script + deploy validator

### "Validators running but no emissions"
**Problem**: Validators not setting weights properly
**Solution**: Check validator logs for weight-setting confirmations

### "Weights set but no emissions"
**Problem**: Weights might be all zeros or not normalized
**Solution**: Use bootstrap script to set proper weights

## Technical Details

### How Bittensor Calculates Emissions
1. Each subnet gets allocated emissions based on root network weights
2. Within subnet: 18% to validators, 82% to miners
3. Distribution based on weights set by validators
4. Consensus mechanism ensures fair distribution

### Weight Setting Requirements
```python
# Weights must:
- Sum to 1.0 (normalized)
- Be non-zero for at least one miner
- Be updated every tempo (~100 blocks)
- Come from registered validators with stake
```

### Our Implementation
The validator automatically:
- Queries miners for statement verification
- Scores responses based on accuracy
- Sets weights proportional to performance
- Updates weights every 10 statements

## Emergency: Force Start Emissions

If normal methods fail, use this emergency procedure:

```python
# 1. Set temporary self-weight (not recommended long-term)
btcli root weights --netuid 90 --self_weight 1.0

# 2. Then immediately deploy proper validators/miners
python deploy_validator.py
```

## Monitoring Emissions

### Check Subnet Status
```bash
# View subnet info
btcli subnet list --netuid 90

# Check metagraph
btcli subnet metagraph --netuid 90

# Monitor your balance
btcli wallet balance --wallet.name owner_wallet
```

### Using Taostats
Visit https://taostats.io/subnets/90 to see:
- Current emissions
- Active validators/miners  
- Weight distribution
- Network health

## Best Practices

1. **Always run at least one validator** as subnet owner
2. **Incentivize early miners** with guaranteed weights
3. **Monitor weight setting** in validator logs
4. **Update weights regularly** to maintain emissions
5. **Gradually onboard** new participants

## Timeline to Emissions

After running bootstrap:
1. **Immediate**: Weights set on chain
2. **Next tempo (~20 min)**: Emissions start calculating  
3. **Within 1 hour**: See first emissions in wallets
4. **After 24 hours**: Stable emission flow

## Need Help?

If emissions still aren't flowing after following this guide:
1. Check validator logs for errors
2. Verify registration with `btcli subnet metagraph --netuid 90`
3. Ensure weights are being set (check Taostats)
4. Contact Bittensor support if subnet-level issue