"""
The odop task decorators are used to mark tasks in written as
Python functions. Each decorator modifies the task specification
and saves the changes into the task list.

Once the tasks are read, they need to be processed to serialize
the function.
"""

import pandas as pd
import uuid
import warnings

tasks = []


class Task:
    def __init__(self, func):
        self.func = func
        self.name = None
        self.time_limit = None

    def to_dict(self):
        task_dict = {
            key: val for key, val in self.__dict__.items() if key != "func"
        }
        return task_dict


def register_task(task):
    """ Register a task for the scheduler.

    Currently just adds it to the list.
    """
    tasks.append(task)


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

        register_task(task)

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


def for_files_in_folder(folder_path, task_name=None):

    def decorator(task):
        if type(task) is not Task:
            task = Task(task)
        if folder_path is not None:
            task.input_folder = folder_path
        if task_name is not None:
            task.name = task_name
        task.single_file_task

        # Check that the function takes a single parameter.
        # Warn if it is not called "filename"
        assert len(task.func.__code__.co_varnames) == 1
        if task.func.__code__.co_varnames[0] != "filename":
            warnings.warn(
                "Parameter name for a for_files_in_folder task is not 'filename'. The name of a file is still provided as the parameter."
            )

        return task
    
    
    return decorator
