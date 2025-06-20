# Bittensor Subnet 90 (DegenBrain) - Production Setup Guide

**Status: ✅ FULLY OPERATIONAL | Validator + 3 Miners Running Successfully**

A Bittensor subnet for automated verification of prediction market statements through distributed consensus.

## 🚀 Quick Start (Easy Mode)

### Option 1: Interactive Setup (Recommended)
```bash
# Run interactive configuration wizard
./start_fresh.sh

# Start all processes
./pm2_setup.sh all
```

### Option 2: Manual Configuration
```bash
# 1. Set up Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
pip install bittensor==9.7.0
pip install -r requirements.txt

# 2. Copy template and edit manually
cp subnet_config.yaml.example subnet_config.yaml
nano subnet_config.yaml  # Edit wallet names, paths, etc.

# 3. Start all processes
./pm2_setup.sh all
```

**Check Status:**
```bash
pm2 status
pm2 logs
```

**Stop Everything:**
```bash
pm2 stop all
```

### Running Specific Components

**Validator Only:**
```bash
./pm2_setup.sh validator
```

**Miners Only:**
```bash
./pm2_setup.sh miners
```

**Individual Processes:**
```bash
pm2 start validator
pm2 start miner1
pm2 stop miner2
pm2 restart miner3
```

**Disable Components (in subnet_config.yaml):**
```yaml
validator:
  enabled: false  # Disable validator

miners:
  - id: miner1
    enabled: false  # Disable specific miner
```

