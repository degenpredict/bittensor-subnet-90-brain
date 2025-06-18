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

# Check if wallet exists first
if ! btcli wallet overview --wallet.name "$WALLET_NAME" >/dev/null 2>&1; then
    echo "❌ Wallet '$WALLET_NAME' not found."
    echo ""
    echo "Please create your wallet first:"
    echo "  btcli wallet create --wallet.name $WALLET_NAME"
    exit 1
fi

# Show available hotkeys and let user choose
echo ""
echo "Available hotkeys in wallet '$WALLET_NAME':"
HOTKEYS=$(btcli wallet list 2>/dev/null | sed -n "/Coldkey $WALLET_NAME/,/^├──\|^└──/p" | grep "Hotkey" | sed 's/.*Hotkey \([^ ]*\).*/\1/')
if [ -z "$HOTKEYS" ]; then
    echo "❌ No hotkeys found in wallet '$WALLET_NAME'"
    echo ""
    echo "Create a hotkey first:"
    echo "  btcli wallet new-hotkey --wallet.name $WALLET_NAME"
    exit 1
fi

# List hotkeys with numbers
echo "$HOTKEYS" | nl -w2 -s') '
echo ""
read -p "Enter hotkey name or number (or press Enter for first available): " SELECTED_HOTKEY

if [ -z "$SELECTED_HOTKEY" ]; then
    SELECTED_HOTKEY=$(echo "$HOTKEYS" | head -n1)
elif [[ "$SELECTED_HOTKEY" =~ ^[0-9]+$ ]]; then
    # User entered a number, convert to hotkey name
    SELECTED_HOTKEY=$(echo "$HOTKEYS" | sed -n "${SELECTED_HOTKEY}p")
    if [ -z "$SELECTED_HOTKEY" ]; then
        echo "❌ Invalid number. Please choose 1-$(echo "$HOTKEYS" | wc -l)"
        exit 1
    fi
fi

# Validate selected hotkey exists
if ! echo "$HOTKEYS" | grep -q "^$SELECTED_HOTKEY$"; then
    echo "❌ Hotkey '$SELECTED_HOTKEY' not found in wallet '$WALLET_NAME'"
    exit 1
fi

echo "✅ Using hotkey: $SELECTED_HOTKEY"

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

# Miner strategy
echo ""
echo "Select miner strategy:"
echo "1) dummy - Simple mock responses (default - works without API keys)"
echo "2) hybrid - Training mode - compare your AI against official resolutions"
echo "3) ai_reasoning - Full independence - analyze statements without assistance"
read -p "Choice (1-3): " STRATEGY_CHOICE

case $STRATEGY_CHOICE in
    2)
        MINER_STRATEGY="hybrid"
        ;;
    3)
        MINER_STRATEGY="ai_reasoning"
        ;;
    *)
        MINER_STRATEGY="dummy"
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
echo "  Strategy: $MINER_STRATEGY"
echo "  Network: $NETWORK"
echo "  Subnet: $SUBNET_UID"
echo "  API: $API_URL"
echo ""

# Wallet and hotkey already validated above

# Function to setup and start a single miner
start_single_miner() {
    local MINER_ID=$1
    local HOTKEY_NAME
    
    if [ $NUM_MINERS -eq 1 ]; then
        # Single miner - use selected hotkey
        HOTKEY_NAME="$SELECTED_HOTKEY"
    else
        # Multiple miners - need to ask for each hotkey name
        echo ""
        echo "🔧 Setting up Miner $MINER_ID"
        echo "=========================="
        echo "Available hotkeys:"
        echo "$HOTKEYS" | nl -w2 -s') '
        echo ""
        read -p "Enter hotkey name or number for miner $MINER_ID: " HOTKEY_NAME
        
        # Handle number input
        if [[ "$HOTKEY_NAME" =~ ^[0-9]+$ ]]; then
            HOTKEY_NAME=$(echo "$HOTKEYS" | sed -n "${HOTKEY_NAME}p")
            if [ -z "$HOTKEY_NAME" ]; then
                echo "⚠️  Invalid number. Please choose 1-$(echo "$HOTKEYS" | wc -l)"
                read -p "Skip this miner and continue? (y/N): " SKIP
                if [[ $SKIP =~ ^[Yy]$ ]]; then
                    return
                else
                    exit 1
                fi
            fi
        fi
        
        # Validate hotkey exists
        if ! echo "$HOTKEYS" | grep -q "^$HOTKEY_NAME$"; then
            echo "⚠️  Hotkey '$HOTKEY_NAME' not found in wallet."
            read -p "Skip this miner and continue? (y/N): " SKIP
            if [[ $SKIP =~ ^[Yy]$ ]]; then
                return
            else
                exit 1
            fi
        fi
    fi
    
    echo ""
    echo "🔧 Setting up Miner $MINER_ID with hotkey: $HOTKEY_NAME"
    echo "=================================================="
    
    # Check if registered
    echo "🔍 Checking registration for $HOTKEY_NAME..."
    WALLET_JSON=$(btcli wallet overview --wallet.name "$WALLET_NAME" --wallet.hotkey "$HOTKEY_NAME" --json-output 2>/dev/null)
    if echo "$WALLET_JSON" | grep -q "\"netuid\": $SUBNET_UID"; then
        echo "✅ Hotkey '$HOTKEY_NAME' is registered on subnet $SUBNET_UID"
    else
        echo "⚠️  Hotkey '$HOTKEY_NAME' not registered on subnet $SUBNET_UID"
        echo ""
        echo "To register (costs ~0.0136 TAO recycled):"
        echo "  btcli subnets register --netuid $SUBNET_UID --wallet.name $WALLET_NAME --wallet.hotkey $HOTKEY_NAME"
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
    export MINER_STRATEGY="$MINER_STRATEGY"
    export LOG_FILE="$HOME/logs/degenbrain_miner_${HOTKEY_NAME}.log"
    export LOG_LEVEL="INFO"
    
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
echo "  View subnet: btcli subnets show --netuid $SUBNET_UID"
echo "  Check registration: btcli wallet overview --wallet.name $WALLET_NAME --json-output | grep '\"netuid\": $SUBNET_UID'"

if [ $RUNNING_MINERS -eq 0 ]; then
    echo ""
    echo "⚠️  No miners started successfully. Check the logs and requirements above."
    exit 1
fi