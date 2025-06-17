#!/bin/bash

# Subnet 90 Status Checker
# Quick way to check if your validator and miners are running properly

echo "🔍 SUBNET 90 STATUS CHECK"
echo "========================="
echo ""

# Check validator
echo "🏛️  VALIDATOR STATUS"
echo "===================="
VALIDATOR_RUNNING=$(pgrep -f "run_validator.py" | wc -l)

if [ $VALIDATOR_RUNNING -gt 0 ]; then
    echo "✅ Validator is running"
    VALIDATOR_PID=$(pgrep -f "run_validator.py")
    echo "   PID: $VALIDATOR_PID"
    
    # Check recent activity
    if [ -f "$HOME/logs/degenbrain_validator.log" ]; then
        echo "   Recent activity:"
        tail -3 "$HOME/logs/degenbrain_validator.log" | sed 's/^/     /'
        echo ""
        
        # Check for success indicators
        echo "   Performance metrics (last 10 entries):"
        grep -E "(Found active miners|valid_responses|Statement validation complete)" "$HOME/logs/degenbrain_validator.log" | tail -5 | while read line; do
            echo "     $line"
        done
    fi
else
    echo "❌ Validator is not running"
    echo "   Start with: ./start_validator.sh"
fi

echo ""

# Check miners
echo "⛏️  MINER STATUS"
echo "================"
MINERS_RUNNING=$(pgrep -f "run_miner.py" | wc -l)

echo "Miners running: $MINERS_RUNNING"

if [ $MINERS_RUNNING -gt 0 ]; then
    echo ""
    echo "✅ Active miners:"
    
    # List each miner
    for logfile in "$HOME/logs/degenbrain_miner_"*.log; do
        if [ -f "$logfile" ]; then
            MINER_NAME=$(basename "$logfile" .log | sed 's/degenbrain_miner_//')
            
            # Check if this miner is running
            if pgrep -f "run_miner.py" | xargs ps -p 2>/dev/null | grep -q "run_miner.py"; then
                echo "   📱 $MINER_NAME:"
                
                # Get PID
                MINER_PID=$(pgrep -f "run_miner.py" | head -1)  # Simplified for now
                echo "      PID: $MINER_PID"
                
                # Check recent activity
                if [ -s "$logfile" ]; then
                    LAST_LINE=$(tail -1 "$logfile")
                    if [ -n "$LAST_LINE" ]; then
                        echo "      Last activity: $LAST_LINE"
                    else
                        echo "      ⚠️  No recent log entries"
                    fi
                else
                    echo "      ⚠️  Log file empty"
                fi
            fi
        fi
    done
else
    echo "❌ No miners running"
    echo "   Start with: ./start_miner.sh"
fi

echo ""

# Network connectivity check
echo "🌐 NETWORK CHECK"
echo "================"

echo -n "API connectivity: "
if curl -s --max-time 5 "https://api.subnet90.com" >/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Failed"
    echo "   Check your internet connection"
fi

echo -n "Bittensor network: "
if command -v btcli >/dev/null 2>&1; then
    if timeout 10 btcli subnet list --netuid 90 >/dev/null 2>&1; then
        echo "✅ Connected"
    else
        echo "❌ Failed"
        echo "   Check bittensor connection"
    fi
else
    echo "❌ btcli not found"
fi

echo ""

# Quick recommendations
echo "💡 QUICK ACTIONS"
echo "================"

if [ $VALIDATOR_RUNNING -eq 0 ] && [ $MINERS_RUNNING -eq 0 ]; then
    echo "🚀 Nothing running. Start with:"
    echo "   ./start_validator.sh  (if you want to run a validator)"
    echo "   ./start_miner.sh      (if you want to run miners)"
elif [ $VALIDATOR_RUNNING -gt 0 ] && [ $MINERS_RUNNING -eq 0 ]; then
    echo "🏛️  Validator running, no miners. This is normal for validator-only setups."
elif [ $VALIDATOR_RUNNING -eq 0 ] && [ $MINERS_RUNNING -gt 0 ]; then
    echo "⛏️  Miners running, no validator. This is normal for miner-only setups."
else
    echo "✅ Both validator and miners running. System looks good!"
fi

echo ""
echo "📊 View detailed logs:"
echo "   tail -f $HOME/logs/degenbrain_validator.log"
echo "   tail -f $HOME/logs/degenbrain_miner_miner1.log"
echo ""
echo "🛑 Stop services:"
echo "   pkill -f run_validator.py"
echo "   pkill -f run_miner.py"