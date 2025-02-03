# How to run pencil-code

## Load correct module

module load CrayEnv
module load rocm
module load cray-python

## Get the code and correct branch

- clone pencil code:

```
git clone https://github.com/pencil-code/pencil-code.git
cd pencil-code
```

source pencil:
. ./sourceme.sh

```
git checkout gputestv6
```

- pull submodules and go to the correct branch there:

  ```
  git submodule update --init --remote
  cd src/astaroth/submodule
  git checkout PCinterface_2019-8-12
  ```

- setup correct grid dims (1024 is big, the first run will take almost an hour with 1000 time steps and diagnostic per 100 steps) and number of processes (I used 8 process as I only run 1 nodes)

  ```
  cd ../../../samples/gputest ($HOME/pencil-code/samples/gputest)
  vim src/cparam.local
  set ncpus to 8, nprocy to 2
  set nxgrid to 32 for a 32^3 domain.
  ```

## Compile

- set up source and compile:

  ```
  pc_setupsrc
  pc_build
  ```

- compile shared library for python job (should be run before pc_build):

  ```
  pc_build -t shared_lib
  ```

- run python-version (if run with the monitoring, you should install the package and set up the .odop directory,:
  ```
  sbatch python-dispatch.sh
  ```

## NOTE

- In pencile-code/sample/gputest/src/cparam.local, nt means the number of iterations and it1 means how many steps between diagnostic output, so to get it every 100th timestep it should be it1=100, nsave is how many timestep we update the snapshot
- If the compiling has error related to some compiler flag, just exit the ssh, load the module and source sourceme.sh again. Should load the module before sourcing sourcme.sh
- Use symlink if the grid size is too big because the use home disk can only be 20GB while the project scratch is 50TB (can extended to 500GB) ln -s /scratch/project_462000509/dung_gputest/data/ data
  nt=1000, it1=100, isave=2000, itorder=3,

- important files:
  - pencil-code/src/equ.f90:536
  - pencile-code/samples/gputest/run.in
  - pencil-code/samples/gputest/Makefile.Local: add POWER = power_spectrum FOURIER = fourier_fftpack

# Add in src/Makefile.local

- change VENDOR to nvidia
- The script changes to odop.sh
