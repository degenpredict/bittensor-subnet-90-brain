#!/usr/bin/env python3
"""
Script to check Bittensor wallet balance and staking information.
"""

import bittensor as bt
import sys


def main():
    try:
        # Initialize wallet
        print("Loading wallet...")
        wallet = bt.wallet(name="subnet90_wallet", hotkey="owner")
        
        # Connect to finney network
        print("Connecting to finney network...")
        subtensor = bt.subtensor(network="finney")
        
        # Get wallet addresses
        print("\n=== Wallet Information ===")
        print(f"Coldkey Address: {wallet.coldkey.ss58_address}")
        print(f"Hotkey Address: {wallet.hotkey.ss58_address}")
        
        # Get coldkey balance
        print("\n=== Balance Information ===")
        coldkey_balance = subtensor.get_balance(wallet.coldkey.ss58_address)
        print(f"Coldkey Balance: {coldkey_balance} TAO")
        
        # Check staking on subnet 90
        print("\n=== Subnet 90 Staking Information ===")
        try:
            # Get all stake info for the coldkey
            stake_info = subtensor.get_stake_info_for_coldkey(wallet.coldkey.ss58_address)
            
            # Check if there's any stake on subnet 90
            subnet_90_stake = 0.0
            if stake_info:
                for hotkey, stake_data in stake_info.items():
                    # Check if this hotkey is registered on subnet 90
                    uid = subtensor.get_uid_for_hotkey_on_subnet(hotkey, netuid=90)
                    if uid is not None:
                        # Get the stake amount
                        stake_amount = stake_data.tao if hasattr(stake_data, 'tao') else stake_data
                        subnet_90_stake += float(stake_amount)
                        print(f"Hotkey {hotkey[:8]}...{hotkey[-6:]} staked on subnet 90: {stake_amount} TAO")
            
            if subnet_90_stake == 0:
                print("No TAO staked on subnet 90")
            else:
                print(f"\nTotal TAO staked on subnet 90: {subnet_90_stake} TAO")
                
        except Exception as e:
            print(f"Error checking subnet 90 stake: {e}")
            
            # Alternative method to check stake
            print("\nTrying alternative method...")
            try:
                # Get neurons for subnet 90
                neurons = subtensor.neurons(netuid=90)
                total_stake = 0.0
                
                for neuron in neurons:
                    if neuron.coldkey == wallet.coldkey.ss58_address:
                        total_stake += float(neuron.stake)
                        print(f"Found neuron with UID {neuron.uid} staked: {neuron.stake} TAO")
                
                if total_stake > 0:
                    print(f"\nTotal TAO staked on subnet 90: {total_stake} TAO")
                else:
                    print("No neurons found on subnet 90 for this coldkey")
                    
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")
        
        # Additional information
        print("\n=== Additional Information ===")
        try:
            # Check if hotkey is registered on subnet 90
            uid = subtensor.get_uid_for_hotkey_on_subnet(wallet.hotkey.ss58_address, netuid=90)
            if uid is not None:
                print(f"Hotkey is registered on subnet 90 with UID: {uid}")
                
                # Get neuron info
                neuron = subtensor.neuron_for_uid(uid, netuid=90)
                if neuron:
                    print(f"Neuron stake: {neuron.stake} TAO")
                    print(f"Neuron rank: {neuron.rank}")
                    print(f"Neuron trust: {neuron.trust}")
                    print(f"Neuron consensus: {neuron.consensus}")
                    print(f"Neuron incentive: {neuron.incentive}")
                    print(f"Neuron dividends: {neuron.dividends}")
            else:
                print("Hotkey is not registered on subnet 90")
                
        except Exception as e:
            print(f"Could not fetch additional neuron information: {e}")
            
    except FileNotFoundError as e:
        print(f"\nError: Wallet not found. Make sure the wallet 'subnet90_wallet' with hotkey 'owner' exists.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    main()