#!/bin/bash
#SBATCH --partition=gpu_h100
#SBATCH --gpus-per-node=4
#SBATCH --time=02:00:00
#SBATCH --mem=80GB
#SBATCH --output=llava_vl_one_shot.log

source ~/.bashrc
conda activate Image

python3 llava_7b_one_shot.py

