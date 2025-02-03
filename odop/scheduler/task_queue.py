import multiprocessing

from .scheduler_task import SchedulerTask


class TaskQueue:
    def __init__(self):
        """Simple implementation of the task queue. Allows getting all tasks
        ordered by priority.
        """
        self.manager = multiprocessing.Manager()
        self.tasks = self.manager.list()

    def push(self, task):
        assert isinstance(task, SchedulerTask)
        self.tasks.append(task)
        self.tasks[:] = sorted(self.tasks, key=lambda task: task.priority)

    def pop(self):
        return self.tasks.pop()

    def get_all(self):
        tasks_copy = list(self.tasks)
        self.tasks[:] = []
        return tasks_copy

    def delete_id(self, task_id):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks[:] = self.tasks[:i] + self.tasks[i + 1 :]
                break

    def dict(self):
        return {task.id: task for task in self.tasks}

    def __len__(self):
        return len(self.tasks)

    def __contains__(self, task):
        return task.name in [t.name for t in self.tasks]

    def n_replicas(self, task):
        replicas = [t for t in self.tasks if t.name == task.name]
        replicas = [r for r in replicas if r.parameters == task.parameters]
        return len(replicas)

    def export_tasks(self):
        return {}
