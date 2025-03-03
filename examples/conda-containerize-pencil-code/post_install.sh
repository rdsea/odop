#!/bin/bash

module load CrayEnv
module load rocm

sample=gputest
install_dir=pc_install

cd ${CW_INSTALLATION_PATH}

set -ex
git clone https://github.com/pencil-code/pencil-code.git

cd pencil-code

git reset --hard 5e2c0e4
git submodule update --init
cd src/astaroth/submodule
git reset --hard 6ba44bab
cd ../../..

. sourceme.sh
cd ..

mkdir -p ${install_dir}
cp -r ${PENCIL_HOME}/samples/${sample}/* ${install_dir}/
cd ${install_dir}

# Build pencil code
pc_setupsrc
pc_build

# PC is a convoluted mess when it comes to installing and running binaries.
# Make wrappers that can be called from outside
mkdir -p ${CW_INSTALLATION_PATH}/bin

start_file=${CW_INSTALLATION_PATH}/bin/start.sh
tee $start_file <<EOF >/dev/null
#!/bin/bash

cd ${CW_INSTALLATION_PATH}
cd pencil-code
. sourceme.sh
cd ../$install_dir
./start.csh
EOF

run_file=${CW_INSTALLATION_PATH}/bin/run.sh
tee $run_file <<EOF >/dev/null
#!/bin/bash

cd ${CW_INSTALLATION_PATH}
cd pencil-code
. sourceme.sh
cd ../$install_dir
./run.csh
EOF

chmod +x $start_file $run_file
