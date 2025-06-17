#!/bin/bash

# Subnet 90 Miner - Easy Start Script
# This script will guide you through starting one or multiple miners on Subnet 90

set -e  # Exit on any error

echo "⛏️  SUBNET 90 MINER SETUP"
echo "========================="
echo ""

# Check if we're in the right directory
if [ ! -f "run_miner.py" ]; then
    echo "❌ Error: Please run this script from the bittensor-subnet-90-brain directory"
    echo "   cd /path/to/bittensor-subnet-90-brain"
    echo "   ./start_miner.sh"
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

# Number of miners
echo ""
echo "How many miners do you want to run?"
echo "1) Single miner"
echo "2) Multiple miners (2-5 recommended)"
read -p "Choice (1-2): " MINER_CHOICE

case $MINER_CHOICE in
    2)
        read -p "Number of miners (2-5): " NUM_MINERS
        if [[ ! $NUM_MINERS =~ ^[2-5]$ ]]; then
            echo "❌ Invalid number. Using 3 miners."
            NUM_MINERS=3
        fi
        ;;
    *)
        NUM_MINERS=1
        ;;
esac

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
echo "  Miners: $NUM_MINERS"
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
    echo "  btcli wallet create --wallet.name $WALLET_NAME"
    exit 1
fi

# Function to setup and start a single miner
start_single_miner() {
    local MINER_ID=$1
    local HOTKEY_NAME="miner$MINER_ID"
    
    echo ""
    echo "🔧 Setting up Miner $MINER_ID"
    echo "=========================="
    
    # Check if hotkey exists
    if ! btcli wallet overview --wallet.name "$WALLET_NAME" --wallet.hotkey "$HOTKEY_NAME" >/dev/null 2>&1; then
        echo "⚠️  Hotkey '$HOTKEY_NAME' not found."
        echo ""
        echo "Create it with:"
        echo "  btcli wallet create --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME"
        echo ""
        read -p "Skip this miner and continue? (y/N): " SKIP
        if [[ $SKIP =~ ^[Yy]$ ]]; then
            return
        else
            exit 1
        fi
    fi
    
    # Check if registered
    if ! btcli subnet list --netuid "$SUBNET_UID" | grep -q "$(btcli wallet overview --wallet.name "$WALLET_NAME" --wallet.hotkey "$HOTKEY_NAME" 2>/dev/null | grep "$HOTKEY_NAME" | awk '{print $NF}')"; then
        echo "⚠️  Hotkey '$HOTKEY_NAME' not registered on subnet $SUBNET_UID"
        echo ""
        echo "To register (costs ~1 TAO):"
        echo "  btcli subnet register --netuid $SUBNET_UID --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME"
        echo ""
        read -p "Continue anyway? (y/N): " CONTINUE
        if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    # Check/create miner environment
    MINER_ENV_PATH="$HOME/miners/${HOTKEY_NAME}_env"
    
    if [ ! -d "$MINER_ENV_PATH" ]; then
        echo "Creating environment for $HOTKEY_NAME..."
        mkdir -p "$HOME/miners"
        python3 -m venv "$MINER_ENV_PATH"
        
        source "$MINER_ENV_PATH/bin/activate"
        pip install --upgrade pip
        # CRITICAL: Use CPU torch version to avoid startup hangs
        pip install torch==2.7.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
        pip install bittensor==9.7.0
        pip install -r requirements.txt
        deactivate
        echo "✅ Environment created for $HOTKEY_NAME"
    fi
    
    # Check if miner is already running
    if pgrep -f "run_miner.py.*$HOTKEY_NAME" > /dev/null; then
        echo "⚠️  Miner $HOTKEY_NAME already running!"
        read -p "Restart $HOTKEY_NAME? (y/N): " RESTART
        if [[ $RESTART =~ ^[Yy]$ ]]; then
            echo "Stopping $HOTKEY_NAME..."
            pkill -f "run_miner.py.*$HOTKEY_NAME" || true
            sleep 2
        else
            echo "Skipping $HOTKEY_NAME..."
            return
        fi
    fi
    
    # Create logs directory
    mkdir -p "$HOME/logs"
    
    # Start miner
    echo "Starting miner $HOTKEY_NAME..."
    
    # Set environment variables for this miner
    export WALLET_NAME="$WALLET_NAME"
    export HOTKEY_NAME="$HOTKEY_NAME"
    export API_URL="$API_URL"
    export NETWORK="$NETWORK"
    export SUBNET_UID="$SUBNET_UID"
    
    # Activate environment and start
    source "$MINER_ENV_PATH/bin/activate"
    nohup python3 run_miner.py > "$HOME/logs/degenbrain_miner_${HOTKEY_NAME}.log" 2>&1 &
    local MINER_PID=$!
    
    echo "✅ Miner $HOTKEY_NAME started with PID: $MINER_PID"
    
    # Check if it started successfully
    sleep 3
    if ps -p $MINER_PID > /dev/null 2>&1; then
        echo "✅ Miner $HOTKEY_NAME is running successfully!"
    else
        echo "❌ Miner $HOTKEY_NAME failed to start. Check logs:"
        echo "  tail -10 $HOME/logs/degenbrain_miner_${HOTKEY_NAME}.log"
    fi
}

# Start miners
echo ""
echo "🚀 Starting Miners"
echo "=================="

for ((i=1; i<=NUM_MINERS; i++)); do
    start_single_miner $i
done

# Final status
echo ""
echo "📊 Final Status"
echo "==============="

RUNNING_MINERS=$(pgrep -f "run_miner.py" | wc -l)
echo "Miners running: $RUNNING_MINERS"

if [ $RUNNING_MINERS -gt 0 ]; then
    echo ""
    echo "✅ Active miner processes:"
    ps aux | grep "run_miner.py" | grep -v grep | awk '{print $2, $11, $12}' | while read pid cmd args; do
        echo "  PID $pid: $args"
    done
fi

echo ""
echo "📈 Monitor your miners:"
echo "  All logs: ls -la $HOME/logs/degenbrain_miner_*.log"
echo "  Live logs: tail -f $HOME/logs/degenbrain_miner_miner1.log"
echo "  Processes: ps aux | grep run_miner"
echo "  Stop all: pkill -f run_miner.py"
echo ""

echo "🎉 Miner setup complete!"
echo ""
echo "💡 Useful commands:"
echo "  Check balance: btcli wallet balance --wallet.name $WALLET_NAME"
echo "  View subnet: btcli subnet list --netuid $SUBNET_UID"
echo "  Check registration: btcli subnet list --netuid $SUBNET_UID | grep \$(btcli wallet overview --wallet.name $WALLET_NAME | tail -n +3 | awk '{print \$NF}')"

if [ $RUNNING_MINERS -eq 0 ]; then
    echo ""
    echo "⚠️  No miners started successfully. Check the logs and requirements above."
    exit 1
fi