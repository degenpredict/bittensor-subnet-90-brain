#!/bin/bash
# Fresh start script for Bittensor Subnet 90 with PM2
# Interactive setup that creates YAML configuration from scratch

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Bittensor Subnet 90 Fresh Setup ===${NC}"
echo "This script will create a new YAML configuration and set up PM2 process management."
echo ""

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local variable_name="$3"
    
    echo -n -e "${BLUE}$prompt${NC}"
    if [ -n "$default" ]; then
        echo -n " [default: $default]"
    fi
    echo -n ": "
    
    read user_input
    if [ -z "$user_input" ]; then
        user_input="$default"
    fi
    
    # Use eval to set the variable dynamically
    eval "$variable_name='$user_input'"
}

# Function to prompt yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    
    while true; do
        echo -n -e "${BLUE}$prompt${NC} [y/n, default: $default]: "
        read yn
        
        if [ -z "$yn" ]; then
            yn="$default"
        fi
        
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

echo -e "${GREEN}=== Global Configuration ===${NC}"

# Global settings
prompt_with_default "Network (finney/test/local)" "finney" "NETWORK"
prompt_with_default "Subnet UID" "90" "SUBNET_UID"
prompt_with_default "API URL" "https://api.subnet90.com" "API_URL"
prompt_with_default "Log Level (DEBUG/INFO/WARNING/ERROR)" "INFO" "LOG_LEVEL"

echo ""
echo -e "${GREEN}=== Validator Configuration ===${NC}"

if prompt_yes_no "Enable validator?" "y"; then
    VALIDATOR_ENABLED="true"
    prompt_with_default "Validator wallet name" "subnet90_wallet" "VALIDATOR_WALLET"
    prompt_with_default "Validator hotkey name" "validator" "VALIDATOR_HOTKEY"
    prompt_with_default "Validator port" "8090" "VALIDATOR_PORT"
    prompt_with_default "Validator ID" "unique_validator_id" "VALIDATOR_ID"
    prompt_with_default "Virtual environment path" "/home/subnet90/bittensor-subnet-90-brain/.venv" "VALIDATOR_VENV"
else
    VALIDATOR_ENABLED="false"
fi

echo ""
echo -e "${GREEN}=== Miners Configuration ===${NC}"

prompt_with_default "How many miners to configure?" "3" "NUM_MINERS"

# Validate number of miners
if ! [[ "$NUM_MINERS" =~ ^[1-5]$ ]]; then
    echo -e "${RED}Error: Number of miners must be between 1 and 5${NC}"
    exit 1
fi

# Array to store miner configurations
declare -a MINER_CONFIGS

for ((i=1; i<=NUM_MINERS; i++)); do
    echo ""
    echo -e "${YELLOW}--- Miner $i Configuration ---${NC}"
    
    MINER_ID="miner$i"
    prompt_with_default "Miner $i wallet name" "subnet90_wallet" "MINER_WALLET_$i"
    prompt_with_default "Miner $i hotkey name" "miner$i" "MINER_HOTKEY_$i"
    
    DEFAULT_PORT=$((8090 + i))
    prompt_with_default "Miner $i port" "$DEFAULT_PORT" "MINER_PORT_$i"
    
    echo "Available strategies: ai_reasoning, hybrid, dummy"
    prompt_with_default "Miner $i strategy" "dummy" "MINER_STRATEGY_$i"
    
    prompt_with_default "Miner $i virtual environment path" "/home/subnet90/bittensor-subnet-90-brain/.venv" "MINER_VENV_$i"
done

# Check if all miners are using dummy strategy
echo ""
echo -e "${YELLOW}=== Strategy Validation ===${NC}"

ALL_DUMMY=true
for ((i=1; i<=NUM_MINERS; i++)); do
    STRATEGY_VAR="MINER_STRATEGY_$i"
    STRATEGY_VALUE="${!STRATEGY_VAR}"
    if [ "$STRATEGY_VALUE" != "dummy" ]; then
        ALL_DUMMY=false
        break
    fi
done

if [ "$ALL_DUMMY" = "true" ]; then
    echo -e "${YELLOW}WARNING: All miners are configured with 'dummy' strategy.${NC}"
    echo -e "${YELLOW}This will dramatically affect your weights/emissions as dummy miners${NC}"
    echo -e "${YELLOW}provide random responses and won't earn meaningful rewards.${NC}"
    echo -e "${YELLOW}This is only recommended for testing purposes.${NC}"
    echo ""
    
    if ! prompt_yes_no "Are you sure you want to continue with all dummy miners?" "n"; then
        echo -e "${RED}Setup cancelled. Please re-run and choose better strategies.${NC}"
        echo "Recommended: Use 'ai_reasoning' or 'hybrid' for production miners."
        exit 1
    fi
    
    echo -e "${YELLOW}Proceeding with dummy configuration (testing mode)...${NC}"
fi

echo ""
echo -e "${GREEN}=== Setting Up Virtual Environment ===${NC}"

# Check if virtual environment exists, create if not
VENV_PATH="/home/subnet90/bittensor-subnet-90-brain/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Check if requirements.txt exists and install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    "$VENV_PATH/bin/pip" install --upgrade pip
    "$VENV_PATH/bin/pip" install -r requirements.txt
    echo "Requirements installed."
else
    echo -e "${YELLOW}Warning: requirements.txt not found. You may need to install dependencies manually.${NC}"
