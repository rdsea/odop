"""A scheduling algorithm for Odop that assigns tasks in priority
order
"""

import logging

from odop.scheduler.algorithms import Algorithm

logging.basicConfig(
    format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO
)


class Priority(Algorithm):
    def task_priority(self, task):
        """Return the priority value of the task inverted."""
        return task.priority

    def next_tasks(self, task_queue: dict, available_resource: dict) -> dict:
        """
        Returns the placement of tasks to be run next.

        If a task cannot be assigned to a node, return tasks already assigned. Don't
        assign lower priority tasks.
        """
        if not task_queue:
            return None

        # initialize task_placement
        task_placement = {}

        # sort the task_ids by increasing queued_timestamp
        sorted_task_ids = self.get_sorted_task_id_list(task_queue)

        # assign tasks to resources in the order they were added to the
        for task_id in sorted_task_ids:
            # if no resources are available, break the loop
            if not available_resource:
                break

            # get the task and assign it to a resource
            task = task_queue[task_id]

            # assign the task to a resource
            assigned_resource = self.assign_task(task, available_resource)

            # if task can be assigned, update the available_resource and task_placement
            if assigned_resource is not None:
                self.update_resource(available_resource, assigned_resource)
                task_placement[task_id] = assigned_resource
            else:
                return task_placement

        return task_placement
