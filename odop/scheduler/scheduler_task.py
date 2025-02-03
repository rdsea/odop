from odop.engine.engine import StatusCode


class SchedulerTask:
    """Placeholder for a queued task.

    Represents a runnable task with a specific set of parameters.
    """

    next_id = 0

    def __init__(self, task, batch=None):
        self.name = task.name
        self.index = task.index
        self.time = task.time
        self.memory = task.memory

        self.nodes = task.nodes
        self.ranks = task.ranks
        self.ranks_per_node = task.ranks_per_node
        self.cpus = task.cpus
        self.cpus_per_rank = task.cpus_per_rank

        self.disk_limit = task.disk_limit
        self.execution_type = task.execution_type
        self.priority = task.priority
        self.filename = task.filename
        self.queued_timestamp = 0

        self.id = SchedulerTask.next_id
        SchedulerTask.next_id += 1

        self.status = StatusCode.PENDING
        self.pid = "none"
        self.times_failed = 0  # Try the task a number of times before giving up
        # Add a timer for retry. There might be a timing issue.

        self.execution_timestamp = 0
        self.execution_nodes = {}

        if batch is not None:
            self.parameters = {"filenames": batch}

    def dict(self):
        dictionary = self.__dict__.copy()
        dictionary["status"] = self.status.value
        return dictionary
