"""
The odop task decorators are used to mark tasks in written as
Python functions. Each decorator modifies the task specification
and saves the changes into the task list.

Once the tasks are read, they need to be processed to serialize
the function.
"""

import pandas as pd
import uuid

tasks = []


class Task:
    def __init__(self, func):
        self.func = func
        self.name = None
        self.time_limit = None
        self.is_task = True

    def to_dict(self):
        task_dict = {
            key: val for key, val in self.__dict__.items() if key != "func"
        }
        return task_dict


def task(name=None, **kwargs):
    """ Marks a function as an ODOP task and sets the name parameter.
    This is the primary decorator used to mark odop tasks. While other
    decorators actually do construct a task object, this adds it to
    the list of found tasks. It must be the last decorator to run,
    meaning it must be first in the users code.

    Parameters:

    name: str, optional
        The name of the task
        By default, a random string ID is used

    Returns:

    dict
        A task object
    """
    if name is None:
        name = str(uuid.uuid4())

    def decorator(task):
        """ Set task parameters and return the task """
        if type(task) is not Task:
            task = Task(task)

        task.name = name

        for key, val in kwargs.items():
            task[key] = val

        tasks.append(task)

        return task

    return decorator


def time_limit(time_limit):
    """ Set the maximum time required to complete the task.

    Parameters:

    time_limit: str or pandas.Timedelta
        The maximum time allowed to complete the task.
        Must be either pandas.Timedelta or a string that
        can be converted to a pandas.Timedelta.

    Returns:

    dict
        A task object
    """
    assert time_limit is not None

    def decorator(task):
        if type(task) is not Task:
            task = Task(task)
        task.time_limit = pd.to_timedelta(time_limit)
        return task

    return decorator


def memory_limit(memory_limit):
    """ Set the memory required to complete the task.

    Parameters:

    memory_limit: integer or str
        The maximum memory allowed to complete the task.
        Must be either an integer or a string formatted as
        a number followed by a unit. Supported units are
        'M' and 'G' for megabytes and gigabytes respectively.

    Returns:

    dict
        A task object
    """
    assert memory_limit is not None

    def decorator(task):
        if type(task) is not Task:
            task = Task(task)
        task.memory_limit = memory_limit
        return task

    return decorator
