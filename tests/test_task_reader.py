""" Tests for the task_reader module. """

import os
from .. import task_reader

current_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(current_dir)
examples_dir = os.path.join(module_dir, 'example_tasks')

def test_task_reader():
    """ Read the example task and check variables are defined """

    file_path = os.path.join(examples_dir, "example_task_with_decorator")
    task_reader.read(file_path)

    assert task_reader.tasks[0].name == "example_task"
