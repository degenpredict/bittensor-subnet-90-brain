#!/bin/bash
# PM2 Setup Script for Bittensor Subnet 90
# This script reads YAML configuration and sets up PM2 processes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/subnet90/bittensor-subnet-90-brain"
CONFIG_FILE="${PROJECT_DIR}/subnet_config.yaml"
ECOSYSTEM_FILE="${PROJECT_DIR}/ecosystem.config.js"
CONFIG_PARSER="${PROJECT_DIR}/scripts/config_parser.py"

echo -e "${GREEN}=== Bittensor Subnet 90 PM2 Setup ===${NC}"

# Check if running as subnet90 user
if [ "$USER" != "subnet90" ]; then
    echo -e "${YELLOW}Warning: Not running as subnet90 user. Switching...${NC}"
    exec sudo su - subnet90 -c "$0 $@"
fi

# Check prerequisites
echo -e "\n${GREEN}Checking prerequisites...${NC}"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}PM2 is not installed. Installing...${NC}"
    npm install -g pm2
fi

# Check if PyYAML is installed in base Python
if ! python3 -c "import yaml" &> /dev/null 2>&1; then
    echo -e "${YELLOW}Installing PyYAML...${NC}"
    pip3 install pyyaml
fi

# Validate configuration
echo -e "\n${GREEN}Validating configuration...${NC}"
cd "$PROJECT_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Configuration file not found: $CONFIG_FILE${NC}"
    echo "Please create subnet_config.yaml first"
    exit 1
fi

# Ensure config parser exists
if [ ! -f "$CONFIG_PARSER" ]; then
    echo -e "${RED}Error: Config parser not found at $CONFIG_PARSER${NC}"
    exit 1
fi
chmod +x "$CONFIG_PARSER"

# Validate config
python3 "$CONFIG_PARSER" --config "$CONFIG_FILE" --validate
if [ $? -ne 0 ]; then
    echo -e "${RED}Configuration validation failed!${NC}"
    exit 1
fi

# Generate PM2 ecosystem config
echo -e "\n${GREEN}Generating PM2 ecosystem configuration...${NC}"
python3 "$CONFIG_PARSER" --config "$CONFIG_FILE" --generate-pm2

# Create logs directory if it doesn't exist
LOG_DIR=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG_FILE')); print(c.get('global',{}).get('log_dir','./logs'))")
mkdir -p "$PROJECT_DIR/$LOG_DIR"

# Function to setup and start a process
setup_process() {
    local process_type=$1
    local process_id=$2
    
    echo -e "\n${GREEN}Setting up $process_type $process_id...${NC}"
    
    # Show environment variables
    echo "Environment variables:"
    python3 "$CONFIG_PARSER" --config "$CONFIG_FILE" --show-env "$process_id"
    
    # Check if virtual environment exists
    if [ "$process_type" = "validator" ]; then
        VENV_PATH="/home/subnet90/validators/validator_env"
    else
        VENV_PATH="/home/subnet90/miners/${process_id}_env"
    fi
    
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}Virtual environment not found: $VENV_PATH${NC}"
        echo "Please create the virtual environment first"
        return 1
    fi
    
    return 0
}

# Parse command line arguments
case "${1:-all}" in
    "validator")
        setup_process "validator" "validator"
        if [ $? -eq 0 ]; then
            pm2 start "$ECOSYSTEM_FILE" --only validator
        fi
        ;;
    
    "miners")
        # Get list of enabled miners
        MINERS=$(python3 -c "
import yaml
config = yaml.safe_load(open('$CONFIG_FILE'))
miners = [m['id'] for m in config.get('miners', []) if m.get('enabled', False)]
print(' '.join(miners))
")
        
        for miner in $MINERS; do
            setup_process "miner" "$miner"
        done
        
        pm2 start "$ECOSYSTEM_FILE" --only "miner*"
        ;;
    
    "all")
        # Start everything
        pm2 start "$ECOSYSTEM_FILE"
        ;;
    
    "stop")
        echo -e "${YELLOW}Stopping all processes...${NC}"
        pm2 stop all
        ;;
    
    "restart")
        echo -e "${YELLOW}Restarting all processes...${NC}"
        pm2 restart all
        ;;
    
    "status")
        pm2 status
        ;;
    
    "logs")
        pm2 logs "${2:-}"
        ;;
    
    "save")
        echo -e "${GREEN}Saving PM2 configuration...${NC}"
        pm2 save
        pm2 startup systemd -u subnet90 --hp /home/subnet90
        echo -e "${YELLOW}Run the command above with sudo to enable auto-start on boot${NC}"
        ;;
    
    "clean")
        echo -e "${YELLOW}Cleaning up old logs and processes...${NC}"
        pm2 delete all
        pm2 flush
        ;;
    
    *)
        echo "Usage: $0 [command] [args]"
        echo ""
        echo "Commands:"
        echo "  all        - Start all enabled processes (default)"
        echo "  validator  - Start only validator"
        echo "  miners     - Start only miners"
        echo "  stop       - Stop all processes"
        echo "  restart    - Restart all processes"
        echo "  status     - Show process status"
        echo "  logs [id]  - Show logs (optionally for specific process)"
        echo "  save       - Save PM2 config for auto-start"
        echo "  clean      - Clean up all processes and logs"
        exit 1
        ;;
esac

# Show final status
echo -e "\n${GREEN}Current process status:${NC}"
pm2 status

echo -e "\n${GREEN}Setup complete!${NC}"
echo "Use 'pm2 monit' for real-time monitoring"
echo "Use 'pm2 logs' to view logs"