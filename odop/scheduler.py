# An implementation of the task reader with using a decorator.

import os
import functools
import importlib.util
import inspect
import json

import cloudpickle
from odop.task import Task

tasks = []


<<<<<<< HEAD:odop/task_manager.py
def odop_task(**kwargs):
    """The odop task decorator. Records each task in an imported
=======
def _odop_task(**kwargs):
    """ The odop task decorator. Records each task in an imported
>>>>>>> main:odop/scheduler.py
    python file.

    Only accepts keyword arguments. Name, time, cpu, and memory are
    required. Other arguments can be provided, keeping in mind that
    the scheduler must be aware of them.

    Parameters:
    name: str
        The name of the task
    time: str
        The time required to complete the task
    cpu: str
        The number of CPUs required to complete the task
    memory: str
        The amount of memory required to complete the task

    Returns:
    function
        The task function with the parameters set
    """

    def decorator(func):
        """Set task parameters and return the task"""
        print(f"found task function {func.__name__}")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
<<<<<<< HEAD:odop/task_manager.py
            """Calls the function and prints the function name before and
            after the call
            """
            print(f"Running {func}")
            return_value = func(*args, **kwargs)
            print(f"Completed {func}")
            return return_value
=======
            """ Thin wrapper we can assign attributes to """
            return func(*args, **kwargs)
>>>>>>> main:odop/scheduler.py

        # Check required parameters
        if "name" not in kwargs:
            raise ValueError(
                f"No name provided for task {func.__name__}. Task name is required"
            )
        wrapper.name = kwargs["name"]

        for arg in ["time", "cpu", "memory"]:
            if arg not in kwargs:
                raise ValueError(
                    f"No {arg} provided for {wrapper.name}. Task {arg} is required."
                )

        # Copy the parameters into the task object
        for arg in kwargs:
            wrapper.__setattr__(arg, kwargs[arg])

        # The arguments variable contains keyword arguments provided to
        # the task function. Check that a value is provided for each
        # parameter.
        signature = inspect.signature(func)
        parameters = list(signature.parameters.keys())
        for parameter in parameters:
            if not parameter in wrapper.arguments:
                raise ValueError(f"Parameter {parameter} not provided for task {wrapper.name}")

        # Check for the inteyrupt_allowed parameter and default to True
        if not "interrupt_allowed" in kwargs:
            wrapper.interrupt_allowed = True

        # Set other parameters not provided by the user
        wrapper.is_task = True
        wrapper.module_file = inspect.getfile(func)
        wrapper.function_name = func.__name__

<<<<<<< HEAD:odop/task_manager.py
        # Extract parameter names from the function signature
        signature = inspect.signature(func)
        parameters = list(signature.parameters.keys())
        wrapper.task_params = {}
        for parameter in parameters:
            if parameter in kwargs:
                wrapper.task_params[parameter] = kwargs[parameter]
            else:
                raise ValueError(
                    f"Parameter {parameter} not provided for task {wrapper.name}"
                )

=======
>>>>>>> main:odop/scheduler.py
        return wrapper

    return decorator


def create_runner_serialized(task):
<<<<<<< HEAD:odop/task_manager.py
    """Create a runer for the task. This is saved to disk, so that the engine can
    run the task on any node.
=======
    """ Create a runner for the task. This is saved to disk, so that
    the engine can run the task on any node.
>>>>>>> main:odop/scheduler.py

    The task function and other parameters are serialized saved into a
    .pickle file.


    Parameters:

    task: An odop.task.Task object

    returns:

    filename: str
        Path to the file containing the serialized task information
    """

    # Define a function to run the task with parameters
    def run_task():
        task(**task.arguments)

    # Save the serialized function to a file
    file_name = f"{task.name}.pickle"
    with open(file_name, "wb") as file:
        cloudpickle.dump(run_task, file)

    return file_name


def create_runner_script(task):
<<<<<<< HEAD:odop/task_manager.py
    """Create a runner for the task. This is saved to disk, so that the engine can
    run the task on any node.
=======
    """ Create a runner for the task. This is saved to disk, so that the
    engine can run the task on any node.
>>>>>>> main:odop/scheduler.py

    The module containing the task function is copied to the output folder
    and a script is generated to import and run the function. The parameters,
    including the module file name and function name are written to a json file.

<<<<<<< HEAD:odop/task_manager.py
    We need to import everything the task function needs to run. The easiest way
    to do this is to make a copy of the module, import the task function from
    the module and run.

    Any parameters for the function itself are written into a json file. Later,
    this could be written by the engine before starting the task.
=======

    Parameters:

    task: An odop.task.Task object

    returns:

    filename: str
        Path to the file containing the runner script
>>>>>>> main:odop/scheduler.py
    """

    file_name = f"{task.name}_runner.py"
    module_file_name = f"{task.name}_module.py"
    params_file = f"{task.name}_arguments.json"

    # Copy the module
    with open(task.module_file, "r") as file:
        with open(module_file_name, "w") as new_file:
            new_file.write(file.read())

    # Write the script
    with open(file_name, "w") as file:
        # Write the imports to the file
        file.write(
            f"from {module_file_name.replace('.py', '')} import {task.function_name}\n"
        )
        file.write(f"import json\n")

        # Write the function to the file
        file.write(f"def run_task():\n")
        file.write(f"    task = {task.function_name}\n")
        file.write(f"    arguments = json.load(open('{params_file}'))\n")
        file.write(f"    task(**arguments)\n")
        file.write(f"\n")
        file.write(f"print(f'Running {task.name}')\n")
        file.write(f"run_task()\n")
        file.write(f"print(f'Completed {task.name}')\n")

    # Write the parameters to a file
    with open(params_file, "w") as file:
        json.dump(task.arguments, file)
    return file_name


def read_module(module_name):
    """ Find odop tasks in a Python module. Tasks are saved to an output
    folder with the information necessary to run them.

    Parameters:

    module_name: str
        A Python module containing odop tasks
    """

    # If file name is provided, figure out the module name
    if module_name.endswith(".py"):
        module_file = module_name
        module_name = module_file.replace(".py", "")
    else:
        module_file = f"{module_name}.py"

    # import the module
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, obj in inspect.getmembers(module):
<<<<<<< HEAD:odop/task_manager.py
        if inspect.isfunction(obj) and getattr(obj, "is_task", False):
=======
        if type(obj) == Task:
>>>>>>> main:odop/scheduler.py
            tasks.append(obj)
            create_runner_serialized(obj)


def read_folder(folder):
    """ Find odop tasks in all Python modules in a folder. Tasks are saved
    to an output folder with the information necessary to run them.

    Parameters:

    folder: str
        A folder containing Python modules with odop tasks
    """

    files = os.listdir(folder)
    for file in files:
        if file.endswith(".py"):
            read_module(file)


if __name__ == "__main__":
    # For a quick test, find the tasks in the example_task_with_decorator.py
<<<<<<< HEAD:odop/task_manager.py
    path = __file__.replace(
        "task_manager.py", "example_tasks/example_task_with_decorator.py"
    )
    read(path)
=======
    path = __file__.replace("scheduler.py", "example_tasks/example_task_with_decorator.py")
    read_module(path)
>>>>>>> main:odop/scheduler.py

    print([task.name for task in tasks])
