# BTCLI Commands Reference

btcli --help                     # Show main help
btcli --commands                 # Show all available commands
btcli --version                  # Show BTCLI version

---

### CONFIG Commands (aliases: conf, c)
btcli config set                 # Set configuration values
btcli config get                 # Get configuration values  
btcli config clear               # Clear configuration

---

### WALLET Commands (aliases: wallets, w)

# Creation & Management
btcli wallet create              # Create new wallet
btcli wallet list                # List all wallets
btcli wallet overview            # Show wallet overview
btcli wallet balance             # Check wallet balance

# Keys Management
btcli wallet new-coldkey         # Create new coldkey
btcli wallet new-hotkey          # Create new hotkey
btcli wallet regen-coldkey       # Regenerate coldkey
btcli wallet regen-coldkeypub    # Regenerate coldkey public
btcli wallet regen-hotkey        # Regenerate hotkey
btcli wallet associate-hotkey    # Associate hotkey with coldkey

# Key Swapping
btcli wallet swap-hotkey         # Swap hotkey
btcli wallet swap-coldkey        # Swap coldkey
btcli wallet swap-check          # Check swap status

# Transfers & Identity
btcli wallet transfer            # Transfer TAO
btcli wallet faucet              # Request faucet tokens (testnet)
btcli wallet set-identity        # Set wallet identity
btcli wallet get-identity        # Get wallet identity
btcli wallet sign                # Sign message with wallet

---

### STAKE Commands (alias: st)

# Basic Staking
btcli stake add                  # Add stake to validator
btcli stake remove               # Remove stake from validator
btcli stake list                 # List current stakes
btcli stake move                 # Move stake between validators
btcli stake transfer             # Transfer stake
btcli stake swap                 # Swap stake

# Child Hotkey Management
btcli stake child get            # Get child hotkey info
btcli stake child set            # Set child hotkey
btcli stake child revoke         # Revoke child hotkey
btcli stake child take           # Take from child hotkey

---

### SUBNETS Commands (aliases: s, subnet)

# Subnet Information
btcli subnets list               # List all subnets
btcli subnets show               # Show subnet details
btcli subnets hyperparameters    # Show subnet hyperparameters
btcli subnets price              # Show registration price

# Registration
btcli subnets register           # Register on subnet
btcli subnets pow-register       # PoW register on subnet
btcli subnets burn-cost          # Check burn cost
btcli subnets create             # Create new subnet

# Subnet Management
btcli subnets start              # Start subnet
btcli subnets check-start        # Check if subnet can start
btcli subnets set-identity       # Set subnet identity
btcli subnets get-identity       # Get subnet identity

---

### SUDO Commands (alias: su)

# Senate & Governance
btcli sudo senate                # Senate operations
btcli sudo proposals             # View proposals
btcli sudo senate-vote           # Vote on proposals

# Parameter Management
btcli sudo set                   # Set sudo parameters
btcli sudo get                   # Get sudo parameters
btcli sudo set-take              # Set validator take
btcli sudo get-take              # Get validator take

---

### VIEW Commands
btcli view dashboard             # Open HTML dashboard

---

# Create wallet and hotkey
btcli wallet new-coldkey --wallet.name my_wallet
btcli wallet new-hotkey --wallet.name my_wallet --wallet.hotkey miner_1

# Register on subnet
btcli subnets register --wallet.name my_wallet --wallet.hotkey miner_1 --netuid 90

# Check balance and stakes
btcli wallet balance --wallet.name my_wallet
btcli stake list --wallet.name my_wallet

# View subnet info
btcli subnets show --netuid 90
btcli subnets list