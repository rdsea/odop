#!/bin/bash -l

#SBATCH --partition=dev-g
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --time=00:15:00
#SBATCH --account=project_462000509
#SBATCH --cpus-per-task=7
#SBATCH --exclusive
#SBATCH --mem=0

ml cray-python

export OMP_NUM_THREADS=7
export OMP_PROC_BIND=close,spread
export OMP_MAX_ACTIVE_LEVELS=2
export OMP_WAIT_POLICY=PASSIVE
./start.csh
export MPICH_GPU_SUPPORT_ENABLED=1

cat << EOF > select_gpu
#!/bin/bash

export ROCR_VISIBLE_DEVICES=\$SLURM_LOCALID
exec \$*
EOF

chmod +x ./select_gpu

CPU_BIND="mask_cpu:fe000000000000,fe00000000000000"
CPU_BIND="${CPU_BIND},fe0000,fe000000"
CPU_BIND="${CPU_BIND},fe,fe00"
CPU_BIND="${CPU_BIND},fe00000000,fe0000000000"

export LD_PRELOAD=./src/libPC.so
export ODOP_PATH=~/monitoring/odop/odop/odop_obs/

srun --cpu-bind=${CPU_BIND} ./select_gpu /projappl/project_462000509/odop-containerized/bin/python call.py

rm -rf ./select_gpu
