# Odop Machine Learning Benchmark

## LUMI

Create an odop container:

```bash
module load LUMI lumi-container-wrapper
conda-containerize new --prefix odop_container odop_env.yml
```

Build a container for the ML training task:

```bash
module load LUMI systools
singularity build container.sif container.def
```

Submit the benchmark tasks:

```bash
sbatch submit_lumi_N1.sh
sbatch submit_lumi_N1_with_odop.sh
```

## Results

| Test Case     | nodes | cores/node | GPUs per node | time (s)  | Odop                           |
| ------------- | ----- | ---------- | ------------- | --------- | ------------------------------ |
| GPT2 training | 1     | 56         | 8             | 868.8157  |                                |
| GPT2 training | 1     | 56         | 8             | 862.1558  | Odop without tasks             |
| GPT2 training | 1     | 56         | 8             | 909.0496  | Upload model to object storage |
| GPT2 training | 2     | 56         | 8             | 1594.7106 |                                |
| GPT2 training | 2     | 56         | 8             | 1778.2687 | Odop without tasks             |
| GPT2 training | 2     | 56         | 8             | 1656.1718 | Upload model to object storage |

## Source

The code used in this benchmark is taken from [csc-training](https://github.com/csc-training/intro-to-dl/tree/master)
