import math
import os
import os.path
import pathlib
import shutil
import tempfile

import click

PENCIL_CODE_SAMPLE = "gputest"


class Experiment:
    def __init__(
        self, experiment_type: str, ngrid: tuple[int, int, int], ncpus: int, gpus: int
    ):
        # x, y, z
        self.ngrid = ngrid
        self.ncpus = ncpus
        self.gpus = gpus

        # Do a naive distribution over the Y axis.
        # x, y, z
        self.nproc = (1, gpus, 1)

        self.name = f"{experiment_type}_{self.ngrid[0]}_{self.ngrid[1]}_{self.ngrid[2]}_{self.gpus}"

    def __str__(self):
        return self.name


def get_grid_memory_cost(grid: tuple[int, int, int]) -> int:
    """Return memory cost of a grid size in megabytes."""
    vert_bufs = 8
    precision = 64
    copies = 2

    return int(
        (grid[0] * grid[1] * grid[2]) * vert_bufs * precision * copies / 8 / 1000 / 1000
    )


def get_grid_size_for_memory(available_memory: int) -> tuple[int, int, int]:
    """Finds a grid size that maximally saturates the memory of available GPUs."""
    nxgrid = 0
    nygrid = 0
    nzgrid = 0
    step = 1024

    while step >= 2:
        nxgrid += step
        nygrid += step
        nzgrid += step

        if get_grid_memory_cost((nxgrid, nygrid, nzgrid)) < available_memory:
            continue

        nxgrid -= step
        nygrid -= step
        nzgrid -= step
        step = int(step / 2)

    return int(nxgrid), int(nygrid), int(nzgrid)


def get_scaling_steps(min: int, max: int) -> list[int]:
    assert min <= max

    steps = [min]
    if min == 1 and max != 1:
        steps.append(2)

    while steps[-1] < max:
        steps.append(pow(steps[-1], 2))

    return steps


def generate_weak_scaling_experiments(
    gpu_size: int,
    gpus_per_node: int,
    cpus_per_gpu: int,
    max_gpus: int,
    min_gpus: int,
):
    max_node_count = math.ceil(max_gpus / gpus_per_node)

    experiments: list[Experiment] = []

    if min_gpus < gpus_per_node:
        # Saturate a single node
        for gpu_count in get_scaling_steps(min_gpus, gpus_per_node):
            grid_size = get_grid_size_for_memory(gpu_count)
            experiments.append(
                Experiment("weak", grid_size, cpus_per_gpu * gpu_count, gpu_count)
            )
    else:
        # Add a base case and proceeded to scaling over nodes.
        grid_size = get_grid_size_for_memory(gpu_size * min_gpus)

        experiments.append(
            Experiment("weak", grid_size, cpus_per_gpu * min_gpus, min_gpus)
        )

    base_node_count = math.ceil(min_gpus / gpus_per_node)

    if base_node_count == max_node_count:
        return experiments

    # Add nodes
    for node_count in get_scaling_steps(base_node_count + 1, max_node_count):
        grid_size = get_grid_size_for_memory(node_count * gpus_per_node * gpu_size)
        experiments.append(
            Experiment(
                "weak",
                grid_size,
                node_count * cpus_per_gpu * gpu_count,
                node_count * gpu_count,
            )
        )

    return experiments


def generate_strong_scaling_experiments(
    gpu_size: int,
    gpus_per_node: int,
    cpus_per_gpu: int,
    max_gpus: int,
    min_gpus: int,
):
    base_grid_size = get_grid_size_for_memory(gpu_size * min_gpus)
    base_node_count = math.ceil(min_gpus / gpus_per_node)
    max_node_count = math.ceil(max_gpus / gpus_per_node)

    experiments: list[Experiment] = []

    if min_gpus < gpus_per_node:
        # Saturate a single node
        for gpu_count in get_scaling_steps(min_gpus, gpus_per_node):
            experiments.append(
                Experiment(
                    "strong", base_grid_size, cpus_per_gpu * gpu_count, gpu_count
                )
            )
    else:
        # Add a base case and proceeded to scaling over nodes.
        experiments.append(
            Experiment("strong", base_grid_size, cpus_per_gpu * min_gpus, min_gpus)
        )

    if base_node_count == max_node_count:
        return experiments

    # Add nodes
    for node_count in get_scaling_steps(base_node_count + 1, max_node_count):
        experiments.append(
            Experiment(
                "strong",
                base_grid_size,
                node_count * cpus_per_gpu * gpu_count,
                node_count * gpu_count,
            )
        )

    return experiments


