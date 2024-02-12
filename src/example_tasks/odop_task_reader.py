# An implementation of the task reader with using a decorator. 

import time
import functools
import inspect
import importlib.util

tasks = []


def odop_task(**kwargs):
    """ The odop task decorator. Records each task in an imported
    python file. 
    """

    def decorator(func):
        """ Set task parameters and return the task """
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """ Calls the function and prints the function name before and
            after the call
            """
            print(f"Running task {func}")
            func(args, **kwargs)
            print(f"Completed task {func}")

        wrapper.is_task = True
        wrapper.task_params = kwargs
        if "name" in wrapper.task_params:
            wrapper.name = wrapper.task_params["name"]
        else:
            wrapper.name = func.__name__
        print(f"found task function {wrapper.name}")
        return wrapper

    return decorator


def find_tasks(module_name):
    # If file name is provided, figure out the module name
    if module_name.endswith(".py"):
        module_file = module_name
        module_name = module_file.replace(".py", "")
    else:
        module_file = f"{module_name}.py"

    #import the module
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and getattr(obj, 'is_task', False):
            tasks.append(obj)


if __name__ == '__main__':
    # For a quick test, find the tasks in the example_task_with_decorator.py
    find_tasks("example_task_with_decorator")

    print([task.task_params for task in tasks])
