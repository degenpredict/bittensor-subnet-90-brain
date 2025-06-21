#!/usr/bin/env python3
"""
Create a minimal coldkey file for validator use.

This creates a coldkey file that contains ONLY public information,
satisfying Bittensor's wallet structure requirements without exposing private keys.
"""
import os
import json
import argparse
from pathlib import Path


def create_minimal_coldkey(wallet_path: str, ss58_address: str):
    """
    Create a minimal coldkey file with only public information.
    
    Args:
        wallet_path: Path to the wallet directory (e.g., ~/.bittensor/wallets/default)
        ss58_address: The SS58 public address of the coldkey
    """
    wallet_path = Path(os.path.expanduser(wallet_path))
    
    # Read existing coldkeypub.txt if it exists
    coldkeypub_path = wallet_path / "coldkeypub.txt"
    if coldkeypub_path.exists():
        print(f"Found existing coldkeypub.txt at {coldkeypub_path}")
        with open(coldkeypub_path, 'r') as f:
            data = json.load(f)
            if 'ss58Address' in data:
                ss58_address = data['ss58Address']
                print(f"Using SS58 address from coldkeypub.txt: {ss58_address}")
    
    # Create minimal coldkey data
    # This structure mimics what Bittensor expects but contains NO private key data
    coldkey_data = {
        "accountId": "0x" + "0" * 64,  # Dummy account ID (public info)
        "publicKey": "0x" + "0" * 64,  # Dummy public key
        "secretPhrase": None,  # No mnemonic!
        "secretSeed": None,    # No seed!
        "ss58Address": ss58_address  # The only real data we need
    }
    
    # Write coldkey file
    coldkey_path = wallet_path / "coldkey"
    with open(coldkey_path, 'w') as f:
        json.dump(coldkey_data, f, indent=2)
    
    # Set restrictive permissions
    os.chmod(coldkey_path, 0o600)
    
    print(f"✓ Created minimal coldkey file at: {coldkey_path}")
    print(f"  - Contains only SS58 address: {ss58_address}")
    print(f"  - NO private keys or sensitive data")
    print(f"\nThe validator can now load the wallet without errors.")


def main():
    parser = argparse.ArgumentParser(description="Create minimal coldkey file for validator")
    parser.add_argument("--wallet-path", 
                       default="~/.bittensor/wallets/default",
                       help="Path to wallet directory")
    parser.add_argument("--ss58-address", 
                       help="SS58 address (will read from coldkeypub.txt if not provided)")
    
    args = parser.parse_args()
    
    if not args.ss58_address:
        # Try to read from coldkeypub.txt
        coldkeypub_path = Path(os.path.expanduser(args.wallet_path)) / "coldkeypub.txt"
        if not coldkeypub_path.exists():
            print("Error: No SS58 address provided and coldkeypub.txt not found")
            print("Please provide --ss58-address or ensure coldkeypub.txt exists")
            return
        args.ss58_address = "will-read-from-file"
    
    create_minimal_coldkey(args.wallet_path, args.ss58_address)


if __name__ == "__main__":
    main()