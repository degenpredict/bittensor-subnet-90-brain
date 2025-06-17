#!/bin/bash
cd $HOME/bittensor-subnet-90-brain
python run_validator.py 2>&1 | tee -a validator.log