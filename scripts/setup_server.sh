#!/bin/bash
# Server setup script for Subnet 90 validator/miner
# Run this on a fresh Ubuntu 20.04/22.04 server

set -e

echo "🧠 Subnet 90 Server Setup"
echo "========================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt-get install -y \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    curl \
    wget \
    htop \
    tmux \
    ufw \
    fail2ban

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 9944/tcp  # Bittensor
sudo ufw allow 9933/tcp  # Bittensor RPC
sudo ufw allow 8091/tcp  # Axon port
echo "y" | sudo ufw enable

# Install Docker (optional, for easier deployment)
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd ~
python3.11 -m venv subnet90_env
source subnet90_env/bin/activate

# Clone repository
echo "📥 Cloning Subnet 90 repository..."
git clone https://github.com/degenpredict/bittensor-subnet-90-brain.git
cd bittensor-subnet-90-brain

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service for validator
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/subnet90-validator.service > /dev/null <<EOF
[Unit]
Description=Subnet 90 Validator
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/bittensor-subnet-90-brain
Environment="PATH=$HOME/subnet90_env/bin:$PATH"
Environment="WALLET_NAME=YOUR_WALLET_NAME"
Environment="HOTKEY_NAME=YOUR_HOTKEY_NAME"
Environment="API_URL=https://api.degenbrain.com"
ExecStart=$HOME/subnet90_env/bin/python -m validator.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for miner
sudo tee /etc/systemd/system/subnet90-miner.service > /dev/null <<EOF
[Unit]
Description=Subnet 90 Miner
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/bittensor-subnet-90-brain
Environment="PATH=$HOME/subnet90_env/bin:$PATH"
Environment="WALLET_NAME=YOUR_WALLET_NAME"
Environment="HOTKEY_NAME=YOUR_HOTKEY_NAME"
ExecStart=$HOME/subnet90_env/bin/python -m miner.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup monitoring
echo "📊 Setting up monitoring..."
# Install netdata for monitoring
wget -O /tmp/netdata-kickstart.sh https://my-netdata.io/kickstart.sh
sh /tmp/netdata-kickstart.sh --dont-wait

# Create wallet directory
echo "💰 Creating wallet directory..."
mkdir -p ~/.bittensor/wallets

echo "✅ Server setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy your wallet files to ~/.bittensor/wallets/"
echo "2. Edit the systemd service files to add your wallet details:"
echo "   sudo nano /etc/systemd/system/subnet90-validator.service"
echo "3. Start the service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable subnet90-validator"
echo "   sudo systemctl start subnet90-validator"
echo "4. Check logs:"
echo "   sudo journalctl -u subnet90-validator -f"
echo ""
echo "Security tips:"
echo "- Use SSH keys only (disable password auth)"
echo "- Keep wallet coldkey offline"
echo "- Monitor server resources"
echo "- Setup log rotation"