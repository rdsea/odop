# Note that /projappl/project_462000509/odop-containerized/ already has an installed and
# containerized odop, no need to perfom the steps below anymore.

# Required modules
ml LUMI/24.03
ml partition/G
ml cray-python
ml lumi-container-wrapper

# Add Odop from git as requirement
echo "git+ssh://git@github.com/rdsea/odop.git@main#egg=odop" > requirements.txt

# Command to run
pip-containerize new --prefix /projappl/project_462000509/odop-containerized/ requirements.txt 
