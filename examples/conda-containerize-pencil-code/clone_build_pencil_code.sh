#!/bin/bash

module load CrayEnv
module load rocm
module load cray-python

config_file=lumi_gnu.config

tee $config_file <<'EOF' >/dev/null
%include compilers/GNU-GCC_MPI
%section Makefile
        # turn on software optimizations
        FC = ftn
        F90 = $(FC)
        CC = cc
        FFLAGS += -O3 -g
        FFLAGS += -mcmodel=large 
        CFLAGS += -O2 -D_GNU_SOURCE
        LDFLAGS += -ldl -lpthread 
%endsection Makefile

%section runtime
        mpiexec = srun
%endsection runtime
EOF

set -ex
git clone https://github.com/pencil-code/pencil-code.git

cd pencil-code
git reset --hard 5e2c0e4
git submodule update --init
cd src/astaroth/submodule
git reset --hard 6ba44bab
cd ../../..
. sourceme.sh
cd samples/gputest

pc_setupsrc

pc_build
