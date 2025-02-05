#!/bin/bash

cd $CW_INSTALLATION_PATH

set -ex
git clone https://github.com/pencil-code/pencil-code.git

cd pencil-code
. sourceme.sh
mkdir test_run
cd test_run
cp -r ../samples/conv-slab/* .
mkdir data

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

pc_setupsrc
pc_build -j 12 -f ./$config_file
