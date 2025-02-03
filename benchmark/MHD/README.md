# MHD Benchmark

## Intro to application

- Magnetohydrodynamics (MHD) simulations is currently used to model the solar magnetic field evolution for the prediction of
  space weather and climate
- Library used: [pencil-code](https://github.com/pencil-code/pencil-code) and [Astaroth](https://bitbucket.org/jpekkila/astaroth)
- Targeted HPC environment is [LUMI](https://docs.lumi-supercomputer.eu/) with AMD GPU. For Nvidia GPU, some parameter in the build script must be changed.

## Benchmark

### BPOD paper

- Focus on the definition and how to determine opportunistic task
- Early-state benefit of ODOP in terms of total required time with two types of _optask_: data movement and single-node data processing

## Future

- Scalability of ODOP
- Scheduling algorithm effect on different types of application, optask, and environment
