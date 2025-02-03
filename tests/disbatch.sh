#!/bin/bash -l
#SBATCH --output=test.out # Name of stdout output file
#SBATCH --partition=small # Partition (queue) name
#SBATCH --nodes=1               # Total number of nodes
#SBATCH --ntasks-per-node=4     # 8 MPI ranks per node, 16 total (2x8)
##SBATCH --gres=gpu:v100:1
#SBATCH --time=00:010:00       # Run time (d-hh:mm:ss)
#SBATCH --account=project_2001736# Project for billing
#SBATCH --cpus-per-task=7

module load python-data

export ODOP_PATH=/users/anhdungn/NEOSC/odop/odop/odop_obs/

# shellcheck source=/users/anhdungn/NEOSC/odop/venv/bin/activate
source /users/anhdungn/NEOSC/odop/venv/bin/activate
srun python3 test_obs.py
