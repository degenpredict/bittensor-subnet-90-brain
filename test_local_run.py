#!/usr/bin/env python3
"""
Test script to run validator and miner together locally.
This simulates the full system without Bittensor network integration.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from validator.main import Validator
from miner.main import Miner
import structlog

# Configure structured logging for better output
import logging
logging.basicConfig(level=logging.INFO)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def run_test_system():
    """Run validator and miner together for testing."""
    
    # Set up test environment
    os.environ["WALLET_NAME"] = "test_wallet"
    os.environ["HOTKEY_NAME"] = "test_hotkey"
    os.environ["API_URL"] = "https://api.degenbrain.com/resolve"
    
    logger.info("🚀 Starting local test of DegenBrain Subnet 90")
    logger.info("=" * 60)
    
    # Create validator and miner instances
    validator = Validator()
    miner = Miner()
    
    # Create tasks for both components
    validator_task = asyncio.create_task(run_validator_limited(validator))
    miner_task = asyncio.create_task(run_miner_limited(miner))
    
    try:
        # Run both tasks concurrently
        await asyncio.gather(validator_task, miner_task)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Stopping test system...")
    finally:
        # Clean shutdown
        validator.running = False
        miner.running = False
        
        await validator.shutdown()
        await miner.shutdown()
        
        logger.info("✅ Test completed successfully!")
        print_summary(validator, miner)


async def run_validator_limited(validator: Validator):
    """Run validator for limited iterations."""
    logger.info("🎯 Starting Validator", role="VALIDATOR")
    
    await validator.setup()
    validator.running = True
    
    max_iterations = 3
    iteration = 0
    
    while validator.running and iteration < max_iterations:
        try:
            logger.info(f"📊 Validator iteration {iteration + 1}/{max_iterations}", role="VALIDATOR")
            
            # Fetch statements
            statements = await validator._fetch_statements()
            
            if not statements:
                logger.info("No statements to process, waiting...", role="VALIDATOR")
                await asyncio.sleep(2)
                iteration += 1
                continue
            
            # Process each statement
            for statement in statements[:1]:  # Process only first statement for demo
                if not validator.running:
                    break
                
                logger.info(f"📝 Processing: {statement.statement[:50]}...", role="VALIDATOR")
                await validator._process_statement(statement)
                validator.stats.statements_processed += 1
            
            # Update weights
            await validator._update_weights()
            
            iteration += 1
            await asyncio.sleep(2)  # Brief pause between iterations
            
        except Exception as e:
            logger.error(f"Validator error: {e}", role="VALIDATOR")
            validator.stats.errors += 1
            await asyncio.sleep(2)
    
    logger.info("✅ Validator test completed", role="VALIDATOR")
    validator.running = False


async def run_miner_limited(miner: Miner):
    """Run miner for limited iterations."""
    logger.info("⛏️  Starting Miner", role="MINER")
    
    await miner.setup()
    miner.running = True
    
    max_iterations = 5
    iteration = 0
    
    while miner.running and iteration < max_iterations:
        try:
            logger.info(f"🔄 Miner iteration {iteration + 1}/{max_iterations}", role="MINER")
            
            # Get next task
            task = await miner._get_next_task()
            
            if task:
                logger.info(f"📋 Got task: {task.statement[:50]}...", role="MINER")
                response = await miner._process_task(task)
                logger.info(f"✅ Response: {response.resolution.value} (confidence: {response.confidence}%)", 
                          role="MINER")
            else:
                logger.info("No tasks available, waiting...", role="MINER")
            
            iteration += 1
            await asyncio.sleep(3)  # Brief pause between iterations
            
        except Exception as e:
            logger.error(f"Miner error: {e}", role="MINER")
            await asyncio.sleep(3)
    
    logger.info("✅ Miner test completed", role="MINER")
    miner.running = False


def print_summary(validator: Validator, miner: Miner):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print("\n🎯 VALIDATOR STATS:")
    val_stats = validator.get_stats()
    for key, value in val_stats.items():
        print(f"  {key}: {value}")
    
    print("\n⛏️  MINER STATS:")
    miner_stats = miner.get_stats()
    for key, value in miner_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Local test complete! Both components working together.")
    print("🚀 Ready for Phase 5: Bittensor integration")
    print("=" * 60)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║        DegenBrain Subnet 90 - Local Test Run              ║
║                                                           ║
║  This will run validator and miner together locally       ║
║  to demonstrate the system working end-to-end.            ║
║                                                           ║
║  Press Ctrl+C to stop at any time.                       ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(run_test_system())
    except KeyboardInterrupt:
        print("\n\n👋 Test stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)