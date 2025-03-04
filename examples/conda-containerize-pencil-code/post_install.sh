#!/bin/bash

sample=gputest

src_dir=${CW_INSTALLATION_PATH}/pencil-code
build_dir=${CW_INSTALLATION_PATH}/build
bin_dir=${CW_INSTALLATION_PATH}/bin
data_dir=${CW_INSTALLATION_PATH}/data

# Clone pencil-code and set correct git branches
set -ex
git clone https://github.com/pencil-code/pencil-code.git ${src_dir}
cd ${src_dir}
git checkout gputestv6
git submodule update --init --recursive
cd src/astaroth/submodule/
git checkout PCinterface_2019-8-12

# Setup sources and copy a sample to build
. ${src_dir}/sourceme.sh
cd
mkdir -p ${build_dir}
cp -r ${src_dir}/samples/${sample}/* ${build_dir}/
cd ${build_dir}

# replace some runtime parameters
sed -i 's/\(ncpus\)=16/\1=8/' src/cparam.local
sed -i 's/\(nprocy\)=4/\1=2/' src/cparam.local
sed -i 's/\(nxgrid\)=64/\1=32/' src/cparam.local

# Add a data dir file that pencil code uses
datadir_file=${build_dir}/datadir.in
tee ${datadir_file} << EOF > /dev/null
${data_dir}
EOF

# build pencil code
pc_setupsrc
pc_build -j 12 -f ${src_dir}/config/hosts/lumi/host-uan01-GNU_Linux.conf 

# Add binaries we want to run from outside the container to ${bin_dir}
cd
mkdir -p ${bin_dir}
cp ${src_dir}/bin/getconf.csh ${bin_dir}/.
cp ${src_dir}/bin/start.csh ${bin_dir}/.
cp ${build_dir}/src/*.x ${bin_dir}/

#start_file=${bin_dir}/pcc_start.sh
#tee ${start_file} << EOF > /dev/null
##!/bin/bash
#
#. ${src_dir}/sourceme.sh
#cd ${build_dir}
#./start.csh
#EOF
#
#run_file=${bin_dir}/pcc_run.sh
#tee ${run_file} << EOF > /dev/null
##!/bin/bash
#
#. ${src_dir}/sourceme.sh
#cd ${build_dir}
#./src/run.x
#EOF
#
#chmod +x ${start_file} ${run_file}
