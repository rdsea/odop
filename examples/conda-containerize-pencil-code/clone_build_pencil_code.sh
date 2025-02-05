#!/bin/bash

ml LUMI/24.03
ml partition/C
ml buildtools
ml PrgEnv-gnu/8.5.0

config_file=lumi_gnu.config

tee $config_file << 'EOF' > /dev/null
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

set -exu
git clone https://github.com/pencil-code/pencil-code.git

cd pencil-code
. sourceme.sh
mkdir test_run
cd test_run
cp -r ../samples/conv-slab/* .
mkdir data

pc_setupsrc

pc_build -f ../../$config_file
