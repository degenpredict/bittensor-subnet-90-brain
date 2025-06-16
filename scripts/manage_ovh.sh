#!/bin/bash
# Management script for OVH KS-4 Subnet 90 deployment

WALLET_NAME=${WALLET_NAME:-"subnet90_wallet"}

show_help() {
    echo "🧠 Subnet 90 Management - OVH KS-4"
    echo "=================================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status     - Show all service status"
    echo "  logs       - Show recent logs"
    echo "  start      - Start all services"
    echo "  stop       - Stop all services"
    echo "  restart    - Restart all services"
    echo "  monitor    - Start monitoring dashboard"
    echo "  bootstrap  - Bootstrap subnet (set initial weights)"
    echo "  register   - Register all hotkeys on subnet"
    echo "  balance    - Check wallet balances"
    echo "  subnet     - Show subnet info"
    echo "  update     - Update code and restart"
    echo ""
    echo "Environment:"
    echo "  WALLET_NAME = $WALLET_NAME"
}

check_status() {
    echo "📊 Service Status:"
    sudo supervisorctl status
    echo ""
    
    echo "💰 Wallet Status:"
    if [ -d "/home/subnet90/.bittensor/wallets/$WALLET_NAME" ]; then
        source /home/subnet90/validators/validator_env/bin/activate
        cd /home/subnet90/bittensor-subnet-90-brain
        btcli wallet balance --wallet.name $WALLET_NAME 2>/dev/null || echo "❌ Cannot check balance"
    else
        echo "❌ Wallet not found: $WALLET_NAME"
    fi
    echo ""
    
    echo "🌐 Network Status:"
    curl -s -o /dev/null -w "API Response: %{http_code}\n" https://api.degenbrain.com/health || echo "❌ API check failed"
}

show_logs() {
    echo "📋 Recent Logs:"
    echo ""
    echo "=== Validator ==="
    sudo tail -n 10 /home/subnet90/logs/validator.out.log 2>/dev/null || echo "No validator logs"
    echo ""
    echo "=== Miner 1 ==="
    sudo tail -n 5 /home/subnet90/logs/miner1.out.log 2>/dev/null || echo "No miner1 logs"
    echo ""
    echo "For live logs: sudo supervisorctl tail -f all"
}

start_services() {
    echo "🚀 Starting all services..."
    sudo supervisorctl start all
    echo "✅ Services started"
}

stop_services() {
    echo "🛑 Stopping all services..."
    sudo supervisorctl stop all
    echo "✅ Services stopped"
}

restart_services() {
    echo "🔄 Restarting all services..."
    sudo supervisorctl restart all
    echo "✅ Services restarted"
}

monitor_dashboard() {
    echo "📊 Starting monitoring dashboard..."
    echo "Access at: http://$(curl -s ifconfig.me)/"
    /home/subnet90/monitor.sh
}

bootstrap_subnet() {
    echo "🎯 Bootstrapping subnet..."
    source /home/subnet90/validators/validator_env/bin/activate
    cd /home/subnet90/bittensor-subnet-90-brain
    export WALLET_NAME=$WALLET_NAME
    python scripts/bootstrap_subnet.py
}

register_hotkeys() {
    echo "📝 Registering hotkeys..."
    source /home/subnet90/validators/validator_env/bin/activate
    
    echo "Registering validator..."
    btcli subnet register --netuid 90 --wallet.name $WALLET_NAME --wallet.hotkey validator --no_prompt
    
    for i in {1..3}; do
        echo "Registering miner${i}..."
        btcli subnet register --netuid 90 --wallet.name $WALLET_NAME --wallet.hotkey miner${i} --no_prompt
    done
    
    echo "✅ Registration complete"
}

check_balance() {
    echo "💰 Checking balances..."
    source /home/subnet90/validators/validator_env/bin/activate
    btcli wallet balance --wallet.name $WALLET_NAME
    echo ""
    btcli wallet overview --wallet.name $WALLET_NAME --netuid 90
}

show_subnet_info() {
    echo "🔍 Subnet 90 Information:"
    source /home/subnet90/validators/validator_env/bin/activate
    btcli subnet list --netuid 90
    echo ""
    btcli subnet metagraph --netuid 90
}

update_code() {
    echo "📥 Updating code..."
    sudo supervisorctl stop all
    
    cd /home/subnet90/bittensor-subnet-90-brain
    git pull origin main
    
    # Update dependencies
    source /home/subnet90/validators/validator_env/bin/activate
    pip install -r requirements.txt
    
    for i in {1..3}; do
        source /home/subnet90/miners/miner${i}_env/bin/activate
        pip install -r requirements.txt
    done
    
    sudo supervisorctl start all
    echo "✅ Update complete"
}

# Main script logic
case "${1:-help}" in
    "status")
        check_status
        ;;
    "logs")
        show_logs
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "monitor")
        monitor_dashboard
        ;;
    "bootstrap")
        bootstrap_subnet
        ;;
    "register")
        register_hotkeys
        ;;
    "balance")
        check_balance
        ;;
    "subnet")
        show_subnet_info
        ;;
    "update")
        update_code
        ;;
    "help"|*)
        show_help
        ;;
esac