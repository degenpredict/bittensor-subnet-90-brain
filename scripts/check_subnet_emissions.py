#!/usr/bin/env python3
"""
Script to check emissions for Bittensor Subnet 90
Checks emission rates, incentives, dividends, and stake information
"""

import bittensor as bt
from typing import Optional

def check_subnet_emissions(netuid: int = 90) -> None:
    """
    Check emission details for a specific subnet on Bittensor
    
    Args:
        netuid: Network UID to check (default: 90)
    """
    
    print(f"=== Checking Emissions for Bittensor Subnet {netuid} ===\n")
    
    # Connect to finney network
    print("Connecting to finney network...")
    subtensor = bt.subtensor(network="finney")
    
    # Get metagraph for subnet 90
    print(f"Fetching metagraph for netuid={netuid}...")
    metagraph = bt.metagraph(netuid=netuid, network="finney")
    
    # 1. Check subnet emission rate
    print("\n1. SUBNET EMISSION RATE")
    print("-" * 50)
    
    # Get total emission for the subnet
    try:
        subnet_emission = subtensor.get_emission_value_by_subnet(netuid=netuid)
        print(f"Subnet {netuid} emission rate: {subnet_emission} RAO/block")
        print(f"Subnet {netuid} emission rate: {subnet_emission / 1e9:.6f} TAO/block")
    except Exception as e:
        print(f"Error getting subnet emission: {e}")
    
    # 2. Check if participants are earning incentives/dividends
    print("\n2. PARTICIPANTS EARNINGS CHECK")
    print("-" * 50)
    
    # Check overall statistics
    total_incentive = sum(metagraph.I)
    total_dividends = sum(metagraph.D)
    active_neurons = sum(1 for i in metagraph.I if i > 0)
    
    print(f"Total neurons in subnet: {len(metagraph.uids)}")
    print(f"Active neurons (with incentive > 0): {active_neurons}")
    print(f"Total incentive distributed: {total_incentive:.6f}")
    print(f"Total dividends distributed: {total_dividends:.6f}")
    
    # 3. Show first 10 neurons' emission details
    print("\n3. FIRST 10 NEURONS EMISSION DETAILS")
    print("-" * 50)
    print(f"{'UID':<5} {'Incentive':<12} {'Dividends':<12} {'Stake (TAO)':<12} {'Trust':<8} {'Active':<8}")
    print("-" * 80)
    
    for uid in range(min(10, len(metagraph.uids))):
        incentive = float(metagraph.I[uid])
        dividends = float(metagraph.D[uid])
        stake = float(metagraph.S[uid]) / 1e9  # Convert from RAO to TAO
        trust = float(metagraph.T[uid])
        active = metagraph.active[uid] if hasattr(metagraph, 'active') else 'N/A'
        
        print(f"{uid:<5} {incentive:<12.6f} {dividends:<12.6f} {stake:<12.4f} {trust:<8.4f} {str(active):<8}")
    
    # 4. Check UID 0 specifically
    print("\n4. UID 0 DETAILED INFORMATION")
    print("-" * 50)
    
    if len(metagraph.uids) > 0:
        uid = 0
        print(f"UID: {uid}")
        print(f"Hotkey: {metagraph.hotkeys[uid]}")
        print(f"Coldkey: {metagraph.coldkeys[uid] if hasattr(metagraph, 'coldkeys') else 'N/A'}")
        print(f"Incentive: {float(metagraph.I[uid]):.6f}")
        print(f"Dividends: {float(metagraph.D[uid]):.6f}")
        print(f"Stake: {float(metagraph.S[uid]) / 1e9:.4f} TAO ({float(metagraph.S[uid])} RAO)")
        print(f"Trust: {float(metagraph.T[uid]):.4f}")
        print(f"Consensus: {float(metagraph.C[uid]):.4f}")
        print(f"Validator Permit: {metagraph.validator_permit[uid] if hasattr(metagraph, 'validator_permit') else 'N/A'}")
        
        # Calculate emission for UID 0
        if subnet_emission:
            uid_emission = subnet_emission * float(metagraph.I[uid])
            print(f"Estimated emission: {uid_emission / 1e9:.6f} TAO/block")
    else:
        print("No neurons found in subnet")
    
    # Additional subnet information
    print("\n5. ADDITIONAL SUBNET INFORMATION")
    print("-" * 50)
    
    try:
        # Get subnet info
        subnet_info = subtensor.get_subnet_info(netuid)
        if subnet_info:
            print(f"Subnet owner: {subnet_info.owner_ss58}")
            print(f"Network modality: {subnet_info.network_modality}")
            print(f"Max allowed UIDs: {subnet_info.max_allowed_uids}")
            print(f"Min allowed weights: {subnet_info.min_allowed_weights}")
            print(f"Tempo: {subnet_info.tempo}")
    except Exception as e:
        print(f"Error getting subnet info: {e}")
    
    print("\n" + "=" * 80)
    print("Emission check complete!")


if __name__ == "__main__":
    try:
        check_subnet_emissions(netuid=90)
    except Exception as e:
        print(f"Error running emission check: {e}")
        print("\nMake sure you have bittensor installed:")
        print("pip install bittensor")