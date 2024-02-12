""" Tests for the task_manager module. """

import os
import odop

module_dir = os.path.dirname(os.path.abspath(odop.__file__))
examples_dir = os.path.join(module_dir, 'example_tasks')

def test_task_manager():
    """ Read the example task and check variables are defined """

    file_path = os.path.join(examples_dir, "example_task_with_decorator")
    odop.task_manager.read(file_path)

    assert odop.task_manager.tasks[0].name == "example_task"

    # Check the task parameters
    assert odop.task_manager.tasks[0].name == "example_task"
    assert odop.task_manager.tasks[0].time == "2h"
    assert odop.task_manager.tasks[0].cpu == "2"
    assert odop.task_manager.tasks[0].memory == "2G"
    assert odop.task_manager.tasks[0].is_task == True
