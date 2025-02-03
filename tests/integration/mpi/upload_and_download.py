import os
import shutil
import time

import yaml

import odop
import odop.simulation
from odop.common import ODOP_PATH


@odop.task(
    name="download",
    time="1m",
    memory="1G",
    priority=1,
    trigger=odop.Timer(interval="1s"),
)
def download_task():
    """Example task that simulates downloading a data file"""
    print("Downloading data")

    # Before running the example program creates files to download
    # Check if there is a file left and if so, copy one to a data folder.
    remote_files = os.listdir("remote_unprocessed_folder")
    local_files = os.listdir("unprocessed_data")
    print(remote_files)
    print(local_files)
    for file in remote_files:
        if file not in local_files:
            shutil.copy("remote_unprocessed_folder/" + file, "unprocessed_data/")
            break

    print("Download complete")


@odop.task(
    name="process",
    time="1m",
    memory="1G",
    nodes=2,
    priority=2,
    trigger=odop.FileIn("unprocessed_data"),
)
def process_task(filename):
    from mpi4py import MPI

    rank = MPI.COMM_WORLD.Get_rank()
    os.makedirs("processed_data", exist_ok=True)
    files = os.listdir("processed_data")
    index = 0
    while f"{index}_{rank}.txt" in files:
        index += 1
    filename = f"{index}_{rank}.txt"
    with open(f"processed_data/{filename}", "w") as f:
        f.write("This is a processed file")
    print(f"Processing {filename}")


def setup_test_environment():
    if os.path.exists("remote_processed_folder"):
        shutil.rmtree("remote_processed_folder", ignore_errors=True)
    if os.path.exists("remote_unprocessed_folder"):
        shutil.rmtree("remote_unprocessed_folder", ignore_errors=True)
    if os.path.exists("unprocessed_data"):
        shutil.rmtree("unprocessed_data", ignore_errors=True)
    if os.path.exists("processed_data"):
        shutil.rmtree("processed_data", ignore_errors=True)
    os.makedirs("remote_unprocessed_folder", exist_ok=True)
    os.makedirs("unprocessed_data", exist_ok=True)
    os.makedirs("processed_data", exist_ok=True)
    os.makedirs("remote_processed_folder", exist_ok=True)

    for i in range(2):
        with open(f"remote_unprocessed_folder/file_{i}.txt", "w") as f:
            f.write("This is a file")


if __name__ == "__main__":
    try:
        setup_test_environment()

        path = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(path, "odop_conf.yaml")
        odop.start(run_name="run_1", task_folder=path, config_file=config_file)

        time.sleep(5)

        run_folder = os.path.join(ODOP_PATH, "runs", "run_1")
        with open(os.path.join(run_folder, "status")) as f:
            status = yaml.safe_load(f)
        nodes = status["nodes"]

        assert len(nodes) == 2
        for _, value in nodes.items():
            assert value == 3

        remote_unprocessed_folder = os.listdir("remote_unprocessed_folder")
        unprocessed_data = os.listdir("unprocessed_data")
        processed_data = os.listdir("processed_data")
        assert len(unprocessed_data) == 2
        assert len(processed_data) == 6

    finally:
        odop.stop()
