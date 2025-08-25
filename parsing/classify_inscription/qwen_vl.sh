#!/bin/bash
#SBATCH --partition=gpu_h100
#SBATCH --gpus-per-node=4
#SBATCH --time=03:00:00
#SBATCH --mem=80GB
#SBATCH --output=qwen_vl_classify.log

source ~/.bashrc
conda activate Image

python3 classify.py