EXPERIMENT_GENERATORS = {
    "weak-scaling": generate_weak_scaling_experiments,
    "strong-scaling": generate_strong_scaling_experiments,
}


def configure_cparams(cparams_file: pathlib.Path, experiment: Experiment):
    cparams = [
        f"integer, parameter :: ncpus={experiment.gpus}\n",
        f"integer, parameter :: nprocx={experiment.nproc[0]},nprocy={experiment.nproc[1]},nprocz={experiment.nproc[1]}\n",
        f"integer, parameter :: nxgrid={experiment.ngrid[0]},nygrid={experiment.ngrid[1]},nzgrid={experiment.ngrid[2]}\n",
    ]

    with open(cparams_file, "w") as f:
        f.writelines(cparams)


@click.group()
def cli():
    """Tool for generating scaling experiments."""
    pass


@cli.command()
@click.option("--gpu-size", type=click.IntRange(1), help="", required=True)
@click.option("--gpus-per-node", type=click.IntRange(1), help="", required=True)
@click.option("--cpus-per-gpu", type=click.IntRange(1), help="", required=True)
@click.option("--max-gpus", type=click.IntRange(1), help="", required=True)
@click.option("--min-gpus", type=click.IntRange(1), help="", required=True)
@click.option(
    "--output-dir",
    type=click.Path(exists=False, path_type=pathlib.Path),
    help="",
    required=True,
)
@click.option(
    "--pencil-code",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        path_type=pathlib.Path,
    ),
    help="",
    required=True,
)
@click.option(
    "--purpose",
    type=click.Choice(EXPERIMENT_GENERATORS.keys(), case_sensitive=False),
    help="",
    required=True,
)
def generate(
    gpu_size: int,
    gpus_per_node: int,
    cpus_per_gpu: int,
    max_gpus: int,
    min_gpus: int,
    output_dir: pathlib.Path,
    pencil_code: pathlib.Path,
    purpose: str,
):
    """Experiment generator."""

    # Check input parameters
    sample_path: pathlib.Path = pencil_code / "samples" / PENCIL_CODE_SAMPLE
    if not sample_path.is_dir():
        raise click.BadParameter(
            f"The provided pencil-code repository does not contain sample '{PENCIL_CODE_SAMPLE}' at path {sample_path}",
            param="pencil-code",
        )

    if output_dir.is_dir() and len(list(output_dir.iterdir())) != 0:
        raise click.BadParameter(
            f"The output directory {output_dir} is not empty. Choose a different output directory."
        )

    # Generate experiment definitions
    experiment_generator = EXPERIMENT_GENERATORS[purpose]
    experiments = experiment_generator(
        gpu_size, gpus_per_node, cpus_per_gpu, max_gpus, min_gpus
    )

    # Generate experiments
    with tempfile.TemporaryDirectory() as template_dir:
        # Create a base template for experiments from the pencil_code sample to ease copying of the tree to the
        # experiment directories.
        for f in sample_path.glob("*.in"):
            target = os.path.join(template_dir, f.name)
            shutil.copy2(f, target)
        os.makedirs(os.path.join(template_dir, "src"))
        for f in sample_path.glob("src/*.local"):
            target = os.path.join(template_dir, "src", f.name)
            shutil.copy2(f, target)

        # Create the experiments
        for experiment in experiments:
            print(f"Creating experiment '{experiment.name}'")

            experiment_dir: pathlib.Path = output_dir / str(experiment)
            cparam_local_filepath: pathlib.Path = (
                experiment_dir / "src" / "cparam.local"
            )

            shutil.copytree(template_dir, experiment_dir)
            configure_cparams(cparam_local_filepath, experiment)


@cli.command()
@click.option(
    "--gpu-size",
    type=click.IntRange(1),
    help="Available GPU memory [MBs]",
    required=True,
)
def get_grid(gpu_size: int):
    """Finds a grid size that fills given amount of memory."""
    print(get_grid_size_for_memory(gpu_size))


@cli.command()
@click.option(
    "--grid", type=(int, int, int), help="Grid size (X, Y, Z).", required=True
)
def get_memory(grid):
    """Prints the memory cost of a given grid."""
    print(get_grid_memory_cost(grid))


if __name__ == "__main__":
    cli()