That's it! The scripts will guide you through everything using PM2 process management.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Validator Setup](#validator-setup)
5. [Miner Setup](#miner-setup)
6. [Running the System](#running-the-system)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Configuration Reference](#configuration-reference)

---

## 🔄 System Overview

The subnet enables automated verification of prediction statements by distributing verification tasks to miners who provide evidence-based resolution decisions.

### How It Works
```
DegenBrain API → Validator → Miners → Consensus → Bittensor Weights
```

1. **Validator** fetches statement batches from `https://api.subnet90.com/api/test/next-chunk` (every 16+ minutes due to rate limiting)
2. **Distributes** statements to registered miners on subnet 90
3. **Miners** query `https://api.subnet90.com/api/resolutions/{id}` for official resolutions (training mode)
4. **Miners** return resolution + confidence + evidence to validator
5. **Validator** calculates consensus and scores miners based on performance
6. **Sets weights** on Bittensor to reward high-performing miners

---

## ✅ Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.11+
- **RAM**: 2GB+ for validator, 1GB+ per miner
- **Storage**: 10GB+ available space
- **Network**: Stable internet connection

### Bittensor Requirements
- **TAO Balance**: 1+ TAO for registration and staking
- **Bittensor CLI**: Installed and configured
- **Wallets**: Created with coldkey and hotkeys

---

## 🛠️ Environment Setup

### 1. Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install other dependencies
sudo apt install git curl build-essential -y
```

### 2. Install Bittensor
```bash
# Install via pip
pip install bittensor

# Or install latest from source
git clone https://github.com/opentensor/bittensor.git
cd bittensor
pip install -e .
```

### 3. Clone Repository
```bash
cd /home/$(whoami)
git clone https://github.com/degenpredict/bittensor-subnet-90-brain.git
cd bittensor-subnet-90-brain
```

### 4. Create Python Environments

#### For Validator
```bash
# Create validator environment
python3.11 -m venv /home/$(whoami)/validators/validator_env
source /home/$(whoami)/validators/validator_env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
pip install bittensor==9.7.0
pip install -r requirements.txt
deactivate
```

#### For Miners (repeat for each miner)
```bash
# Create miner environments
for miner in miner1 miner2 miner3; do
    python3.11 -m venv /home/$(whoami)/miners/${miner}_env
    source /home/$(whoami)/miners/${miner}_env/bin/activate
    
    # Install dependencies (CPU torch version - CRITICAL!)
    pip install --upgrade pip
    pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
    pip install bittensor==9.7.0
    pip install -r requirements.txt
    
    deactivate
done
```

**⚠️ IMPORTANT**: Use CPU torch version (`torch==2.7.1+cpu`) not CUDA version, as CUDA causes startup hangs.

---

## 🏛️ Validator Setup

### 1. Create Bittensor Wallet
```bash
# Create validator wallet
btcli wallet create --wallet.name my_wallet --wallet.hotkey validator

# Check balance (need 1+ TAO for registration)
btcli wallet balance --wallet.name my_wallet
```

### 2. Register on Subnet 90
```bash
# Register validator (costs ~1 TAO)
btcli subnet register --netuid 90 --wallet.name my_wallet --wallet.hotkey validator
```

### 3. Create Validator Startup Script
```bash
cat > /home/$(whoami)/start_degenbrain_validator.sh << 'EOF'
#!/bin/bash

echo "🏛️ Starting DegenBrain Validator"
echo "================================="

cd /home/$(whoami)/bittensor-subnet-90-brain

# Set environment variables
export WALLET_NAME="my_wallet"
export HOTKEY_NAME="validator"
export API_URL="https://api.subnet90.com"
export NETWORK="finney"
export SUBNET_UID="90"

# Activate validator environment
source /home/$(whoami)/validators/validator_env/bin/activate

# Create logs directory
mkdir -p /home/$(whoami)/logs

# Start validator
echo "Starting validator..."
nohup python3 run_validator.py > /home/$(whoami)/logs/degenbrain_validator.log 2>&1 &
VALIDATOR_PID=$!

echo "✅ Validator started with PID: $VALIDATOR_PID"
echo "📄 Logs: tail -f /home/$(whoami)/logs/degenbrain_validator.log"

# Check if it started
sleep 3
if ps -p $VALIDATOR_PID > /dev/null 2>&1; then
    echo "✅ Validator is running successfully"
else
    echo "❌ Validator failed to start - check logs"
fi
EOF

chmod +x /home/$(whoami)/start_degenbrain_validator.sh
```

---

## ⛏️ Miner Setup

### 1. Create Miner Wallets
```bash
# Create 3 miner hotkeys
for i in {1..3}; do
    btcli wallet create --wallet.name my_wallet --wallet.hotkey miner$i
done
```

### 2. Register Miners on Subnet
```bash
# Register each miner (costs ~1 TAO each)
for i in {1..3}; do
    btcli subnet register --netuid 90 --wallet.name my_wallet --wallet.hotkey miner$i
done
```

### 3. Create Miner Startup Script
```bash
cat > /home/$(whoami)/start_degenbrain_miners.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting DegenBrain Miners"
echo "============================="

cd /home/$(whoami)/bittensor-subnet-90-brain

# Function to start a miner
start_miner() {
    local hotkey=$1
    local expected_uid=$2
    
    echo "Starting miner $hotkey..."
    
    # Set environment variables
    export WALLET_NAME="my_wallet"
    export HOTKEY_NAME="$hotkey"
    export API_URL="https://api.subnet90.com"
    export NETWORK="finney"
    export SUBNET_UID="90"
    
    # Activate correct miner environment
    source /home/$(whoami)/miners/${hotkey}_env/bin/activate
    
    # Create logs directory
    mkdir -p /home/$(whoami)/logs
    
    # Start miner in background
    nohup python3 run_miner.py > /home/$(whoami)/logs/degenbrain_miner_${hotkey}.log 2>&1 &
    local MINER_PID=$!
    
    echo "  ✅ Started miner $hotkey with PID: $MINER_PID"
    echo "  📄 Logs: tail -f /home/$(whoami)/logs/degenbrain_miner_${hotkey}.log"
    
    # Check if it started
    sleep 2
    if ps -p $MINER_PID > /dev/null 2>&1; then
        echo "  ✅ Miner $hotkey is running"
    else
        echo "  ❌ Miner $hotkey failed to start"
    fi
    echo
}

# Start all 3 miners
start_miner "miner1" "124"
start_miner "miner2" "125" 
start_miner "miner3" "126"

echo "📊 All miners started. Check processes with:"
echo "   ps aux | grep run_miner"
EOF

chmod +x /home/$(whoami)/start_degenbrain_miners.sh
```

### 4. Configure Miner Strategy (Optional)

Miners support different verification strategies. Set `MINER_STRATEGY` in your `.env` file:

```bash
# Copy the example configuration
cp .env.example .env

# Edit your strategy (choose one):
MINER_STRATEGY=dummy      # Default: Works without any API keys
MINER_STRATEGY=hybrid     # Training mode: Uses official resolutions + optional AI
MINER_STRATEGY=ai_reasoning  # Full independence: Requires AI API keys
```

#### Strategy Comparison:

| Strategy | API Keys Required | Description |
|----------|------------------|-------------|
| **dummy** | None | Simple mock responses - perfect for testing |
| **hybrid** | None (optional AI) | Training mode - uses official resolutions from `api.subnet90.com` |  
| **ai_reasoning** | AI keys required | Full independence - analyzes statements without assistance |

#### Hybrid Mode (Recommended for Training)
```bash
# Works immediately with zero configuration
MINER_STRATEGY=hybrid

# Optional: Add AI keys for unknown statements  
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

**Hybrid mode** is perfect for learning:
- ✅ **Zero setup** - works without any API keys
- ✅ **Official resolutions** - learns from verified answers  
- ✅ **Training phase** - prepares miners for independent analysis
- 🔄 **Temporary** - will be phased out as subnet matures

---

## 🚀 Running the System

### Easy Way (Recommended - PM2)
```bash
# Interactive setup (first time)
./start_fresh.sh

# Start all processes
./pm2_setup.sh all

# Check everything
pm2 status
pm2 logs
```

### Manual Way (Advanced Users)

<details>
<summary>Click to expand manual instructions</summary>

#### Start Validator
```bash
# Start the validator
./start_degenbrain_validator.sh

# Monitor logs
tail -f /home/$(whoami)/logs/degenbrain_validator.log
```

#### Start Miners
```bash
# Start all miners
./start_degenbrain_miners.sh

# Monitor individual miners
tail -f /home/$(whoami)/logs/degenbrain_miner_miner1.log
tail -f /home/$(whoami)/logs/degenbrain_miner_miner2.log
tail -f /home/$(whoami)/logs/degenbrain_miner_miner3.log
```

#### Verify Everything is Running
```bash
# Check all processes
ps aux | grep -E "(run_validator|run_miner)" | grep -v grep

# Expected output:
# python3 run_validator.py  (1 process)
# python3 run_miner.py     (3 processes)
```

</details>

---

## 📊 Monitoring & Troubleshooting

### Check System Status
```bash
# Quick status check
echo "=== VALIDATOR STATUS ==="
ps aux | grep run_validator | grep -v grep && echo "✅ Validator Running" || echo "❌ Validator Stopped"

echo "=== MINER STATUS ==="
MINER_COUNT=$(ps aux | grep run_miner | grep -v grep | wc -l)
echo "Miners Running: $MINER_COUNT/3"

echo "=== RECENT VALIDATOR LOGS ==="
tail -5 /home/$(whoami)/logs/degenbrain_validator.log

echo "=== NETWORK METRICS ==="
tail -10 /home/$(whoami)/logs/degenbrain_validator.log | grep -E "(Found active miners|valid_responses)"
```

### Check Validator Performance
```bash
# Look for key metrics in validator logs
grep -E "(Statement validation complete|Found active miners|valid_responses)" /home/$(whoami)/logs/degenbrain_validator.log | tail -10

# Expected patterns:
# "Found active miners count=14"
# "valid_responses=3" (or more)
# "Statement validation complete confidence=XX.X consensus=TRUE/FALSE"
```

### Check Miner Performance
```bash
# Check if miners are responding
for miner in miner1 miner2 miner3; do
    echo "=== $miner Status ==="
    if ps aux | grep "run_miner" | grep -v grep > /dev/null; then
        echo "✅ Process running"
    else
        echo "❌ Process stopped"
    fi
    
    # Check for recent activity
    if [ -f "/home/$(whoami)/logs/degenbrain_miner_${miner}.log" ]; then
        LAST_LOG=$(tail -1 /home/$(whoami)/logs/degenbrain_miner_${miner}.log)
        if [ -n "$LAST_LOG" ]; then
            echo "Last activity: $LAST_LOG"
        else
            echo "⚠️ No recent log entries"
        fi
    fi
    echo
done
```

### Common Issues & Solutions

#### 1. Miner Won't Start
```bash
# Check environment activation
source /home/$(whoami)/miners/miner1_env/bin/activate
python3 -c "import torch; print(f'Torch version: {torch.__version__}')"

# Should show: Torch version: 2.7.1+cpu
# If it shows CUDA version, reinstall CPU torch:
pip uninstall torch
pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
```

#### 2. Validator Not Finding Miners
```bash
# Check if miners are registered
btcli subnet list --netuid 90 | grep $(btcli wallet overview --wallet.name my_wallet | tail -n +3)
```

#### 3. No Valid Responses
```bash
# Check miner logs for errors
for miner in miner1 miner2 miner3; do
    echo "=== $miner errors ==="
    grep -i error /home/$(whoami)/logs/degenbrain_miner_${miner}.log | tail -5
done
```

#### 4. Restart Services
```bash
# Stop all services
pkill -f "run_validator.py"
pkill -f "run_miner.py"

# Wait a moment
sleep 5

# Restart
./start_degenbrain_validator.sh
sleep 10
./start_degenbrain_miners.sh
```

---

## ⚙️ Configuration Reference

### Environment Variables

#### Required for All Components
```bash
export WALLET_NAME="my_wallet"     # Bittensor wallet name
export API_URL="https://api.subnet90.com"  # DegenBrain API endpoint
export NETWORK="finney"                  # Bittensor network
export SUBNET_UID="90"                   # Subnet number
```

#### Validator Specific
```bash
export HOTKEY_NAME="validator"           # Validator hotkey name
export VALIDATOR_ID="my_validator"       # Unique validator identifier (required for API)
export VALIDATOR_PORT="8090"             # Validator port (optional)
```

#### Miner Specific
```bash
export HOTKEY_NAME="miner1"              # Miner hotkey name (miner1, miner2, miner3)
export MINER_PORT="8091"                 # Miner port (optional)
```

### File Locations
```
/home/$(whoami)/
├── bittensor-subnet-90-brain/           # Main codebase
├── logs/                                # All log files
│   ├── degenbrain_validator.log
│   ├── degenbrain_miner_miner1.log
│   ├── degenbrain_miner_miner2.log
│   └── degenbrain_miner_miner3.log
├── validators/
│   └── validator_env/                   # Validator Python environment
├── miners/
│   ├── miner1_env/                      # Miner Python environments
│   ├── miner2_env/
│   └── miner3_env/
├── start_degenbrain_validator.sh        # Validator startup script
└── start_degenbrain_miners.sh          # Miner startup script
```

### Key Dependencies
```
Python 3.11+
bittensor==9.7.0
torch==2.7.1+cpu          # CRITICAL: Use CPU version
structlog
httpx
tenacity
pydantic
```

---

## 🎯 Success Indicators

When everything is working correctly, you should see:

### Validator Logs
```
Found active miners count=14
Received miner responses total_queried=14 valid_responses=3
Statement validation complete confidence=XX.X consensus=TRUE/FALSE
Weights set successfully
```

### Miner Logs
```
Verification complete resolution=TRUE/FALSE confidence=XX.X
Processing verification request statement=...
```

### Process Check
```bash
# Should show 4 processes total
ps aux | grep -E "(run_validator|run_miner)" | grep -v grep | wc -l
# Output: 4
```

---

## 📞 Support

For issues or questions:
1. Check the logs first: `/home/$(whoami)/logs/`
2. Verify environment setup and dependencies
3. Ensure all processes are running
4. Check network connectivity and API access

The system is designed to be robust and self-healing. Most issues can be resolved by restarting the affected components.

---

## 📚 Additional Documentation

- **`ARCHITECTURE.md`** - Detailed technical architecture documentation
- **`.env.example`** - Configuration template with all available options