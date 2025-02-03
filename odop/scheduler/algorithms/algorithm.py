import copy
import os

from odop.scheduler.scheduler_task import SchedulerTask


class Algorithm:
    def task_priority(self, task: SchedulerTask) -> int:
        """Return as numerical value for ordering tasks.
        Tasks with higher scheduling order will be assigned first.

        Args:
            task (SchedulerTask): Task to be ordered.

        Returns:
            int: Numerical value for ordering tasks.
        """

        return task.priority

    def get_sorted_task_id_list(self, task_queue: dict) -> list:
        """Sort tasks before attempting to assign to nodes.

        Args:
            task_queue (dict): A dictionary of tasks to be sorted.

        Returns:
            list: A list of task_ids sorted by decreasing assignment
            priority.
        """

        sorted_tasks = sorted(
            task_queue.items(),
            key=lambda item: self.task_priority(item[1]),
            reverse=True,
        )
        sorted_task_ids = [task_id for task_id, _ in sorted_tasks]
        return sorted_task_ids

    def node_priority(self, node: dict) -> int:
        """Return as numerical value for ordering nodes.

        Args:
            node (dict): Node to be ordered.
                Example:
                {
                    'memory': int,
                    'cpus': []  # Example: ["core_1", "core_2", ...],
                }

        Returns:
            int: Numerical value for ordering nodes.
        """

        return -len(node["cpus"])

    def get_sorted_node_list(self, node_queue: dict) -> list:
        """Sort nodes before attempting to assign tasks.

        Args:
            node queue (dict): A dictionary of nodes to be sorted.

        Returns:
            list: A list of node names sorted by decreasing assignment
        """
        sorted_nodes = sorted(
            node_queue.keys(),
            key=lambda item: self.node_priority(node_queue[item]),
        )
        return sorted_nodes

    def build_assign_block(self, task, nodes_ids, resources):
        """Organize the task cpu and node requirements into blocks that can be allocated to individual nodes"""

        # Slurm does not different numbers of ranks per node or
        # cpus per rank. For now, we assign a single block per node
        # in this case
        if "SLURM_JOB_ID" in os.environ:
            require_node = True
        else:
            require_node = False

        # construct minimal blocks
        if task.nodes != "any":
            require_node = True
            if task.nodes == "all":
                n_blocks = len(nodes_ids)
            else:
                n_blocks = task.nodes
            if task.ranks_per_node == "all":
                block_ranks = "all"
                block_cpus = "all"
            else:
                block_ranks = task.ranks_per_node
                block_cpus = task.cpus_per_rank * task.ranks_per_node

        elif task.ranks != "any":
            block_ranks = 1
            if task.ranks == "all":
                n_blocks = len(nodes_ids)
                block_cpus = 1
            else:
                n_blocks = task.ranks
                if task.cpus_per_rank == "any":
                    block_cpus = 1
                elif task.cpus_per_rank == "all":
                    block_cpus = "all"
                else:
                    block_cpus = task.cpus_per_rank

        elif task.cpus != "any":
            n_blocks = 1
            block_ranks = 1
            block_cpus = task.cpus

        else:
            n_blocks = 1
            block_ranks = 1
            block_cpus = 1

        return n_blocks, block_ranks, block_cpus, require_node

    def assign_task(self, task: SchedulerTask, resources: dict) -> bool:
        """
        Check if a task can be assigned to a resource based on resource availability.
        Input:
            task: Task
                Inside the task:
                - resource_requirement: {
                    'memory': int,
                    'nodes', [int, "all", "any"],
                    'ranks': [int, "all", "any"],
                    'cpus': [int, "all", "any"]  # Example: [100, 200, ...]
                    'ranks_per_node': [int, "any", "all"],
                    'cpus_per_rank': [int, "any", "all"]
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
        nodes_ids = self.get_sorted_node_list(available_resources["nodes"])

        # Reorganize task cpu requirements into blocks that can be allocated to individual nodes
        n_blocks, block_ranks, block_cpus, require_node = self.build_assign_block(
            task, nodes_ids, available_resources
        )

        # check if there are enough resources to assign the task with the given number of nodes
        for _node in range(n_blocks):
            # Check if there is a node to assign the task with the given number of cpus
            assigned_node = None
            for node_id in nodes_ids:
                if node_id not in available_resources["nodes"]:
                    continue
                resource = available_resources["nodes"][node_id]
                can_assign = False
                # If all CPUs are required, check that the node is free
                if block_cpus == "all" and resource["free"]:
                    can_assign = True
                elif block_cpus != "all":
                    can_assign = (
                        resource["memory"] >= task.memory
                        and len(resource["cpus"]) >= block_cpus
                    )

                # Best fit
                if can_assign:
                    # if node is not assigned yet, assign the task to the node
                    if assigned_node is None:
                        assigned_node = node_id
                    else:
                        # if the node is already assigned, check if the current node is a better fit
                        if len(resource["cpus"]) < len(
                            available_resources["nodes"][assigned_node]["cpus"]
                        ):
                            assigned_node = node_id
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

    def update_resource(
        self, available_resource: dict, assigned_resource: dict
    ) -> None:
        """
        Update the available_resource by removing the assigned_resource.
        Input:
            available_resource: dict
                Example:
                {
                    '@node_id': {
                        'memory': int,
                        'cpus': []  # Example: ["core_1", "core_2", ...],
                        'private_disk': int,
                    },
                    shared_disk: int,
                }
            assigned_resource: dict
                Example:
                {
                    '@node_id': {
                        'memory': int,
                        'cpus': []  # Example: ["core_1", "core_2", ...],
                        'private_disk': int,
                    },
                    shared_disk: int,
                }
        Output:
            None
        """
        # update the available_resource by removing the assigned_resource
        for node_id in assigned_resource.keys():
            available_resource["nodes"][node_id]["memory"] -= assigned_resource[
                node_id
            ]["memory"]
            available_resource["nodes"][node_id]["cpus"] = available_resource["nodes"][
                node_id
            ]["cpus"][len(assigned_resource[node_id]["cpus"]) :]

    def next_tasks(self, task_queue: dict, available_resource: dict) -> dict:
        """
        Returns the placement of tasks to be run next.
        Note: @<id> -> id of the object as a string
        Input:
            task_queue: dict
                Example:
                {
                    '@task_id': SchedulerTask
                }
            available_resource: dict
                Example:
                {
                    nodes: {
                        '@node_id': {
                            'memory': int,
                            'cpus': []  # Example: ["core_1", "core_2", ...],
                            'private_disk': int,
                        },
                    }
                    shared_disk: int,
                }
        Output:
            task_placement: dict
                Example:
                {
                    '@task_id': {
                        '@node_id': {
                            'memory': int,
                            'cpus': []  # Example: ["core_1", "core_2", ...],
                            'private_disk': int,
                        }
                    }
                }

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

        return task_placement
