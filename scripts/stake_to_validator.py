#!/usr/bin/env python3
"""
Script to stake TAO to validator on subnet 90.
"""

import bittensor as bt
import sys


def main():
    try:
        # Initialize wallet
        print("Loading wallet...")
        wallet = bt.wallet(name="mainnet_wallet", hotkey="subnet_owner")
        
        # Connect to finney network
        print("Connecting to finney network...")
        subtensor = bt.subtensor(network="finney")
        
        # Check current balance
        balance = subtensor.get_balance(wallet.coldkey.ss58_address)
        print(f"\nCurrent coldkey balance: {balance} TAO")
        
        # Ask for stake amount
        print("\nHow much TAO would you like to stake to your validator?")
        print(f"Available balance: {balance} TAO")
        print("Recommended: At least 1-2 TAO for effective weight setting")
        
        try:
            stake_amount = float(input("Enter amount to stake: "))
        except ValueError:
            print("Invalid amount entered")
            sys.exit(1)
            
        if stake_amount <= 0:
            print("Stake amount must be positive")
            sys.exit(1)
            
        if stake_amount > float(balance):
            print(f"Not enough balance. You have {balance} TAO available")
            sys.exit(1)
        
        # Confirm staking
        print(f"\nAbout to stake {stake_amount} TAO to hotkey: {wallet.hotkey.ss58_address}")
        confirm = input("Continue? (y/N): ")
        
        if confirm.lower() != 'y':
            print("Staking cancelled")
            sys.exit(0)
        
        # Perform staking
        print(f"\nStaking {stake_amount} TAO...")
        success = subtensor.add_stake(
            wallet=wallet,
            hotkey_ss58=wallet.hotkey.ss58_address,
            amount=bt.Balance.from_tao(stake_amount)
        )
        
        if success:
            print(f"✅ Successfully staked {stake_amount} TAO!")
            
            # Check new balance
            new_balance = subtensor.get_balance(wallet.coldkey.ss58_address)
            print(f"New coldkey balance: {new_balance} TAO")
            
        else:
            print("❌ Staking failed")
            
    except FileNotFoundError as e:
        print(f"\nError: Wallet not found. Make sure the wallet 'mainnet_wallet' with hotkey 'owner' exists.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    main()