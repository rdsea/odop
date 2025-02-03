"""A scheduling algorithm for Odop that assigns tasks in order
of largest first (in terms of CPU requirements)
"""

import logging

from odop.common import LARGE_INT
from odop.scheduler.algorithms import Algorithm

assumed_cpus_per_node = 10240

logging.basicConfig(
    format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO
)


class BestFit(Algorithm):
    def task_priority(self, task):
        """Return the priority value of the task.

        Order by task size in terms of CPU count. We don't know how many CPUs
        each node has, so when a full node is required, we return multiply
        the node count with a larg-ish number.
        """
        if task.nodes == "all":
            return LARGE_INT
        if task.ranks == "all":
            return LARGE_INT

        if task.nodes == "any":
            if task.ranks == "any":
                return task.cpus
            else:
                return task.ranks * task.cpus_per_rank
        else:
            return task.nodes * task.ranks_per_node * task.cpus_per_rank
