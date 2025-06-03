# Deployment Guide for Subnet 90 Validator

This guide covers deploying a validator on Bittensor Subnet 90 ("Brain") for live production use.

## Prerequisites

### 1. System Requirements
- Python 3.11 or higher
- Minimum 8GB RAM
- Stable internet connection
- Linux/macOS (recommended)

### 2. Bittensor Setup
```bash
# Install Bittensor CLI
pip install bittensor

# Create a wallet (if you don't have one)
btcli wallet create --wallet.name validator_wallet

# Fund your wallet with TAO tokens
# You'll need sufficient TAO for registration and staking
```

### 3. Registration on Subnet 90
```bash
# Register your hotkey on subnet 90
btcli subnet register --netuid 90 --wallet.name validator_wallet

# Check registration status
btcli wallet overview --wallet.name validator_wallet
```

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/degenpredict/bittensor-subnet-90-brain
cd bittensor-subnet-90-brain
```

### 2. Set Environment Variables
Create a `.env` file or export these variables:

```bash
# Required: Wallet configuration
export WALLET_NAME="validator_wallet"
export HOTKEY_NAME="default"

# Required: API endpoint
export API_URL="https://api.degenbrain.com"

# Optional: Network configuration
export NETWORK="finney"           # or "local" for testing
export SUBNET_UID="90"
export QUERY_TIMEOUT="30.0"

# Optional: Logging
export LOG_LEVEL="INFO"
export LOG_FORMAT="json"
```

### 3. Install Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Or use the deployment script
python deploy_validator.py --install-deps
```

## Deployment Options

### Option 1: Quick Deploy (Recommended)
Use the deployment script for automated setup:

```bash
# Test mode (no real network interaction)
python deploy_validator.py --test

# Production mode
python deploy_validator.py
```

### Option 2: Manual Deploy
For more control over the deployment process:

```bash
# 1. Test validator initialization
python -c "
import asyncio
from validator.main import Validator
async def test():
    validator = Validator()
    await validator.setup()
    print('Validator initialized successfully')
    await validator.shutdown()
asyncio.run(test())
"

# 2. Run validator
python -m validator.main
```

## Pre-Production Testing

### Test with Mock Bittensor
Before deploying to the live network, test with mock components:

```bash
# Run in test mode
export USE_MOCK_VALIDATOR=true
python deploy_validator.py --test
```

### Validate Network Connection
```bash
# Check your registration
btcli wallet overview --wallet.name validator_wallet --netuid 90

# Check subnet information
btcli subnet list | grep "90"

# Check network connectivity
btcli subnet metagraph --netuid 90
```

## Production Deployment

### 1. Final Checks
```bash
# Run deployment checks
python deploy_validator.py --skip-checks=false
```

Expected output:
- ✅ Python 3.11+ detected
- ✅ Environment variables set
- ✅ Bittensor installed
- ✅ Wallet found and accessible
- ✅ Hotkey registered on subnet 90
- ✅ Validator test passed

### 2. Start Validator
```bash
# Start validator in production mode
python deploy_validator.py

# Or run directly
python -m validator.main
```

### 3. Monitor Validator
The validator will output structured logs. Key metrics to monitor:

```json
{
  "event": "Statement validation complete",
  "consensus": "TRUE",
  "confidence": 85.2,
  "valid_responses": 8,
  "total_responses": 10
}
```

## Monitoring and Maintenance

### Key Metrics
- `statements_processed`: Number of statements validated
- `consensus_reached`: Successful consensus calculations
- `miners_queried`: Total miner interactions
- `weights_updated`: Network weight updates
- `errors`: Error count

### Health Checks
```bash
# Check validator stats
curl http://localhost:8080/stats  # If health endpoint is enabled

# Check Bittensor network status
btcli subnet metagraph --netuid 90

# Monitor TAO balance
btcli wallet balance --wallet.name validator_wallet
```

### Log Monitoring
```bash
# Follow validator logs
tail -f validator.log

# Check for errors
grep "ERROR" validator.log | tail -20
```

## Troubleshooting

### Common Issues

1. **Registration Failed**
   ```bash
   # Check subnet registration cost
   btcli subnet register --netuid 90 --wallet.name validator_wallet --no_prompt false
   
   # Ensure sufficient TAO balance
   btcli wallet balance --wallet.name validator_wallet
   ```

2. **Connection Issues**
   ```bash
   # Test network connectivity
   ping -c 3 api.degenbrain.com
   
   # Check Bittensor network
   btcli subnet list
   ```

3. **Import Errors**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   
   # Check Python version
   python --version
   ```

4. **Wallet Access Issues**
   ```bash
   # Check wallet permissions
   ls -la ~/.bittensor/wallets/validator_wallet/
   
   # Recreate wallet if needed
   btcli wallet regen_hotkey --wallet.name validator_wallet
   ```

### Performance Issues
- Ensure stable internet (>10 Mbps recommended)
- Monitor system resources (RAM, CPU)
- Check for API rate limiting
- Verify wallet has sufficient stake

## Security Considerations

### Wallet Security
- Never commit wallet files to version control
- Use separate hotkeys for validators vs miners
- Regularly backup coldkey (offline storage)
- Monitor stake and delegation

### Network Security
- Use firewall to restrict access
- Keep system updated
- Monitor for suspicious activity
- Use VPN for remote access

### API Security
- Verify API_URL is correct
- Monitor API response times
- Handle API failures gracefully
- Use HTTPS only

## Production Checklist

Before going live:
- [ ] Wallet created and funded
- [ ] Hotkey registered on subnet 90
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Test deployment successful
- [ ] Monitoring setup
- [ ] Backup procedures in place
- [ ] Security measures implemented

## Testing in Production

Per your request about testing in production without permanently damaging the subnet:

### Safe Testing Approach
1. **Start with minimal stake**: Register with minimum required TAO
2. **Monitor for 24 hours**: Observe validator behavior and network response
3. **Gradual scaling**: Increase stake and activity slowly
4. **Network monitoring**: Watch for any negative impact on subnet metrics

### What won't damage the subnet
- Running a validator with proper registration
- Setting appropriate weights based on miner performance
- Following consensus protocols correctly
- Responding to network queries properly

### What could cause issues
- Setting random or malicious weights
- Spamming the network with excessive queries
- Providing incorrect consensus results
- Running without proper registration

The current implementation follows Bittensor best practices and should be safe for production testing on the live network.

## Support

For issues specific to Subnet 90:
- GitHub: https://github.com/degenpredict/bittensor-subnet-90-brain
- Documentation: This repository's README and docs

For general Bittensor issues:
- Bittensor Docs: https://docs.bittensor.com
- Bittensor Discord: https://discord.gg/bittensor