#!/bin/bash
# OVH KS-4 Optimized Setup for Subnet 90
# Runs multiple validators/miners on single powerful server

set -e

echo "🧠 Subnet 90 - OVH KS-4 Setup"
echo "=============================="

# System optimization for dedicated server
echo "⚡ Optimizing system for dedicated server..."
# Increase file limits
cat >> /etc/security/limits.conf <<EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# Optimize network settings
cat >> /etc/sysctl.conf <<EOF
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
EOF
sysctl -p

# Install dependencies
echo "📦 Installing dependencies..."
apt update
apt install -y software-properties-common

# Add deadsnakes PPA for Python 3.11
echo "🐍 Adding Python 3.11 repository..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update

# Install Python 3.11 and other dependencies
apt install -y \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    git \
    curl \
    wget \
    htop \
    iotop \
    tmux \
    screen \
    ufw \
    fail2ban \
    nginx \
    supervisor

# Ensure pip is available for Python 3.11 (ignore system pip conflicts)
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 --force-reinstall || echo "pip install completed (ignore errors)"

# Setup firewall with multiple ports for services
echo "🔥 Configuring firewall for multiple services..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP (for monitoring)
ufw allow 443/tcp # HTTPS (for monitoring)

# Bittensor ports for multiple instances
for i in {0..4}; do
    ufw allow $((9944 + i))/tcp  # Bittensor ports
    ufw allow $((9933 + i))/tcp  # RPC ports
    ufw allow $((8091 + i))/tcp  # Axon ports
done

echo "y" | ufw enable

# Create dedicated user for subnet
echo "👤 Creating subnet user..."
useradd -m -s /bin/bash subnet90 || true
usermod -aG sudo subnet90

# Setup directory structure
echo "📁 Setting up directory structure..."
su - subnet90 -c "mkdir -p ~/validators ~/miners ~/logs"

# Clone repository
echo "📥 Cloning repository..."
su - subnet90 -c "cd ~ && git clone https://github.com/degenpredict/bittensor-subnet-90-brain.git"

# Setup Python environments
echo "🐍 Setting up Python environments..."
# Validator environment
su - subnet90 -c "cd ~/validators && python3.11 -m venv validator_env"
su - subnet90 -c "cd ~/validators && source validator_env/bin/activate && pip install --upgrade pip"
su - subnet90 -c "cd ~/validators && source validator_env/bin/activate && pip install -r ~/bittensor-subnet-90-brain/requirements.txt"

# Miner environments (3 miners)
for i in {1..3}; do
    su - subnet90 -c "cd ~/miners && python3.11 -m venv miner${i}_env"
    su - subnet90 -c "cd ~/miners && source miner${i}_env/bin/activate && pip install --upgrade pip"
    su - subnet90 -c "cd ~/miners && source miner${i}_env/bin/activate && pip install -r ~/bittensor-subnet-90-brain/requirements.txt"
done

# Create supervisor configs
echo "⚙️ Setting up supervisor for process management..."

# Validator config
cat > /etc/supervisor/conf.d/subnet90-validator.conf <<EOF
[program:subnet90-validator]
command=/home/subnet90/validators/validator_env/bin/python -m validator.main
directory=/home/subnet90/bittensor-subnet-90-brain
user=subnet90
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/subnet90/logs/validator.err.log
stdout_logfile=/home/subnet90/logs/validator.out.log
environment=PATH="/home/subnet90/validators/validator_env/bin",WALLET_NAME="%(ENV_WALLET_NAME)s",HOTKEY_NAME="validator",API_URL="https://api.degenbrain.com"
EOF

# Miner configs
for i in {1..3}; do
    cat > /etc/supervisor/conf.d/subnet90-miner${i}.conf <<EOF
[program:subnet90-miner${i}]
command=/home/subnet90/miners/miner${i}_env/bin/python -m miner.main
directory=/home/subnet90/bittensor-subnet-90-brain
user=subnet90
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/subnet90/logs/miner${i}.err.log
stdout_logfile=/home/subnet90/logs/miner${i}.out.log
environment=PATH="/home/subnet90/miners/miner${i}_env/bin",WALLET_NAME="%(ENV_WALLET_NAME)s",HOTKEY_NAME="miner${i}",AXON_PORT="$((8091 + i))"
EOF
done

# Setup monitoring dashboard
echo "📊 Setting up monitoring..."
cat > /etc/nginx/sites-available/subnet90 <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:3000;  # Grafana
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /prometheus {
        proxy_pass http://localhost:9090;
        proxy_set_header Host \$host;
    }
}
EOF
ln -sf /etc/nginx/sites-available/subnet90 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# Setup monitoring script
cat > /home/subnet90/monitor.sh <<'EOF'
#!/bin/bash
# Simple monitoring script
while true; do
    clear
    echo "=== Subnet 90 Status ==="
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4"%"}')"
    echo "Memory: $(free -h | awk '/^Mem/ {print $3 " / " $2}')"
    echo "Disk: $(df -h / | awk 'NR==2 {print $3 " / " $2}')"
    echo ""
    echo "=== Process Status ==="
    supervisorctl status
    echo ""
    echo "=== Recent Logs ==="
    tail -n 5 /home/subnet90/logs/validator.out.log 2>/dev/null || echo "No validator logs yet"
    sleep 5
done
EOF
chmod +x /home/subnet90/monitor.sh
chown subnet90:subnet90 /home/subnet90/monitor.sh

# Create wallet setup script
cat > /home/subnet90/setup_wallets.sh <<'EOF'
#!/bin/bash
# Setup wallets for validator and miners
source ~/validators/validator_env/bin/activate
cd ~/bittensor-subnet-90-brain

echo "Setting up wallets..."
# Create validator wallet
btcli wallet new_coldkey --wallet.name subnet90_wallet
btcli wallet new_hotkey --wallet.name subnet90_wallet --wallet.hotkey validator

# Create miner hotkeys
for i in {1..3}; do
    btcli wallet new_hotkey --wallet.name subnet90_wallet --wallet.hotkey miner${i}
done

echo "Wallets created! Now you need to:"
echo "1. Fund the coldkey with TAO"
echo "2. Register each hotkey on subnet 90"
echo "   btcli subnet register --netuid 90 --wallet.name subnet90_wallet --wallet.hotkey validator"
echo "   btcli subnet register --netuid 90 --wallet.name subnet90_wallet --wallet.hotkey miner1"
echo "   etc..."
EOF
chmod +x /home/subnet90/setup_wallets.sh
chown subnet90:subnet90 /home/subnet90/setup_wallets.sh

# Final setup message
echo "✅ OVH KS-4 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Switch to subnet90 user: su - subnet90"
echo "2. Set up wallets: ./setup_wallets.sh"
echo "3. Copy wallet files to: /home/subnet90/.bittensor/wallets/"
echo "4. Set environment variable: export WALLET_NAME=your_wallet_name"
echo "5. Start services: sudo supervisorctl reload"
echo "6. Monitor: ./monitor.sh"
echo ""
echo "Useful commands:"
echo "- View all logs: sudo supervisorctl tail -f all"
echo "- Stop service: sudo supervisorctl stop subnet90-validator"
echo "- Start service: sudo supervisorctl start subnet90-validator"
echo "- Status: sudo supervisorctl status"
echo ""
echo "Your server can run:"
echo "- 1 Validator (as subnet owner)"
echo "- 3 Miners (to bootstrap the network)"
echo "- Monitoring dashboard"
echo ""
echo "Access monitoring at: http://YOUR_SERVER_IP/"