fi

# Test that bittensor is properly installed
echo "Testing bittensor installation..."
if "$VENV_PATH/bin/python3" -c "import bittensor; print('Bittensor version:', bittensor.__version__)" 2>/dev/null; then
    echo -e "${GREEN}Bittensor successfully installed and accessible.${NC}"
else
    echo -e "${RED}Error: Bittensor not properly installed. Please check requirements.txt${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Generating Configuration ===${NC}"

# Create the YAML configuration
CONFIG_FILE="subnet_config.yaml"

cat > "$CONFIG_FILE" << EOF
# Bittensor Subnet 90 Configuration
# Generated on $(date)

# Global settings applied to all processes
global:
  network: $NETWORK
  subnet_uid: $SUBNET_UID
  api_url: $API_URL
  log_level: $LOG_LEVEL
  log_format: json
  log_dir: ./logs
  
  # Process management
  max_restarts: 10
  min_uptime: 10s
  restart_delay: 4000
  
  # Performance
  max_workers: 4
  request_timeout: 30

EOF

# Add validator configuration
if [ "$VALIDATOR_ENABLED" = "true" ]; then
    cat >> "$CONFIG_FILE" << EOF
# Validator configuration
validator:
  enabled: true
  wallet_name: $VALIDATOR_WALLET
  hotkey_name: $VALIDATOR_HOTKEY
  port: $VALIDATOR_PORT
  validator_id: $VALIDATOR_ID
  
  # Validator-specific settings
  bootstrap_mode: true
  min_stake_threshold: 1000
  
  # Process settings
  max_restarts: 20
  
  # Virtual environment
  venv_path: $VALIDATOR_VENV

EOF
else
    cat >> "$CONFIG_FILE" << EOF
# Validator configuration
validator:
  enabled: false

EOF
fi

# Add miners configuration
cat >> "$CONFIG_FILE" << EOF
# Miners configuration
miners:
EOF

for ((i=1; i<=NUM_MINERS; i++)); do
    # Get the variable values
    WALLET_VAR="MINER_WALLET_$i"
    HOTKEY_VAR="MINER_HOTKEY_$i"
    PORT_VAR="MINER_PORT_$i"
    STRATEGY_VAR="MINER_STRATEGY_$i"
    VENV_VAR="MINER_VENV_$i"
    
    WALLET_VALUE="${!WALLET_VAR}"
    HOTKEY_VALUE="${!HOTKEY_VAR}"
    PORT_VALUE="${!PORT_VAR}"
    STRATEGY_VALUE="${!STRATEGY_VAR}"
    VENV_VALUE="${!VENV_VAR}"
    
    cat >> "$CONFIG_FILE" << EOF
  # Miner $i
  - id: miner$i
    enabled: true
    wallet_name: $WALLET_VALUE
    hotkey_name: $HOTKEY_VALUE
    port: $PORT_VALUE
    strategy: $STRATEGY_VALUE
    venv_path: $VENV_VALUE
EOF

    # Add strategy-specific configuration
    if [ "$STRATEGY_VALUE" = "ai_reasoning" ]; then
        cat >> "$CONFIG_FILE" << EOF
    
    # Strategy-specific settings
    model_config:
      temperature: 0.7
      max_tokens: 2000
EOF
    elif [ "$STRATEGY_VALUE" = "hybrid" ]; then
        cat >> "$CONFIG_FILE" << EOF
    
    # Strategy weights for hybrid
    strategy_weights:
      ai: 0.6
      heuristic: 0.4
EOF
    fi
    
    echo "" >> "$CONFIG_FILE"
done

# Add PM2 configuration
cat >> "$CONFIG_FILE" << EOF

# PM2-specific configuration
pm2:
  log_rotation:
    max_size: 100M
    retain: 7d
    compress: true
  
  health_check:
    enabled: true
    interval: 30s
    timeout: 5s
    max_failures: 3
EOF

echo "Generated configuration file: $CONFIG_FILE"

# Validate the configuration
echo -e "\n${GREEN}Validating configuration...${NC}"
if python3 scripts/config_parser.py --config "$CONFIG_FILE" --validate; then
    echo -e "${GREEN}Configuration is valid!${NC}"
else
    echo -e "${RED}Configuration validation failed!${NC}"
    exit 1
fi

# Show configuration summary
echo -e "\n${GREEN}Configuration Summary:${NC}"
python3 scripts/config_parser.py --config "$CONFIG_FILE"

# Generate PM2 ecosystem config
echo -e "\n${GREEN}Generating PM2 ecosystem configuration...${NC}"
python3 scripts/config_parser.py --config "$CONFIG_FILE" --generate-pm2

# Create logs directory
mkdir -p logs

echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Copy the following files to your project directory:"
echo "   - $CONFIG_FILE"
echo "   - scripts/config_parser.py"
echo "   - scripts/subnet_config_loader.py"
echo "   - pm2_setup.sh"
echo "   - ecosystem.config.js"
echo ""
echo "2. Update your Python code to use the new config loader:"
echo "   from subnet_config_loader import get_env"
echo "   api_url = get_env('API_URL')"
echo ""
echo "3. Start processes with PM2:"
echo "   ./pm2_setup.sh all"
echo ""
echo "4. Monitor processes:"
echo "   pm2 status"
echo "   pm2 logs"
echo "   pm2 monit"