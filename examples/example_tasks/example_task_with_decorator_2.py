# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.
import argparse
import multiprocessing
import os
import sys
import threading
import time

import yaml

import odop
from odop.odop_obs import OdopObs

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


@odop.task(name="example_task", time="2h", cpus=2, memory="2G")
def example_task_function():
    # The task can be an arbitrary Python function
    print("Running example task")
    time.sleep(1)


@odop.task(name="heavy_work_process", time="10s", cpus=1, memory="1G")
def heavy_work_process():
    _ = sum(x * x for x in range(10**8))


@odop.task(name="heavy_work_thread", time="5s", cpus=1, memory="1G")
def heavy_work_thread():
    _ = sum(x * x for x in range(10**7))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="config path", default="./odop_conf.yaml"
    )
    args = parser.parse_args()
    config_file = args.config
    config = yaml.safe_load(open(config_file))
    odop_obs = OdopObs(config)
    odop_obs.start()
    i = 0
    for _ in range(0, 5):
        processes = []
        for _ in range(2):
            p = multiprocessing.Process(target=heavy_work_process)
            processes.append(p)
            p.start()

        threads = []
        for _ in range(2):
            t = threading.Thread(target=heavy_work_thread)
            threads.append(t)
            t.start()

        for p in processes:
            p.join()

        for t in threads:
            t.join()
    print("Done!!!")
    odop_obs.stop()
