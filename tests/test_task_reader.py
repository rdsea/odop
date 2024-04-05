""" Tests for the task_manager module. """

import os
import time
import pytest
import odop

module_dir = os.path.dirname(os.path.abspath(odop.__file__))
examples_dir = os.path.join(module_dir, 'example_tasks')


def test_task():
    @odop.task.task(name="test_name")
    def test_task():
        return "success"

    assert type(test_task) == odop.task.Task

    assert test_task.name == "test_name"
    assert test_task.func() == "success"
    assert test_task.time_limit is None


