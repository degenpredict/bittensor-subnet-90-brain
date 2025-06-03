# Server Deployment Guide for Subnet 90

## Quick Start: Cloud Deployment

### Option 1: Single Server (Budget ~$50/month)

1. **Create a VPS** (DigitalOcean example):
```bash
# Create droplet via DO CLI
doctl compute droplet create subnet90-validator \
  --region nyc3 \
  --size s-4vcpu-8gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID
```

2. **SSH into server and run setup**:
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Download and run setup script
wget https://raw.githubusercontent.com/degenpredict/bittensor-subnet-90-brain/main/scripts/setup_server.sh
chmod +x setup_server.sh
./setup_server.sh
```

3. **Transfer wallet** (from local machine):
```bash
# IMPORTANT: Only copy hotkey, keep coldkey offline!
scp -r ~/.bittensor/wallets/YOUR_WALLET/hotkeys root@SERVER_IP:~/.bittensor/wallets/YOUR_WALLET/
```

4. **Configure and start**:
```bash
# On server
cd ~/bittensor-subnet-90-brain

# Set environment variables
export WALLET_NAME="your_wallet"
export HOTKEY_NAME="your_hotkey"
export API_URL="https://api.degenbrain.com"

# Start validator
python deploy_validator.py
```

### Option 2: Docker Deployment (Recommended for Production)

1. **Setup server** (same as above)

2. **Use Docker Compose**:
```bash
# Clone repo
git clone https://github.com/degenpredict/bittensor-subnet-90-brain.git
cd bittensor-subnet-90-brain

# Copy wallet files
mkdir -p ~/.bittensor/wallets
# Copy your wallet files here

# Create .env file
cat > .env << EOF
WALLET_NAME=your_wallet
HOTKEY_NAME=validator
MINER_HOTKEY=miner1
API_URL=https://api.degenbrain.com
NETWORK=finney
EOF

# Start services
docker-compose up -d validator
```

### Option 3: Multi-Server Setup (Production)

**Validator Server** (High-spec):
- AWS EC2 c5.large or equivalent
- Static IP (Elastic IP)
- Enhanced monitoring

**Miner Servers** (Lower-spec):
- 2-3 separate servers
- Can be t3.medium instances
- Different regions for redundancy

## Server Providers Comparison

| Provider | Validator Cost | Miner Cost | Pros | Cons |
|----------|---------------|------------|------|------|
| **DigitalOcean** | $48/mo (4CPU/8GB) | $24/mo (2CPU/4GB) | Easy, good UI | Limited regions |
| **Hetzner** | €20/mo (4CPU/8GB) | €8/mo (2CPU/4GB) | Cheapest | EU only |
| **AWS EC2** | ~$70/mo (c5.large) | ~$35/mo (t3.medium) | Reliable, global | Complex pricing |
| **Google Cloud** | ~$65/mo (n2-standard-2) | ~$30/mo (e2-medium) | Good network | Complex |
| **Vultr** | $48/mo (4CPU/8GB) | $24/mo (2CPU/4GB) | Global, simple | Smaller provider |

## Essential Security Setup

### 1. SSH Hardening
```bash
# Disable password auth
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Use SSH keys only
ssh-keygen -t ed25519 -C "subnet90-validator"
```

### 2. Firewall Rules
```bash
# Already in setup script, but verify:
sudo ufw status

# Should show:
# 22/tcp (SSH) - your IP only if possible
# 9944/tcp (Bittensor)
# 9933/tcp (RPC)
# 8091/tcp (Axon)
```

### 3. Wallet Security
- **NEVER** put coldkey on server
- Use separate hotkeys for validator vs miners
- Backup hotkeys encrypted

### 4. Monitoring Setup
```bash
# View logs
sudo journalctl -u subnet90-validator -f

# Monitor resources
htop

# Check Bittensor connection
btcli subnet metagraph --netuid 90
```

## Systemd Service Management

### Start Services
```bash
# Enable auto-start
sudo systemctl enable subnet90-validator

# Start service
sudo systemctl start subnet90-validator

# Check status
sudo systemctl status subnet90-validator
```

### View Logs
```bash
# Follow logs
sudo journalctl -u subnet90-validator -f

# Last 100 lines
sudo journalctl -u subnet90-validator -n 100
```

## Cost Optimization Tips

1. **Start Small**: Begin with one validator on a mid-tier server
2. **Use Spot Instances**: For miners (not validators)
3. **Regional Pricing**: Hetzner (EU) is cheapest
4. **Reserved Instances**: AWS/GCP for long-term savings

## Troubleshooting

### Port Issues
```bash
# Check if ports are open
sudo netstat -tlnp | grep -E '9944|9933|8091'

# Test from outside
nc -zv YOUR_SERVER_IP 9944
```

### Connection Problems
```bash
# Check Bittensor connectivity
btcli subnet metagraph --netuid 90

# Verify wallet
btcli wallet list
```

### High Resource Usage
- Validators need more resources than miners
- Monitor with `htop` and `iotop`
- Consider upgrading if consistently >80% CPU

## Production Checklist

Before going live:
- [ ] Server provisioned with static IP
- [ ] SSH key-only access enabled
- [ ] Firewall configured
- [ ] Wallet hotkey transferred (coldkey offline)
- [ ] Environment variables set
- [ ] Validator service running
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Logs rotating properly

## Next Steps

1. **Bootstrap emissions**: Run `python scripts/bootstrap_subnet.py`
2. **Monitor subnet**: Check https://taostats.io/subnets/90
3. **Add miners**: Deploy on separate servers
4. **Scale gradually**: Add resources as subnet grows