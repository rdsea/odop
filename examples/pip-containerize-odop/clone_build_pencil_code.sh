#!/bin/bash

ml LUMI/24.03
ml partition/G
ml buildtools/24.03
ml PrgEnv-cray/8.5.0
ml rocm/6.0.3

# Clone pencil-code and set correct git branches
set -ex
git clone https://github.com/pencil-code/pencil-code.git
cd pencil-code
git checkout gputestv6
git submodule update --init --remote
cd src/astaroth/submodule/
git checkout PCinterface_2019-8-12

# Setup sources and copy a sample to build
cd ../../..
. sourceme.sh
mkdir -p test_run/data
cd test_run
cp -r ../samples/gputest/* .

# for a single node run, replace some runtime parameters
#sed -i 's/\(ncpus\)=16/\1=8/' src/cparam.local
#sed -i 's/\(nprocy\)=4/\1=2/' src/cparam.local
#sed -i 's/\(nxgrid\)=64/\1=32/' src/cparam.local

# build pencil code
pc_setupsrc

# Need to build on a GPU node to get the offload-arch correctly
#pc_build -j 12 -f ../config/hosts/lumi/host-uan01-GNU_Linux.conf -t shared_lib
#pc_build -j 12 -f ../config/hosts/lumi/host-uan01-GNU_Linux.conf
