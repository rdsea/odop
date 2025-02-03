"""A Python script that loads and executes a single copy of an Odop task."""

import os
import sys

import click
import cloudpickle
import psutil
import yaml

from odop.common import create_logger
from odop.engine import cgroup

logger = create_logger("engine")


@click.command()
@click.option("--config", required=True, help="Path to the YAML configuration file.")
def main(config):
    try:
        with open(config) as f:
            config = yaml.safe_load(f)

        with open(config["task_file"], "rb") as f:
            task = cloudpickle.load(f)

        hostname = os.uname().nodename
        if hostname not in config["placement"]:
            raise Exception(f"Task {config['task_file']} not placed on this host.")
        cpu_list = config["placement"][hostname]["cpus"]

        logger.info(
            f"Executing task {config['task_file']} with parameters {config['parameters']}"
        )
        cpu_group = cgroup.get_cpu_group()
        if cpu_group is None:
            logger.info("Task {config['task_file']} could not get CPU group.")
        else:
            logger.info(f"Task {config['task_file']} CPU group: {cpu_group}")

        try:
            process = psutil.Process()
            process.cpu_affinity(cpu_list)
        except Exception as e:
            logger.info("Failed to set CPU affinity.")
            logger.info(e)

        task(**config["parameters"])
    except Exception as e:
        logger.info(f"Error executing task {config['task_file']}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
