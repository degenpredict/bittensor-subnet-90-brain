#!/usr/bin/env python3
"""
Simple demo showing the flow of statement verification.
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.types import Statement, Resolution
from miner.agents.dummy_agent import DummyAgent
from validator.weights import WeightsCalculator


async def demo_flow():
    """Demonstrate the statement verification flow."""
    
    print("\n🚀 DegenBrain Subnet 90 - Statement Verification Demo")
    print("=" * 70)
    
    # 1. Create a sample statement
    statement = Statement(
        statement="Bitcoin will reach $100,000 by December 31, 2024",
        end_date="2024-12-31T23:59:59Z",
        createdAt="2024-01-15T12:00:00Z",
        initialValue=42000.0,
        direction="increase",
        id="demo_001"
    )
    
    print(f"\n📝 STATEMENT TO VERIFY:")
    print(f"   '{statement.statement}'")
    print(f"   End date: {statement.end_date}")
    print(f"   Initial value: ${statement.initialValue:,.2f}")
    
    # 2. Simulate multiple miners analyzing the statement
    print(f"\n⛏️  SIMULATING 5 MINERS ANALYZING THE STATEMENT...")
    print("-" * 70)
    
    miners = [
        DummyAgent({"accuracy": 0.9, "confidence_range": (85, 95)}),
        DummyAgent({"accuracy": 0.8, "confidence_range": (70, 90)}),
        DummyAgent({"accuracy": 0.85, "confidence_range": (75, 92)}),
        DummyAgent({"accuracy": 0.7, "confidence_range": (60, 80)}),
        DummyAgent({"accuracy": 0.95, "confidence_range": (88, 98)}),
    ]
    
    responses = []
    for i, miner in enumerate(miners):
        response = await miner.verify_statement(statement)
        response.miner_uid = i  # Assign miner ID
        responses.append(response)
        
        print(f"\nMiner {i}: {response.resolution.value}")
        print(f"  Confidence: {response.confidence:.1f}%")
        print(f"  Summary: {response.summary[:60]}...")
        print(f"  Sources: {', '.join(response.sources[:2])}")
    
    # 3. Calculate consensus using the validator's scoring algorithm
    print(f"\n🎯 CALCULATING CONSENSUS...")
    print("-" * 70)
    
    calculator = WeightsCalculator()
    validation_result = calculator.calculate_consensus(statement, responses)
    
    print(f"\n✅ CONSENSUS RESULT:")
    print(f"   Resolution: {validation_result.consensus_resolution.value}")
    print(f"   Confidence: {validation_result.consensus_confidence:.1f}%")
    print(f"   Valid responses: {validation_result.valid_responses}/{validation_result.total_responses}")
    
    # 4. Show miner scores
    print(f"\n📊 MINER SCORES (normalized weights):")
    for uid, score in validation_result.miner_scores.items():
        print(f"   Miner {uid}: {score:.3f}")
    
    # 5. Show resolution distribution
    print(f"\n📈 RESOLUTION DISTRIBUTION:")
    resolution_counts = {}
    for response in responses:
        res = response.resolution.value
        resolution_counts[res] = resolution_counts.get(res, 0) + 1
    
    for resolution, count in resolution_counts.items():
        percentage = (count / len(responses)) * 100
        print(f"   {resolution}: {count}/{len(responses)} ({percentage:.0f}%)")
    
    print("\n" + "=" * 70)
    print("✅ Demo complete! This shows how statements flow through the system.")
    print("=" * 70)


async def demo_scoring():
    """Demonstrate the scoring algorithm in detail."""
    
    print("\n\n🔍 SCORING ALGORITHM DEMO")
    print("=" * 70)
    
    statement = Statement(
        statement="Ethereum will cross $5,000 before July 1, 2024",
        end_date="2024-07-01T00:00:00Z",
        createdAt="2024-01-01T00:00:00Z"
    )
    
    # Create responses with different characteristics
    from shared.types import MinerResponse
    
    responses = [
        # High confidence, correct answer, good sources
        MinerResponse(
            statement=statement.statement,
            resolution=Resolution.TRUE,
            confidence=95.0,
            summary="Strong bullish indicators",
            sources=["coingecko", "coinmarketcap", "yahoo"],
            miner_uid=0
        ),
        # Low confidence, correct answer
        MinerResponse(
            statement=statement.statement,
            resolution=Resolution.TRUE,
            confidence=60.0,
            summary="Uncertain but leaning bullish",
            sources=["reddit"],
            miner_uid=1
        ),
        # High confidence, wrong answer
        MinerResponse(
            statement=statement.statement,
            resolution=Resolution.FALSE,
            confidence=90.0,
            summary="Market correction expected",
            sources=["unknown_blog"],
            miner_uid=2
        ),
        # Appropriate uncertainty
        MinerResponse(
            statement=statement.statement,
            resolution=Resolution.PENDING,
            confidence=50.0,
            summary="Too early to determine",
            sources=["bloomberg", "reuters"],
            miner_uid=3
        ),
    ]
    
    calculator = WeightsCalculator()
    
    # First determine consensus
    consensus = Resolution.TRUE  # 2 TRUE vs 1 FALSE vs 1 PENDING
    
    print("📊 DETAILED SCORING BREAKDOWN:")
    print("-" * 70)
    
    for response in responses:
        print(f"\n🔸 Miner {response.miner_uid}: {response.resolution.value} (confidence: {response.confidence}%)")
        
        # Calculate individual score components
        accuracy = calculator._calculate_accuracy_score(response, consensus)
        confidence = calculator._calculate_confidence_score(response, consensus)
        consistency = calculator._calculate_consistency_score(response, responses)
        source = calculator._calculate_source_score(response)
        
        print(f"   Accuracy score: {accuracy:.2f} (weight: 40%)")
        print(f"   Confidence score: {confidence:.2f} (weight: 20%)")
        print(f"   Consistency score: {consistency:.2f} (weight: 30%)")
        print(f"   Source quality: {source:.2f} (weight: 10%)")
        
        total = (accuracy * 0.4 + confidence * 0.2 + 
                consistency * 0.3 + source * 0.1)
        print(f"   → Total score: {total:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Set minimal environment for demo
    os.environ["WALLET_NAME"] = "demo"
    os.environ["HOTKEY_NAME"] = "demo"
    os.environ["API_URL"] = "https://api.degenbrain.com"
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║          DegenBrain Subnet 90 - Flow Demo                 ║
║                                                           ║
║  This demo shows:                                         ║
║  1. Statement verification by multiple miners             ║
║  2. Consensus calculation                                 ║
║  3. Miner scoring algorithm                               ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(demo_flow())
    asyncio.run(demo_scoring())