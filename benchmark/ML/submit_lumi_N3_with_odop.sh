#!/usr/bin/env -S bash -e
#SBATCH --job-name=finetune_multigpu
#SBATCH --nodes=3
#SBATCH --tasks-per-node=8
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-node=8
#SBATCH --mem=120G
#SBATCH --partition=dev-g
#SBATCH --time=00:50:00
#SBATCH --account=project_462000365

set -xv

source env.sh

# Set up variables to control distributed PyTorch training
export MASTER_ADDR=$(hostname)
export MASTER_PORT=25900
export WORLD_SIZE=$SLURM_NPROCS
export LOCAL_WORLD_SIZE=$SLURM_GPUS_PER_NODE

# Huggingface cache location
export HF_HOME=/scratch/project_462000365/HF_home/

srun singularity exec --bind /scratch/project_462000365/ container.sif\
    bash -c "RANK=\$SLURM_PROCID \
             LOCAL_RANK=\$SLURM_LOCALID \
             python3.11 GPT-neo-IMDB-finetuning_with_odop.py \
                --model-name gpt-imdb-model-multigpu \
                --output-path /scratch/project_462000365/odop_ml_benchmark_data/ \
                --init-model-name gpt-neo-2.7B\
		--logging-path .\
                --num-workers $(( SLURM_CPUS_PER_TASK ))\
                --set-cpu-binds " 2>&1 > logs/output_2_${SLURM_JOB_NUM_NODES}.txt

