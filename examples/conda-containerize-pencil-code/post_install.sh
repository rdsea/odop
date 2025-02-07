#!/bin/bash

sample=conv-slab
install_dir=pc_install

cd ${CW_INSTALLATION_PATH}

set -ex
git clone https://github.com/pencil-code/pencil-code.git

cd pencil-code
. sourceme.sh
cd ..

mkdir -p ${install_dir}
cp -r ${PENCIL_HOME}/samples/${sample}/* ${install_dir}/
cd ${install_dir}

# Generate a config file
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

# Build pencil code
pc_setupsrc
pc_build -j 12 -f ./$config_file

# PC is a convoluted mess when it comes to installing and running binaries.
# Make wrappers that can be called from outside
mkdir -p ${CW_INSTALLATION_PATH}/bin

start_file=${CW_INSTALLATION_PATH}/bin/start.sh
tee $start_file << EOF > /dev/null
#!/bin/bash

cd ${CW_INSTALLATION_PATH}
cd pencil-code
. sourceme.sh
cd ../$install_dir
./start.csh
EOF

run_file=${CW_INSTALLATION_PATH}/bin/run.sh
tee $run_file << EOF > /dev/null
#!/bin/bash

cd ${CW_INSTALLATION_PATH}
cd pencil-code
. sourceme.sh
cd ../$install_dir
./run.csh
EOF

chmod +x $start_file $run_file
