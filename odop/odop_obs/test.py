import os
import multiprocessing
import time

import yaml

from odop_obs import OdopObs

def child_process(depth):
    process_id = os.getpid()
    print(f"Child process {process_id} created by {os.getppid()}.")
    create_processes(depth-1)
    time.sleep(10)
    print(f"Child process {process_id} finished.")

def create_processes(depth):
    if depth <= 0:
        return
    processes = []
    for _ in range(2):
        p = multiprocessing.Process(target=child_process, args=[depth])
        processes.append(p)
        p.start()
    for p in processes:
        p.join()

if __name__ == "__main__":
    config = yaml.safe_load(open("../odop_obs/odop_obs_conf.yaml"))
    odop_obs = OdopObs(config)
    odop_obs.start()
    depth = 4 # Change the value of depth for nesting depth
    create_processes(depth)
    odop_obs.stop()
