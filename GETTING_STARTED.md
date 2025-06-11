# Getting Started with Bittensor Subnet 90

This guide walks you through setting up everything needed to run a miner or validator on Bittensor Subnet 90.

## Prerequisites

- Python 3.8 or higher
- Git
- Access to a terminal/command line
- Some TAO tokens for registration (at least 0.1 TAO recommended)

## Step 1: Set Up Python Virtual Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

## Step 2: Install Bittensor CLI

```bash
# Install bittensor
pip install bittensor bittensor-cli

# Verify installation
btcli --version
```

## Step 3: Set Up Wallet

### Create a New Wallet

```bash
# Create a new coldkey (manages funds)
btcli wallet new_coldkey --wallet.name subnet90_wallet

# Create hotkeys for mining/validating
# For a miner:
btcli wallet new_hotkey --wallet.name subnet90_wallet --wallet.hotkey miner

# For a validator:
btcli wallet new_hotkey --wallet.name subnet90_wallet --wallet.hotkey validator
```

### Important: Save Your Mnemonics!
- **Write down your mnemonic phrases** and store them securely
- You'll need these to recover your wallet if needed
- Never share your mnemonics with anyone

### Check Your Wallet

```bash
# List all wallets
btcli wallet list

# Check wallet balance
btcli wallet balance --wallet.name subnet90_wallet
```

## Step 4: Load Wallet with TAO

### Get Your Wallet Address

```bash
# Get your coldkey address to receive TAO
btcli wallet list --wallet.name subnet90_wallet
```

### Options to Get TAO:
1. **Purchase TAO** from exchanges like Binance, Gate.io, or MEXC
2. **Transfer TAO** from another wallet
3. **Request TAO** from the community for testing (Discord/Telegram)

### Verify Your Balance

```bash
btcli wallet balance --wallet.name subnet90_wallet --wallet.hotkey miner
```

## Step 5: Register on Subnet 90

### Check Subnet Information

```bash
# View subnet details
btcli subnet show --netuid 90

# View current validators/miners (top 15)
btcli subnet metagraph --netuid 90 | head -15
```

### Register as a Miner

```bash
btcli subnet register --netuid 90 --wallet.name subnet90_wallet --wallet.hotkey miner --no_prompt
```

### Register as a Validator

```bash
btcli subnet register --netuid 90 --wallet.name subnet90_wallet --wallet.hotkey validator --no_prompt
```

## Step 6: Install Subnet 90 Code

```bash
# Clone the repository
git clone https://github.com/bittensor-subnet-90-brain/bittensor-subnet-90-brain.git
cd bittensor-subnet-90-brain

# Install requirements
pip install -r requirements.txt
```

## Step 7: Run Your Node

### For Miners

```bash
python run_miner.py \
    --netuid 90 \
    --wallet.name subnet90_wallet \
    --wallet.hotkey miner \
    --subtensor.network finney \
    --axon.port 8091
```

### For Validators

```bash
python run_validator.py \
    --netuid 90 \
    --wallet.name subnet90_wallet \
    --wallet.hotkey validator \
    --subtensor.network finney
```

## Useful Commands

### Monitor Your Node

```bash
# Check your registration status
btcli subnet metagraph --netuid 90 | grep <your_hotkey_address>

# View subnet statistics
btcli subnet show --netuid 90

# Check subnet emissions
python check_subnet_emissions.py

# View all participants
python scripts/check_subnet_participants.py --netuid 90
```

### Wallet Management

```bash
# Check balance
btcli wallet balance --wallet.name subnet90_wallet

# Transfer TAO between wallets
btcli wallet transfer --wallet.name source_wallet --dest <destination_address> --amount <amount>

# View wallet history
btcli wallet history --wallet.name subnet90_wallet
```

### Troubleshooting Commands

```bash
# Check if your hotkey is registered
btcli subnet list --wallet.name subnet90_wallet

# View your UID on the subnet
btcli subnet metagraph --netuid 90 --wallet.name subnet90_wallet --wallet.hotkey miner

# Check connectivity
btcli subnet metagraph --netuid 90
```

## Tips

1. **Start Small**: Begin with a miner before running a validator
2. **Monitor Logs**: Keep terminal windows open to monitor your node's activity
3. **Join Community**: Get support in Bittensor Discord/Telegram channels
4. **Keep Software Updated**: Regularly pull latest changes from the repository
5. **Secure Your Wallet**: Never share private keys or mnemonics

## Next Steps

- Read the [README.md](README.md) for more detailed information
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Review [LOCAL_TESTING.md](LOCAL_TESTING.md) for development setup
- See [EMISSIONS_GUIDE.md](EMISSIONS_GUIDE.md) to understand rewards

## Need Help?

- Check the [Bittensor Documentation](https://docs.bittensor.com/)
- Join the Bittensor Discord community
- Open an issue on the GitHub repository