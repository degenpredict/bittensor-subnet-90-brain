#!/bin/bash

# Subnet 90 - Stop All Services
# Simple script to stop all running validators and miners

echo "🛑 STOPPING SUBNET 90 SERVICES"
echo "==============================="
echo ""

# Check what's running first
VALIDATOR_RUNNING=$(pgrep -f "run_validator.py" | wc -l)
MINERS_RUNNING=$(pgrep -f "run_miner.py" | wc -l)

echo "Current status:"
echo "  Validators running: $VALIDATOR_RUNNING"
echo "  Miners running: $MINERS_RUNNING"
echo ""

if [ $VALIDATOR_RUNNING -eq 0 ] && [ $MINERS_RUNNING -eq 0 ]; then
    echo "✅ No services running. Nothing to stop."
    exit 0
fi

# Ask for confirmation
read -p "Stop all services? (y/N): " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Stop validator
if [ $VALIDATOR_RUNNING -gt 0 ]; then
    echo "🏛️  Stopping validator..."
    pkill -f "run_validator.py"
    sleep 2
    
    # Check if stopped
    if pgrep -f "run_validator.py" > /dev/null; then
        echo "⚠️  Validator still running, forcing stop..."
        pkill -9 -f "run_validator.py"
    fi
    echo "✅ Validator stopped"
fi

# Stop miners
if [ $MINERS_RUNNING -gt 0 ]; then
    echo "⛏️  Stopping miners..."
    pkill -f "run_miner.py"
    sleep 2
    
    # Check if stopped
    STILL_RUNNING=$(pgrep -f "run_miner.py" | wc -l)
    if [ $STILL_RUNNING -gt 0 ]; then
        echo "⚠️  $STILL_RUNNING miners still running, forcing stop..."
        pkill -9 -f "run_miner.py"
    fi
    echo "✅ All miners stopped"
fi

echo ""
echo "🔍 Final check..."
sleep 1

FINAL_VALIDATOR=$(pgrep -f "run_validator.py" | wc -l)
FINAL_MINERS=$(pgrep -f "run_miner.py" | wc -l)

if [ $FINAL_VALIDATOR -eq 0 ] && [ $FINAL_MINERS -eq 0 ]; then
    echo "✅ All services stopped successfully!"
else
    echo "⚠️  Some processes may still be running:"
    echo "  Validators: $FINAL_VALIDATOR"
    echo "  Miners: $FINAL_MINERS"
    echo ""
    echo "Check with: ps aux | grep -E '(run_validator|run_miner)'"
fi

echo ""
echo "💡 To restart:"
echo "  ./start_validator.sh  (for validator)"
echo "  ./start_miner.sh      (for miners)"