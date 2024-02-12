# An implementation of the task reader with using a decorator. 

import functools
import inspect
import importlib.util

tasks = []


def odop_task(**kwargs):
    """ The odop task decorator. Records each task in an imported
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
        """ Set task parameters and return the task """
        print(f"found task function {func.__name__}")
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """ Calls the function and prints the function name before and
            after the call
            """
            print(f"Running task {func}")
            return_value = func(*args, **kwargs)
            print(f"Completed task {func}")
            return return_value

        # Check required parameters
        if "name" not in kwargs:
            raise ValueError(f"No name provided for task {func.__name__}. Task name is required")
        wrapper.name = kwargs["name"]

        for arg in ["time", "cpu", "memory"]:
            if arg not in kwargs:
                raise ValueError(f"No {arg} provided for {wrapper.name}. Task {arg} is required.")

        # Copy the parameters into the task function object
        for arg in kwargs:
            wrapper.__setattr__(arg, kwargs[arg])

        wrapper.is_task = True
        return wrapper

    return decorator


def read(module_name):
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
        if inspect.isfunction(obj) and getattr(obj, 'is_task', False):
            tasks.append(obj)


if __name__ == '__main__':
    # For a quick test, find the tasks in the example_task_with_decorator.py
    read("example_tasks/example_task_with_decorator")

    print([task.task_params for task in tasks])
