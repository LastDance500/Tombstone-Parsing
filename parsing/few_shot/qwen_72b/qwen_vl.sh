#!/bin/bash
#SBATCH --partition=gpu_h100
#SBATCH --gpus-per-node=4
#SBATCH --time=03:00:00
#SBATCH --mem=80GB
#SBATCH --output=qwen_vl_three_shot.log

source ~/.bashrc
conda activate Image

python3 qwen_72b_three_shot.py

