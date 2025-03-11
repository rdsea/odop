 #!/bin/bash

[ $# -eq 4 ] || { 
    echo "Give four arguments:"
    echo "path to requirements.txt"
    echo "path to install dir"
    echo "path to post build script"
    echo "path to env.yaml"
    echo "For example:"
    echo "./build.sh requirements.txt /projappl/project_462000509/pc-containerized post_install.sh env.yaml"
    exit 1
}

requirements=$1
prefix=$2
post_build=$3
env=$4

ml LUMI/24.03
ml partition/G
ml buildtools
ml PrgEnv-cray/8.5.0
ml rocm/6.0.3
ml lumi-container-wrapper

conda-containerize new -r $requirements --prefix $prefix --post $post_build -w bin/pencil-code $env
