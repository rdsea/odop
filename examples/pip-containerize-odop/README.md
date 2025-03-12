# Contents
`clone_build_pencil_code.sh` clones pencil-code and sets it up in your current directory. Note that you need to build it still.

`containerize_odop.sh` uses `pip-containerize` to containerize odop. It's already been done, and it's available at the path specified in the script.

`disbatch.sh` was used to test that the compiled pencil-code runs correctly.

`python-dispatch.sh` can be used to run odop and pencil-code. `sbatch python-dispatch.sh` in e.g. `pencil-code/test_run/` directory created by `clone_build_pencil_code.sh` once you've built pencil-code. Note that the sbatch script uses the containerized python executable, which has odop in its `PYTHONPATH`.

`odop_conf.yaml` was copied directly from odop github repository and may be set up incorrectly. Feel free to correct it.
