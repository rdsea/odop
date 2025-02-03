"""A scheduling algorithm for Odop that assigns tasks in priority
order
"""

import logging

from odop.scheduler.algorithms import Algorithm

logging.basicConfig(
    format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO
)


class FIFO(Algorithm):
    def task_priority(self, task):
        """Return the priority value of the task directly"""
        return -task.queued_timestamp
