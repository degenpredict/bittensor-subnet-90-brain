#!/bin/bash
cd $HOME/bittensor-subnet-90-brain
python run_miner.py 2>&1 | tee -a miner.log