import os

import pytest
import yaml

from odop.scheduler.algorithms import algorithm as algorithm_template
from odop.scheduler.scheduler_task import SchedulerTask


class DummyTask:
    def __init__(
        self,
        name="",
        priority=0,
        nodes="any",
        ranks_per_node="any",
        ranks="any",
        cpus_per_rank="any",
        cpus="any",
        **kwargs,
    ):
        self.name = name
        self.time = 1
        self.memory = 0
        self.nodes = nodes
        self.ranks_per_node = ranks_per_node
        self.ranks = ranks
        self.cpus_per_rank = cpus_per_rank
        self.cpus = cpus
        self.disk_limit = 0
        self.index = 0

        self.execution_type = ""
        self.priority = priority
        self.filename = None

        self.task_id = None
        self.status = ""


@pytest.fixture()
def inputs():
    """Create an example task queue."""
    in_file = os.path.join(
        os.path.dirname(__file__), "test_cases", "algorithm_input.yaml"
    )
    with open(in_file) as f:
        test_cases = yaml.safe_load(f)

    for case_name in test_cases:
        test_case = test_cases[case_name]
        task_queue = {}
        for task_name, task in test_case["queue"].items():
            scheduler_task = SchedulerTask(DummyTask(**task))
            scheduler_task.queued_timestamp = task["queued_timestamp"]
            task_queue[task_name] = scheduler_task
        test_cases[case_name]["task_queue"] = task_queue
    yield test_cases


@pytest.fixture()
def outputs():
    in_file = os.path.join(
        os.path.dirname(__file__), "test_cases", "priority_output.yaml"
    )
    with open(in_file) as f:
        test_cases = yaml.safe_load(f)
    yield test_cases


class TestPriority:
    def test_next_task(self, inputs, outputs):
        algorithm = algorithm_template.Algorithm()
        for key in inputs:
            queue = inputs[key]["task_queue"]
            resource = inputs[key]["available_resource"]
            output = outputs[key]
            assignment = algorithm.next_tasks(queue, resource)
            assert assignment == output

    def test_get_sorted_task_id_list(self, inputs):
        algorithm = algorithm_template.Algorithm()
        for key in inputs:
            queue = inputs[key]["task_queue"]
            sorted_task_ids = algorithm.get_sorted_task_id_list(queue)
            result = [queue[t].priority for t in sorted_task_ids]
            correct = sorted(queue, key=lambda x: -queue[x].priority)
            correct = [queue[t].priority for t in correct]
            assert result == correct
