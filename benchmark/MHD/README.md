# MHD Benchmark

Magnetohydrodynamics (MHD) simulations is currently used to model the solar magnetic field evolution for the prediction
of space weather and climate.

This benchmark runs a large-scale computation on GPUs using [pencil-code](https://github.com/pencil-code/pencil-code)
and [Astaroth](https://bitbucket.org/jpekkila/astaroth). It is GPU-heavy and by design tries to maximize the GPU
utilization. This allows to see the effect of running opportunistic tasks on CPU cores and what is the effect of the
number of available CPU cores on the total performance of the benchmark.

The opportunities currently pursued by ODOP in this benchmark are:

- reduction
- uploading of checkpoints to an object storage

## Requirements

- [pencil-code](https://github.com/pencil-code/pencil-code) (use branch `gputestv6`)
- [Astaroth](https://bitbucket.org/jpekkila/astaroth) (submodule of `pencil-code`; use branch `PCinterface_2019-8-12`
- OpenMPI (ROCm or CUDA-enabled)
- AMD ROCm or NVIDIA CUDA development environment
- CMake

This benchmark uses as the basis the `gputest` sample application from the `pencil-code` repository. See the README file
in the repository for more instructions on how to get started with that application and how to set-up the experiment
file structure.

## Running an experiment

> The current targeted HPC environment is [LUMI](https://docs.lumi-supercomputer.eu/) with AMD GPU. For Nvidia GPU, some
> parameter in the build script must be changed.

> [!IMPORTANT]
> Take note of the environment you're running in. What are the minimum and maximum resources you can and want to use for
> the benchmark? Especially, what is the maximum memory capacity of the GPUs you're using. This is important for
> adjusting the domain sizes used in the benchmark to ensure maximum utilization.

> [!IMPORTANT]
> Make sure you source the `sourceme.sh` script in the `pencil-code` repository **after** you make all required
> libraries available (e.g., using `module`).

1. Enter the experiment directory.
2. Adjust the used GPU accelerator (`AMD` or `NVIDIA`) in `src/Makefile.local`.
3. Run `pc_setupsrc`.
4. Copy `equations.h` into `src/astaroth/submodule/include/equations.h`.
5. Run `pc_build -t shared_lib`.
6. Dispatch using your favourite job queue.

### Scaling tests

For running scaling tests (weak, strong) there is a helper tool used to generate specific experiments:
`generate-experiment.py`. The tool generates a set of experiments that can be run as per instruction in the **Running**
section.

The generator creates experiments with the following characteristics:

Specific characteristics of the generated experiments:

- the domain size aims to maximize utilization of GPU memory,
- the size of the domain is uniform,
- the domain is distributed across GPUs only across the Y-axis.

Before dispatching a job using a batch script, check its configuration. Namely the

- number of OpenMP threads,
- number of nodes,
- tasks per node,
- CPUs per task, and
- GPUs per node.

### BPOD paper

- Focus on the definition and how to determine opportunistic task
- Early-state benefit of ODOP in terms of total required time with two types of _optask_: data movement and single-node data processing

## Future

- Scalability of ODOP
- Scheduling algorithm effect on different types of application, optask, and environment
