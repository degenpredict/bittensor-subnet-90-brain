#!/bin/bash

# Subnet 90 Validator - Easy Start Script
# This script will guide you through starting a validator on Subnet 90

set -e  # Exit on any error

echo "🏛️  SUBNET 90 VALIDATOR SETUP"
echo "============================"
echo ""

# Check if we're in the right directory
if [ ! -f "run_validator.py" ]; then
    echo "❌ Error: Please run this script from the bittensor-subnet-90-brain directory"
    echo "   cd /path/to/bittensor-subnet-90-brain"
    echo "   ./start_validator.sh"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python3 not found. Please install Python 3.11+"
    exit 1
fi

if ! command_exists btcli; then
    echo "❌ Bittensor CLI not found. Please install bittensor:"
    echo "   pip install bittensor"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Get user configuration
echo "📝 Configuration Setup"
echo "======================"

# Wallet name
read -p "Enter your wallet name (default: my_wallet): " WALLET_NAME
WALLET_NAME=${WALLET_NAME:-my_wallet}

# Hotkey name
read -p "Enter your validator hotkey name (default: validator): " HOTKEY_NAME
HOTKEY_NAME=${HOTKEY_NAME:-validator}

# Validator ID
read -p "Enter your validator ID (unique identifier for API): " VALIDATOR_ID
while [ -z "$VALIDATOR_ID" ]; do
    echo "❌ Validator ID is required for API communication"
    read -p "Enter your validator ID (unique identifier for API): " VALIDATOR_ID
done

# Network
echo ""
echo "Select Bittensor network:"
echo "1) finney (mainnet - default)"
echo "2) test (testnet)"
read -p "Choice (1-2): " NETWORK_CHOICE

case $NETWORK_CHOICE in
    2)
        NETWORK="test"
        SUBNET_UID="90"
        ;;
    *)
        NETWORK="finney"
        SUBNET_UID="90"
        ;;
esac

# API URL
API_URL="https://api.subnet90.com"

echo ""
echo "📋 Configuration Summary:"
echo "  Wallet: $WALLET_NAME"
echo "  Hotkey: $HOTKEY_NAME"
echo "  Validator ID: $VALIDATOR_ID"
echo "  Network: $NETWORK"
echo "  Subnet: $SUBNET_UID"
echo "  API: $API_URL"
echo ""

# Check if wallet exists
echo "🔑 Checking wallet..."
if ! btcli wallet overview --wallet.name "$WALLET_NAME" >/dev/null 2>&1; then
    echo "❌ Wallet '$WALLET_NAME' not found."
    echo ""
    echo "Please create your wallet first:"
    echo "  btcli wallet create --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME"
    echo ""
    echo "Then ensure you have TAO for registration:"
    echo "  btcli wallet balance --wallet.name $WALLET_NAME"
    exit 1
fi

# Check if registered
echo "🔍 Checking registration..."
if ! btcli subnet list --netuid "$SUBNET_UID" | grep -q "$(btcli wallet overview --wallet.name "$WALLET_NAME" --wallet.hotkey "$HOTKEY_NAME" 2>/dev/null | grep "$HOTKEY_NAME" | awk '{print $NF}')"; then
    echo "⚠️  Hotkey '$HOTKEY_NAME' not registered on subnet $SUBNET_UID"
    echo ""
    echo "To register (costs ~1 TAO):"
    echo "  btcli subnet register --netuid $SUBNET_UID --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME"
    echo ""
    read -p "Continue anyway? (y/N): " CONTINUE
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check/create validator environment
VALIDATOR_ENV_PATH="$HOME/validators/validator_env"
echo "🐍 Checking Python environment..."

if [ ! -d "$VALIDATOR_ENV_PATH" ]; then
    echo "Creating validator environment at $VALIDATOR_ENV_PATH..."
    mkdir -p "$HOME/validators"
    python3 -m venv "$VALIDATOR_ENV_PATH"
    
    echo "Installing dependencies..."
    source "$VALIDATOR_ENV_PATH/bin/activate"
    pip install --upgrade pip
    pip install torch==2.7.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
    pip install bittensor==9.7.0
    pip install -r requirements.txt
    deactivate
fi

# Create logs directory
mkdir -p "$HOME/logs"

# Check if validator is already running
if pgrep -f "run_validator.py" > /dev/null; then
    echo "⚠️  Validator already running!"
    echo ""
    echo "Current validator process:"
    ps aux | grep "run_validator.py" | grep -v grep
    echo ""
    read -p "Stop current validator and restart? (y/N): " RESTART
    if [[ $RESTART =~ ^[Yy]$ ]]; then
        echo "Stopping current validator..."
        pkill -f "run_validator.py"
        sleep 3
    else
        echo "Exiting..."
        exit 0
    fi
fi

# Start validator
echo ""
echo "🚀 Starting Validator"
echo "===================="

# Set environment variables
export WALLET_NAME="$WALLET_NAME"
export HOTKEY_NAME="$HOTKEY_NAME"
export VALIDATOR_ID="$VALIDATOR_ID"
export API_URL="$API_URL"
export NETWORK="$NETWORK"
export SUBNET_UID="$SUBNET_UID"

# Activate environment
source "$VALIDATOR_ENV_PATH/bin/activate"

# Start validator
echo "Starting validator..."
nohup python3 run_validator.py > "$HOME/logs/degenbrain_validator.log" 2>&1 &
VALIDATOR_PID=$!

echo "✅ Validator started with PID: $VALIDATOR_PID"
echo ""
echo "📊 Monitor your validator:"
echo "  Logs: tail -f $HOME/logs/degenbrain_validator.log"
echo "  Status: ps aux | grep run_validator"
echo "  Stop: pkill -f run_validator.py"
echo ""

# Check if it started successfully
sleep 5
if ps -p $VALIDATOR_PID > /dev/null 2>&1; then
    echo "✅ Validator is running successfully!"
    echo ""
    echo "📈 Watch for these success indicators in logs:"
    echo "  - 'Found active miners count=X'"
    echo "  - 'Received miner responses'"
    echo "  - 'Weights set successfully'"
    echo ""
else
    echo "❌ Validator failed to start. Check logs:"
    echo "  tail -20 $HOME/logs/degenbrain_validator.log"
    exit 1
fi

echo "🎉 Validator setup complete!"
echo ""
echo "💡 Useful commands:"
echo "  Check balance: btcli wallet balance --wallet.name $WALLET_NAME"
echo "  View subnet: btcli subnet list --netuid $SUBNET_UID"
echo "  Monitor logs: tail -f $HOME/logs/degenbrain_validator.log"