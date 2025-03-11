#!/bin/bash

# Define variables
## Sample
sample=gputest

## Directories
src_dir=${CW_INSTALLATION_PATH}/pencil-code
build_dir=${CW_INSTALLATION_PATH}/build
bin_dir=${CW_INSTALLATION_PATH}/bin/pencil-code

# Create directories
mkdir -p ${src_dir}
mkdir -p ${build_dir}
mkdir -p ${bin_dir}

# Clone & setup
set -ex
git clone https://github.com/pencil-code/pencil-code.git ${src_dir}
cd ${src_dir}
git checkout gputestv6
git submodule update --init --recursive
cd src/astaroth/submodule/
git checkout PCinterface_2019-8-12

# Setup sources
cd ${src_dir}
. sourceme.sh
cp -r ${src_dir}/samples/${sample}/* ${build_dir}/

# Build
cd ${build_dir}
## Replace params
sed -i 's/\(ncpus\)=16/\1=8/' src/cparam.local
sed -i 's/\(nprocy\)=4/\1=2/' src/cparam.local
sed -i 's/\(nxgrid\)=64/\1=32/' src/cparam.local

## Compilation
pc_setupsrc
pc_build -j 12 -f ${src_dir}/config/hosts/lumi/host-uan01-GNU_Linux.conf 

# Add wrappers
## start.csh wrapper
start_file=${bin_dir}/start.sh
tee ${start_file} << EOF > /dev/null
#!/bin/bash
PATH=${src_dir}/bin:${PATH} start.csh
EOF

## run.x wrapper
run_file=${bin_dir}/run.sh
tee ${run_file} << EOF > /dev/null
#!/bin/bash
LD_LIBRARY_PATH=${build_dir}/src/astaroth:${LD_LIBRARY_PATH} ${build_dir}/src/run.x
EOF

## Make wrappers executable
chmod +x ${start_file} ${run_file}
