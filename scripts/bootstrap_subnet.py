#!/usr/bin/env python3
"""
Bootstrap script for Subnet 90 to initialize emissions.

This script helps subnet owners get emissions flowing by:
1. Checking subnet status
2. Setting initial weights
3. Monitoring emission flow
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import bittensor as bt
except ImportError:
    print("ERROR: Bittensor not installed. Run: pip install bittensor")
    sys.exit(1)

import structlog
logger = structlog.get_logger()


class SubnetBootstrapper:
    """Helper class to bootstrap subnet emissions."""
    
    def __init__(self, wallet_name: str, hotkey_name: str = "default", netuid: int = 90):
        self.wallet = bt.wallet(name=wallet_name, hotkey=hotkey_name)
        self.subtensor = bt.subtensor(network="finney")
        self.netuid = netuid
        self.metagraph = None
        
    def check_subnet_status(self):
        """Check current subnet status."""
        print(f"\n🔍 Checking Subnet {self.netuid} Status...\n")
        
        try:
            # Get subnet info
            subnet_info = self.subtensor.get_subnet_info(self.netuid)
            if subnet_info:
                print(f"✅ Subnet {self.netuid} exists")
                print(f"   Owner: {subnet_info.owner_ss58}")
                print(f"   Tempo: {subnet_info.tempo}")
                print(f"   Emission: {subnet_info.emission_value}")
            else:
                print(f"❌ Subnet {self.netuid} not found")
                return False
                
            # Get metagraph
            self.metagraph = self.subtensor.metagraph(self.netuid)
            print(f"\n📊 Network Status:")
            print(f"   Total neurons: {self.metagraph.n}")
            print(f"   Active validators: {len([n for n in self.metagraph.neurons if n.stake.sum() > 0])}")
            print(f"   Active miners: {len([n for n in self.metagraph.neurons if n.stake.sum() == 0])}")
            
            # Check our registration
            our_uid = None
            for i, neuron in enumerate(self.metagraph.neurons):
                if neuron.hotkey == self.wallet.hotkey.ss58_address:
                    our_uid = i
                    print(f"\n✅ Your hotkey registered as UID {our_uid}")
                    print(f"   Stake: {neuron.stake.tao} TAO")
                    print(f"   Rank: {neuron.rank}")
                    print(f"   Trust: {neuron.trust}")
                    break
            
            if our_uid is None:
                print(f"\n❌ Your hotkey {self.wallet.hotkey.ss58_address} not registered")
                print(f"   Run: btcli subnet register --netuid {self.netuid}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error checking subnet: {e}")
            return False
    
    def check_weights(self):
        """Check current weight distribution."""
        print(f"\n⚖️  Checking Current Weights...\n")
        
        our_uid = None
        for i, neuron in enumerate(self.metagraph.neurons):
            if neuron.hotkey == self.wallet.hotkey.ss58_address:
                our_uid = i
                break
        
        if our_uid is None:
            print("❌ Cannot check weights - not registered")
            return
        
        # Get our weights
        weights = self.metagraph.weights[our_uid]
        set_weights = [(i, w.item()) for i, w in enumerate(weights) if w > 0]
        
        if set_weights:
            print(f"Current weights from UID {our_uid}:")
            for uid, weight in set_weights:
                print(f"   UID {uid}: {weight:.4f}")
        else:
            print("❌ No weights currently set")
            print("   This is why emissions aren't flowing!")
    
    def set_initial_weights(self, distribute_to_all: bool = False):
        """Set initial weights to start emissions."""
        print(f"\n🎯 Setting Initial Weights...\n")
        
        try:
            # Find our UID
            our_uid = None
            for i, neuron in enumerate(self.metagraph.neurons):
                if neuron.hotkey == self.wallet.hotkey.ss58_address:
                    our_uid = i
                    break
            
            if our_uid is None:
                print("❌ Cannot set weights - not registered")
                return False
            
            # Prepare weights
            n = self.metagraph.n
            weights = [0.0] * n
            
            if distribute_to_all and n > 1:
                # Distribute equally to all neurons except ourselves
                weight_per_neuron = 1.0 / (n - 1)
                for i in range(n):
                    if i != our_uid:
                        weights[i] = weight_per_neuron
                print(f"Setting equal weights to {n-1} neurons")
            else:
                # Find miners (neurons without stake)
                miners = []
                for i, neuron in enumerate(self.metagraph.neurons):
                    if i != our_uid and neuron.stake.sum() == 0:
                        miners.append(i)
                
                if miners:
                    # Distribute to miners only
                    weight_per_miner = 1.0 / len(miners)
                    for miner_uid in miners:
                        weights[miner_uid] = weight_per_miner
                    print(f"Setting weights to {len(miners)} miners: {miners}")
                else:
                    print("⚠️  No miners found. Setting self-weight temporarily...")
                    # As last resort, set tiny self-weight to activate emissions
                    weights[our_uid] = 1.0
            
            # Convert to proper format
            import torch
            weights_tensor = torch.FloatTensor(weights)
            uids_tensor = torch.LongTensor(list(range(n)))
            
            # Normalize
            weights_tensor = weights_tensor / weights_tensor.sum()
            
            print(f"\nSetting weights on chain...")
            success = self.subtensor.set_weights(
                wallet=self.wallet,
                netuid=self.netuid,
                uids=uids_tensor,
                weights=weights_tensor,
                wait_for_inclusion=True,
                wait_for_finalization=False
            )
            
            if success:
                print("✅ Weights set successfully!")
                print("   Emissions should start flowing in the next tempo")
                return True
            else:
                print("❌ Failed to set weights")
                return False
                
        except Exception as e:
            print(f"❌ Error setting weights: {e}")
            return False
    
    def monitor_emissions(self, duration: int = 60):
        """Monitor emission flow for a period."""
        print(f"\n📈 Monitoring Emissions for {duration} seconds...\n")
        
        import time
        start_time = time.time()
        initial_emission = {}
        
        # Get initial emissions
        for neuron in self.metagraph.neurons:
            initial_emission[neuron.uid] = neuron.emission
        
        while time.time() - start_time < duration:
            time.sleep(10)
            
            # Refresh metagraph
            self.metagraph.sync()
            
            # Check for emission changes
            print(f"\nTime: +{int(time.time() - start_time)}s")
            changes_found = False
            
            for neuron in self.metagraph.neurons:
                if neuron.emission != initial_emission[neuron.uid]:
                    changes_found = True
                    print(f"   UID {neuron.uid}: {initial_emission[neuron.uid]:.6f} -> {neuron.emission:.6f}")
            
            if not changes_found:
                print("   No emission changes yet...")
        
        print("\n✅ Monitoring complete")


async def main():
    """Main bootstrap function."""
    print("🧠 Subnet 90 Bootstrap Tool\n")
    
    # Get wallet info from environment or prompt
    wallet_name = os.getenv("WALLET_NAME")
    if not wallet_name:
        wallet_name = input("Enter wallet name: ")
    
    hotkey_name = os.getenv("HOTKEY_NAME", "default")
    
    # Create bootstrapper
    bootstrapper = SubnetBootstrapper(wallet_name, hotkey_name)
    
    # Check status
    if not bootstrapper.check_subnet_status():
        print("\n❌ Subnet not properly initialized")
        return
    
    # Check weights
    bootstrapper.check_weights()
    
    # Ask to set weights
    print("\n" + "="*50)
    print("⚠️  To enable emissions, validators MUST set weights!")
    print("="*50)
    
    response = input("\nSet initial weights now? (y/n): ")
    if response.lower() == 'y':
        distribute_all = input("Distribute to all neurons (y) or miners only (n)? ").lower() == 'y'
        if bootstrapper.set_initial_weights(distribute_to_all=distribute_all):
            # Monitor
            monitor = input("\nMonitor emissions? (y/n): ")
            if monitor.lower() == 'y':
                bootstrapper.monitor_emissions(duration=60)
    
    print("\n✅ Bootstrap complete!")
    print("\nNext steps:")
    print("1. Run your validator: python deploy_validator.py")
    print("2. Encourage miners to join")
    print("3. Validators will automatically set weights based on miner performance")


if __name__ == "__main__":
    asyncio.run(main())