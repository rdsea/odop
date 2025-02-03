import copy
import logging

from odop.scheduler.algorithms import Algorithm
from odop.scheduler.scheduler_task import SchedulerTask

logging.basicConfig(
    format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO
)


class RoundRobin(Algorithm):
    """
    A scheduling algorithm for Odop that assigns tasks following Round Robin pattern
    """

    def __init__(self):
        self.current_node = 0

    def assign_task(self, task: SchedulerTask, resources: dict) -> bool:
        """
        Check if a task can be assigned to a resource based on resource availability.
        Input:
            task: Task
                Inside the task:
                - resource_requirement: {
                    'memory': int,
                    'cpus': [int]  # Example: [100, 200, ...]
                }
            resource: dict
                Example:
                {
                    @node_id: {
                        'memory': int,
                        'cpus': []  # Example: ["core_1", "core_2", ...],
                    }
                }
        Output:
            bool
        """

        available_resources = copy.deepcopy(resources)
        assigned_resource = {}
        nodes_ids = list(resources["nodes"].keys())

        # Reorganize task cpu requirements into blocks that can be allocated to individual nodes
        n_blocks, block_ranks, block_cpus, require_node = self.build_assign_block(
            task, nodes_ids, available_resources
        )

        # check if there are enough resources to assign the task with the given number of nodes
        for _node in range(n_blocks):
            # Check if there is a node to assign the task with the given number of cpus
            assigned_node = None
            for i in range(len(nodes_ids)):
                node_index = (i + self.current_node) % len(nodes_ids)
                node_id = nodes_ids[node_index]
                resource = available_resources["nodes"][node_id]
                # Select the node if it has enough resources
                # If all CPUs are required, check that the node is free
                if block_cpus == "all" and resource["free"]:
                    can_assign = True
                else:
                    can_assign = (
                        resource["memory"] >= task.memory
                        and len(resource["cpus"]) >= block_cpus
                    )
                if can_assign:
                    # if node is not assigned yet, assign the task to the node
                    if assigned_node is None:
                        assigned_node = node_id
                    self.current_node = node_index + 1
                    break

            # if no node is available to assign the task, return False
            if assigned_node is None:
                return None
            else:
                # assign the task to the node with specific cpus
                if assigned_node in assigned_resource:
                    assigned_resource[assigned_node]["cpus"] += available_resources[
                        "nodes"
                    ][assigned_node]["cpus"][:block_cpus]
                    assigned_resource[assigned_node]["ranks"] += block_ranks
                else:
                    assigned_resource[assigned_node] = copy.deepcopy(
                        available_resources["nodes"][assigned_node]
                    )
                    assigned_resource[assigned_node]["cpus"] = assigned_resource[
                        assigned_node
                    ]["cpus"][:block_cpus]
                    assigned_resource[assigned_node]["ranks"] = block_ranks
                if require_node:
                    available_resources["nodes"].pop(assigned_node)
                else:
                    available_resources["nodes"][assigned_node]["free"] = False
                    available_resources["nodes"][assigned_node]["cpus"] = (
                        assigned_resource[assigned_node]["cpus"][block_cpus:]
                    )

        return assigned_resource
