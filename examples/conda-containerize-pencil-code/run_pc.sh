#!/bin/bash -l
#SBATCH --partition=debug
#SBATCH --time=00:05:00
#SBATCH --account=project_462000509
#SBATCH --ntasks=2

/projappl/project_462000509/pc-containerized/bin/start.csh
srun /projappl/project_462000509/pc-containerized/bin/run.x
