class DummyTask:
    def __init__(self, priority=0):
        self.name = ""
        self.time = 1
        self.memory = 0
        self.nodes = "any"
        self.ranks_per_node = "any"
        self.ranks = "any"
        self.cpus_per_rank = "any"
        self.cpus = 1
        self.disk_limit = 0
        self.index = 0

        self.execution_type = ""
        self.priority = priority
        self.filename = None

        self.task_id = None
        self.status = ""
