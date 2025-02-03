from multiprocessing import Process

from odop.scheduler.scheduler_task import SchedulerTask
from odop.scheduler.task_queue import TaskQueue


class DummyTask:
    def __init__(self, priority=0):
        self.name = ""
        self.time = 1
        self.memory = 1
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


def test_init_queue():
    task1 = SchedulerTask(DummyTask(1))
    task2 = SchedulerTask(DummyTask(2))
    task3 = SchedulerTask(DummyTask(3))
    queue = TaskQueue()

    assert len(queue) == 0

    queue.push(task1)
    assert len(queue) == 1

    tasks = queue.get_all()
    assert len(queue) == 0
    assert tasks[0].priority == 1

    queue.push(task1)
    queue.push(task3)
    queue.push(task2)
    assert len(queue) == 3

    tasks = queue.get_all()
    assert len(queue) == 0
    assert tasks[2].priority == 3
    assert tasks[1].priority == 2
    assert tasks[0].priority == 1


def test_queue_multiprocess():
    queue = TaskQueue()

    def add_task_to_queue(queue):
        task1 = SchedulerTask(DummyTask(3))
        queue.push(task1)

    def read_from_queue(queue):
        tasks = queue.get_all()
        assert len(queue) == 0
        assert tasks[0].priority == 3

    p1 = Process(target=add_task_to_queue, args=(queue,))
    p1.start()
    p1.join()

    assert len(queue) == 1
    tasks = queue.get_all()
    assert len(queue) == 0
    assert tasks[0].priority == 3

    p1 = Process(target=add_task_to_queue, args=(queue,))
    p1.start()
    p1.join()
    p2 = Process(target=read_from_queue, args=(queue,))
    p2.start()
    p2.join()

    assert len(queue) == 0
