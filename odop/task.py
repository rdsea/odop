# Implements the odop task decorators. These are used
# to mark tasks in written as Python functions
# Replaces task_manager.py

"""
Implements the odop task decorators. These are used
to mark tasks in written as Python functions
Replaces task_manager.py

Each decorator modifies the task specification dictionary
and saves the changes into the task list.

Since decorator run order is "reversed", we need to check
in each decorator it the task has been constructed yet.

Once the tasks
are read, they need to be processed to serialize the 
function. 
"""


import inspect
import importlib.util
import json
import cloudpickle
import uuid

tasks = []


def task(name=None, **kwargs):
    """ Marks a function as an ODOP task. The task
    name must be provided as a parameter. Other
    parameters can be provided with different
    decorators.
    
    Parameters:
    name: str
        The name of the task

    Returns:
    dict
        A dictionary of task parameters and
        the task function
    """
    print("task decorator")
    if name is None:
        name = str(uuid.uuid4())

    def decorator(func):
        """ Set task parameters and return the task """
        print(f"found task function {func.__name__}")

        task = {
            "name": name,
            "func": func
        }

        for key, val in kwargs.items():
            task[key] = val

        tasks.append(task)

        return task

    return decorator
    

def time(time):
    """ Set the time required to complete the task """
    print("time decorator")
    assert time is not None
    
    def decorator(task):
        print(task)
        return task
    
    return decorator



