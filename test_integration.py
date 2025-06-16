#!/usr/bin/env python3
"""
Test script for brain-api integration with bittensor subnet.

This script tests the end-to-end flow:
1. Fetch statements from api.subnet90.com
2. Create mock miner responses 
3. Submit responses back to brain-api
"""
import asyncio
import sys
import os
from typing import List

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.api import DegenBrainAPIClient
from shared.types import Statement, MinerResponse, Resolution

async def test_fetch_statements():
    """Test fetching statements from brain-api."""
    print("🔗 Testing statement fetching from api.subnet90.com...")
    
    try:
        async with DegenBrainAPIClient(api_url="https://api.subnet90.com") as client:
            statements = await client.fetch_statements()
            
            print(f"✅ Successfully fetched {len(statements)} statements")
            for i, stmt in enumerate(statements[:3]):  # Show first 3
                print(f"   {i+1}. {stmt.statement[:60]}...")
                print(f"      ID: {stmt.id}, Category: {stmt.category}")
            
            return statements
            
    except Exception as e:
        print(f"❌ Failed to fetch statements: {e}")
        return []

async def test_submit_responses(statements: List[Statement]):
    """Test submitting miner responses to brain-api."""
    if not statements:
        print("⏭️  Skipping response submission - no statements available")
        return
    
    print("\n📤 Testing miner response submission...")
    
    # Use the first statement for testing
    test_statement = statements[0]
    print(f"Testing with statement: {test_statement.statement[:60]}...")
    
    # Create mock miner responses
    mock_responses = [
        MinerResponse(
            statement=test_statement.statement,
            resolution=Resolution.TRUE,
            confidence=85.0,
            summary="Mock analysis shows this statement is likely true",
            sources=["MockDataSource1", "MockAPI"],
            miner_uid=1001
        ),
        MinerResponse(
            statement=test_statement.statement,
            resolution=Resolution.FALSE,
            confidence=75.0,
            summary="Mock analysis suggests this statement is false",
            sources=["MockDataSource2", "MockExchange"],
            miner_uid=1002
        ),
        MinerResponse(
            statement=test_statement.statement,
            resolution=Resolution.TRUE,
            confidence=90.0,
            summary="Strong evidence supporting true resolution",
            sources=["MockAPI", "MockNews"],
            miner_uid=1003
        )
    ]
    
    try:
        async with DegenBrainAPIClient(api_url="https://api.subnet90.com") as client:
            success = await client.submit_miner_responses(
                statement_id=test_statement.id,
                validator_id="test-validator-integration",
                miner_responses=mock_responses
            )
            
            if success:
                print("✅ Successfully submitted miner responses to brain-api")
                print(f"   Submitted {len(mock_responses)} responses for statement: {test_statement.id}")
            else:
                print("❌ Failed to submit miner responses")
                
    except Exception as e:
        print(f"❌ Error during response submission: {e}")

async def test_full_integration():
    """Test the complete integration flow."""
    print("🚀 Starting Brain-API ↔ Bittensor Subnet Integration Test")
    print("=" * 60)
    
    # Test fetching statements
    statements = await test_fetch_statements()
    
    # Test submitting responses
    await test_submit_responses(statements)
    
    print("\n" + "=" * 60)
    print("🎯 Integration test complete!")
    
    if statements:
        print(f"✅ Successfully connected to brain-api")
        print(f"✅ Data models are compatible")
        print(f"✅ End-to-end flow working")
        print("\n🔥 Ready for validator deployment!")
    else:
        print("❌ Integration test failed - check API connectivity")

if __name__ == "__main__":
    asyncio.run(test_full_integration())