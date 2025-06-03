#!/usr/bin/env python3
"""
Run the DegenBrain miner.

Usage:
    python run_miner.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from miner.main import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMiner stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)