#!/usr/bin/env python3
"""
Check participants on Subnet 90 - validators and miners.
Shows who's actively setting weights and participating in the network.
"""
import sys
import bittensor as bt
from typing import List, Tuple

def get_participant_identity(uid: int) -> str:
    """Get known identity for specific UIDs."""
    known_identities = {
        0: "brain (Owner)",
        1: "RoundTable21",
        63: "Rizzo (Insured)",
        68: "Openτensor Foundation",
        69: "tao.bot",
    }
    return known_identities.get(uid, "")

def check_subnet_participants(netuid: int = 90):
    """Check all participants on the subnet."""
    print(f"Connecting to Bittensor network...")
    subtensor = bt.subtensor(network='finney')
    metagraph = subtensor.metagraph(netuid=netuid)
    
    print(f"\n📊 Subnet {netuid} Overview")
    print(f"Total neurons: {len(metagraph.neurons)}")
    print(f"Total stake: {metagraph.S.sum():.2f} TAO\n")
    
    # Categorize participants
    validators = []
    miners = []
    
    for i, neuron in enumerate(metagraph.neurons):
        stake = neuron.stake.tao
        # Check if setting weights (validators set weights)
        weights_set = len([w for w in metagraph.weights[i] if w > 0]) if i < len(metagraph.weights) else 0
        
        # Special handling for subnet owner (UID 0) - always show as validator
        if i == 0 or stake > 0.1:  # Subnet owner or has meaningful stake
            validators.append((i, neuron, stake, weights_set))
        else:  # No/minimal stake - likely miner
            miners.append((i, neuron, stake))
    
    # Print validators
    print(f"=== VALIDATORS ({len(validators)}) ===")
    print(f"{'UID':>4} | {'Hotkey':>10} | {'Coldkey':>10} | {'Stake (TAO)':>12} | {'Weights Set':>11} | Active | Identity")
    print("-" * 85)
    
    for uid, neuron, stake, weights in sorted(validators, key=lambda x: x[2], reverse=True)[:20]:
        active = '✓' if neuron.active else '✗'
        identity = get_participant_identity(uid)
        print(f"{uid:4} | {neuron.hotkey[:10]} | {neuron.coldkey[:10]} | {stake:12,.1f} | {weights:11} | {active:6} | {identity}")
    
    # Print active miners (recent registrations)
    print(f"\n=== MINERS (Recent 30) ===")
    print(f"{'UID':>4} | {'Hotkey':>10} | {'Coldkey':>10} | {'Last Update':>12} | Active")
    print("-" * 60)
    
    recent_miners = sorted(miners, key=lambda x: x[0], reverse=True)[:30]
    for uid, neuron, stake in recent_miners:
        active = '✓' if neuron.active else '✗'
        print(f"{uid:4} | {neuron.hotkey[:10]} | {neuron.coldkey[:10]} | Block {neuron.last_update:6} | {active}")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"- Validators (stake > 0.1 TAO): {len(validators)}")
    print(f"- Miners (stake ≤ 0.1 TAO): {len(miners)}")
    print(f"- Total participants: {len(metagraph.neurons)}")

def check_active_validators(netuid: int = 90):
    """Check who is actively setting weights."""
    print(f"\nChecking active weight setters...")
    subtensor = bt.subtensor(network='finney')
    metagraph = subtensor.metagraph(netuid=netuid)
    
    print("\n=== ACTIVE WEIGHT SETTERS (True Validators) ===")
    print(f"{'UID':>4} | {'Stake (TAO)':>12} | {'Weights Set':>11} | {'Hotkey':>10} | Identity")
    print("-" * 70)
    
    active_validators = []
    for i, neuron in enumerate(metagraph.neurons):
        if i < len(metagraph.weights):
            weights_set = len([w for w in metagraph.weights[i] if w > 0])
            if weights_set > 0:
                active_validators.append((i, neuron, weights_set))
    
    # Sort by stake
    active_validators.sort(key=lambda x: x[1].stake.tao, reverse=True)
    
    for uid, neuron, weights in active_validators[:20]:
        identity = get_participant_identity(uid)
        print(f"{uid:4} | {neuron.stake.tao:12,.1f} | {weights:11} | {neuron.hotkey[:10]} | {identity}")
    
    print(f"\nTotal validators setting weights: {len(active_validators)}")
    
    # Check your specific registrations
    print("\n=== YOUR REGISTRATIONS ===")
    your_hotkeys = {
        "5DwAxR": "subnet_owner_validator",  # Your actual subnet owner hotkey
        "5EFa44": "validator",
        "5C8bXe": "miner1", 
        "5G9EJv": "miner2",
        "5Deg9Q": "miner3"
    }
    
    for i, neuron in enumerate(metagraph.neurons):
        hotkey_prefix = neuron.hotkey[:6]
        if hotkey_prefix in your_hotkeys:
            weights_set = len([w for w in metagraph.weights[i] if w > 0]) if i < len(metagraph.weights) else 0
            print(f"UID {i:3}: {your_hotkeys[hotkey_prefix]:10} - Stake: {neuron.stake.tao:.4f} TAO, Weights set: {weights_set}, Active: {'✓' if neuron.active else '✗'}")

if __name__ == "__main__":
    try:
        # Check if specific netuid provided
        netuid = int(sys.argv[1]) if len(sys.argv) > 1 else 90
        
        print(f"🧠 Checking Subnet {netuid} Participants\n")
        
        # Check all participants
        check_subnet_participants(netuid)
        
        # Check active validators
        check_active_validators(netuid)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)