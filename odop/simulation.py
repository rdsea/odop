import multiprocessing
import os
import time
from typing import Union

import psutil

from odop.common import create_logger

LOAD_INTERVAL = 0.3

logger = create_logger("simulation")


def simulate_load(expected_utilization_list: list[tuple[int, int, int, int, bool]]):
    processes = []
    i = 0
    pid = 0
    affinity = os.sched_getaffinity(pid)
    allowed_core_list = list(affinity)
    for (
        utilization,
        cycle_length,
        num_cycle,
        between_cycle_interval,
        sleep_before_load,
    ) in expected_utilization_list:
        core_id = allowed_core_list[i]
        i += 1
        p = multiprocessing.Process(
            target=generate_load,
            args=(
                utilization,
                cycle_length,
                num_cycle,
                between_cycle_interval,
                sleep_before_load,
                core_id,
            ),
        )
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


def generate_load(
    utilization: int,
    cycle_length: float,
    num_cycle: int,
    between_cycle_interval: float,
    sleep_before_load: bool,
    core_id: int,
):
    try:
        p = psutil.Process()
        p.cpu_affinity([core_id])
        for _ in range(num_cycle):
            if sleep_before_load:
                time.sleep(between_cycle_interval)
            start_time = time.time()
            cycle_start = time.time()
            while time.time() - cycle_start <= cycle_length:
                while time.time() - start_time < utilization / 100.0 * LOAD_INTERVAL:
                    pass
                time.sleep(LOAD_INTERVAL - utilization / 100.0 * LOAD_INTERVAL)
                start_time += LOAD_INTERVAL
            if not sleep_before_load:
                time.sleep(between_cycle_interval)
    except KeyboardInterrupt:
        pass


def simulate_cyclical_process(
    expected_utilization_list: Union[list, None] = None,
    num_processes=8,
):
    """
    expected_utilization_list:
    utilization, cycle_length, num_cycle, between_cycle_interval, sleep_before_load
    """
    if expected_utilization_list is None:
        expected_utilization_list = [
            (100, 10, 10, 0, False),
            (97, 10, 10, 0, False),
            (90, 7, 10, 3, True),
            (90, 7, 10, 3, True),
            (90, 7, 10, 3, True),
            (0, 10, 10, 0, False),
            (10, 10, 10, 0, False),
        ]

    logger.info("Simulating cyclical process")
    try:
        simulate_load(expected_utilization_list)
        logger.info("Simulation complete")
    except KeyboardInterrupt:
        logger.info("Simulation interrupted")
