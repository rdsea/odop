#!/bin/bash

module load CrayEnv
module load rocm
module load cray-python

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
