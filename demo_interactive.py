#!/usr/bin/env python3
"""
Interactive demo of DegenBrain Subnet 90.
Shows the complete flow from statement to consensus.
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.types import Statement, Resolution, MinerResponse
from miner.agents.dummy_agent import DummyAgent
from validator.weights import WeightsCalculator


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_section(title):
    """Print a section divider."""
    print(f"\n{'-' * 40}")
    print(f"  {title}")
    print(f"{'-' * 40}\n")


async def demo_complete_flow():
    """Run a complete demonstration of the subnet."""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║        DegenBrain Subnet 90 - Interactive Demo                 ║
    ║                                                                ║
    ║  This demo simulates the complete flow of:                    ║
    ║  1. Statement submission                                       ║
    ║  2. Miner verification                                         ║
    ║  3. Consensus calculation                                      ║
    ║  4. Weight assignment                                          ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    await asyncio.sleep(1)
    
    # Sample statements
    statements = [
        Statement(
            statement="Bitcoin will reach $100,000 by December 31, 2024",
            end_date="2024-12-31T23:59:59Z",
            createdAt="2024-01-15T12:00:00Z",
            initialValue=42000.0,
            direction="increase",
            id="demo_001"
        ),
        Statement(
            statement="Ethereum will flip Bitcoin in market cap by 2025",
            end_date="2025-12-31T23:59:59Z",
            createdAt="2024-06-01T00:00:00Z",
            initialValue=0.055,  # ETH/BTC ratio
            direction="increase",
            id="demo_002"
        ),
        Statement(
            statement="Solana will process 100k TPS consistently in Q4 2024",
            end_date="2024-12-31T23:59:59Z",
            createdAt="2024-03-01T00:00:00Z",
            initialValue=65000.0,  # Current TPS
            direction="increase",
            id="demo_003"
        ),
    ]
    
    # Process each statement
    for idx, statement in enumerate(statements):
        print_header(f"STATEMENT {idx + 1} OF {len(statements)}")
        await process_statement_demo(statement)
        
        if idx < len(statements) - 1:
            print("\n⏳ Processing next statement in 3 seconds...")
            await asyncio.sleep(3)
    
    print_header("DEMO COMPLETE")
    print("✅ This demonstration showed:")
    print("   • Statement verification by multiple miners")
    print("   • Consensus calculation using confidence-weighted voting")
    print("   • Miner scoring based on accuracy, confidence, consistency, and sources")
    print("   • Weight normalization for Bittensor network")
    print("\n🚀 The system is ready for Phase 5: Bittensor network integration!")


async def process_statement_demo(statement: Statement):
    """Process a single statement through the full pipeline."""
    
    # 1. Show the statement
    print("📋 STATEMENT TO VERIFY:")
    print(f"   \"{statement.statement}\"")
    print(f"   End date: {statement.end_date}")
    print(f"   Initial value: {statement.initialValue}")
    print(f"   Direction: {statement.direction}")
    
    await asyncio.sleep(1)
    
    # 2. Simulate miners
    print_section("MINER VERIFICATION PHASE")
    
    # Create diverse miners with different characteristics
    miner_configs = [
        {"name": "HighAccuracyMiner", "accuracy": 0.95, "confidence_range": (85, 98)},
        {"name": "ConservativeMiner", "accuracy": 0.85, "confidence_range": (60, 75)},
        {"name": "BalancedMiner", "accuracy": 0.80, "confidence_range": (70, 90)},
        {"name": "AggressiveMiner", "accuracy": 0.75, "confidence_range": (80, 95)},
        {"name": "CautiousMiner", "accuracy": 0.90, "confidence_range": (50, 70)},
        {"name": "RandomMiner", "accuracy": 0.60, "confidence_range": (40, 90)},
        {"name": "ExpertMiner", "accuracy": 0.92, "confidence_range": (75, 95)},
    ]
    
    responses = []
    for i, config in enumerate(miner_configs):
        print(f"⛏️  {config['name']} analyzing statement...")
        await asyncio.sleep(0.3)  # Simulate processing time
        
        agent = DummyAgent({
            "accuracy": config["accuracy"],
            "confidence_range": config["confidence_range"],
            "delay": 0  # No delay for demo
        })
        
        response = await agent.verify_statement(statement)
        response.miner_uid = i
        responses.append(response)
        
        # Show response
        print(f"   → Resolution: {response.resolution.value}")
        print(f"   → Confidence: {response.confidence:.1f}%")
        print(f"   → Sources: {len(response.sources)} sources")
    
    await asyncio.sleep(1)
    
    # 3. Calculate consensus
    print_section("CONSENSUS CALCULATION")
    
    calculator = WeightsCalculator()
    validation_result = calculator.calculate_consensus(statement, responses)
    
    # Show resolution counts
    resolution_counts = {}
    total_confidence = {}
    for response in responses:
        res = response.resolution.value
        resolution_counts[res] = resolution_counts.get(res, 0) + 1
        total_confidence[res] = total_confidence.get(res, 0) + response.confidence
    
    print("📊 RESOLUTION VOTES:")
    for resolution, count in sorted(resolution_counts.items()):
        avg_conf = total_confidence[resolution] / count if count > 0 else 0
        print(f"   {resolution}: {count} votes (avg confidence: {avg_conf:.1f}%)")
    
    print(f"\n✅ CONSENSUS: {validation_result.consensus_resolution.value}")
    print(f"   Confidence: {validation_result.consensus_confidence:.1f}%")
    print(f"   Agreement: {validation_result.valid_responses}/{validation_result.total_responses} valid responses")
    
    await asyncio.sleep(1)
    
    # 4. Show miner scores
    print_section("MINER SCORING & WEIGHTS")
    
    print("📈 INDIVIDUAL MINER SCORES:")
    for i, config in enumerate(miner_configs):
        if i in validation_result.miner_scores:
            score = validation_result.miner_scores[i]
            response = responses[i]
            
            # Determine if miner was correct
            correct = "✅" if response.resolution == validation_result.consensus_resolution else "❌"
            
            print(f"   {config['name']}: {score:.3f} {correct}")
            print(f"      Resolution: {response.resolution.value}, Confidence: {response.confidence:.1f}%")
    
    # Show weight distribution
    print("\n⚖️  NORMALIZED WEIGHTS (for Bittensor):")
    sorted_weights = sorted(validation_result.miner_scores.items(), key=lambda x: x[1], reverse=True)
    for uid, weight in sorted_weights[:5]:  # Top 5
        config = miner_configs[uid]
        print(f"   {config['name']}: {weight:.3f}")
    
    # Summary insights
    print("\n💡 INSIGHTS:")
    if validation_result.consensus_resolution == Resolution.TRUE:
        print("   • Miners believe this prediction will come TRUE")
    elif validation_result.consensus_resolution == Resolution.FALSE:
        print("   • Miners believe this prediction will be FALSE")
    else:
        print("   • Miners are uncertain (PENDING) about this prediction")
    
    print(f"   • Consensus strength: {validation_result.consensus_confidence:.1f}%")
    print(f"   • Top performing miners rewarded with higher weights")


if __name__ == "__main__":
    # Set minimal environment
    os.environ["WALLET_NAME"] = "demo"
    os.environ["HOTKEY_NAME"] = "demo"
    os.environ["API_URL"] = "https://api.degenbrain.com"
    
    # Suppress warnings for cleaner output
    import warnings
    warnings.filterwarnings("ignore")
    
    # Configure logging to be quiet
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    try:
        asyncio.run(demo_complete_flow())
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()