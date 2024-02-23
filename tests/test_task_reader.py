""" Tests for the task_manager module. """

import os
import time
import pytest
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

# Try creating a task without a required parameter
def test_task_manager_missing_parameter():
    """ Test that a task without a required parameter raises a ValueError """
    with pytest.raises(ValueError):
        @odop.task_manager.odop_task(time="2h", cpu="2", memory="2G")
        def test_task_function():
            time.sleep(1)

    with pytest.raises(ValueError):
        @odop.task_manager.odop_task(name="test_task", cpu="2", memory="2G")
        def test_task_function():
            time.sleep(1)
    
    with pytest.raises(ValueError):
        @odop.task_manager.odop_task(name="test_task", time="2h", memory="2G")
        def test_task_function():
            time.sleep(1)
    
    with pytest.raises(ValueError):
        @odop.task_manager.odop_task(name="test_task", time="2h", cpu="2")
        def test_task_function():
            time.sleep(1)


def test_task_manager_decorator():
    """ Test the decorator directly """

    @odop.task_manager.odop_task(
        name="test_task", time="2h", cpu="2", memory="2G",
        other_parameter="other_value"
    )
    def test_task_function():
        """ docstring """
        return 1

    assert test_task_function.name == "test_task"
    assert test_task_function.time == "2h"
    assert test_task_function.cpu == "2"
    assert test_task_function.memory == "2G"
    assert test_task_function.is_task == True
    assert test_task_function.__name__ == "test_task_function"
    assert test_task_function.other_parameter == "other_value"
    assert test_task_function.__doc__ == " docstring "

    # Check that the function is called
    assert test_task_function() == 1


def test_run_from_script():
    """ Test running a task from a script """

    file_path = os.path.join(examples_dir, "example_task_with_decorator")
    odop.task_manager.read(file_path)

    assert odop.task_manager.tasks[0].name == "example_task"

    # Write the task script (this is currently called when the task is read),
    # but we call it again to allow changing that
    odop.task_manager.create_runner_script(odop.task_manager.tasks[0])

    # Run the task
    os.system(f"python {odop.task_manager.tasks[0].name}.py")


def test_run_from_serialized():
    """ Test running a task from a serialized file """

    file_path = os.path.join(examples_dir, "example_task_with_decorator")
    odop.task_manager.read(file_path)

    assert odop.task_manager.tasks[0].name == "example_task"

    # Serialize the task
    odop.task_manager.create_runner_serialized(odop.task_manager.tasks[0])

    # Run the task
    odop.task_manager.engine_run_task_from_serialized(odop.task_manager.tasks[0].name)
