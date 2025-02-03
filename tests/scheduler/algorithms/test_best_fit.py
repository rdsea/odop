import os

import pytest
import yaml

from odop.scheduler.algorithms import best_fit
from odop.scheduler.scheduler_task import SchedulerTask

from .test_algorithm import DummyTask


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
        os.path.dirname(__file__), "test_cases", "best_fit_output.yaml"
    )
    with open(in_file) as f:
        test_cases = yaml.safe_load(f)
    yield test_cases


class TestBestFit:
    def test_next_task(self, inputs, outputs):
        algorithm = best_fit.BestFit()
        for key in inputs:
            queue = inputs[key]["task_queue"]
            resource = inputs[key]["available_resource"]
            output = outputs[key]
            assignment = algorithm.next_tasks(queue, resource)

            for key in list(output.keys()):
                del output[key]["actual_cpu_count"]
                if output[key] == {}:
                    del output[key]
            assert assignment == output

    def test_get_sorted_task_id_list(self, inputs, outputs):
        algorithm = best_fit.BestFit()
        for key in inputs:
            queue = inputs[key]["task_queue"]
            sorted_task_ids = algorithm.get_sorted_task_id_list(queue)
            result = [queue[t].cpus for t in sorted_task_ids]
            output = outputs[key]
            correct = sorted(queue, key=lambda x: -output[x]["actual_cpu_count"])
            correct = [queue[t].cpus for t in correct]
            assert result == correct
