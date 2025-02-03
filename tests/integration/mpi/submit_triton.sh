#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=3

module load mamba
source activate odop

srun python upload_and_download.py
