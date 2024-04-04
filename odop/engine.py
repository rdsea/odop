import json
import cloudpickle
import multiprocessing

running_tasks = []


def _load_and_run_pickled_task(task_file):
    """ Actually loads and runs the task from a pickled file.
    This should be called in the task process, and not directly
    by the engine.
    """
    with open(task_file, "rb") as file:
        task = cloudpickle.load(file)
    return task()


def engine_run_task_from_serialized(task_file):
    """ Run a task from a serialized file.

    Parameters:

    task_file: str
        Path to the file containing the task information
    """
    process = multiprocessing.Process(
        target=_load_and_run_pickled_task, args=(task_file,)
    ).start()
    return process


def engine_run_task_from_script(task_file):
    """ Run a task described in a json file.

    Assumes the task is a Python script. Other executables will be
    supported.

    Parameters:

    task_file: str
        Path to the file containing the task information
    """
    import subprocess

    with open(task_file, "r") as file:
        task_info = json.load(file)
    executable = task_info["executable"]
    process = subprocess.run(["python", executable])
    return process


def run(task_file):
    """ Run a task from a file. The task can be serialized as a pickle
    file or described in a json file.

    Parameters:

    task_file: str
        Path to the file containing the task information
    """
   
    if task_file.endswith(".pickle"):
        process = engine_run_task_from_serialized(task_file)
    elif task_file.endswith(".json"):
        process = engine_run_task_from_script(task_file)
    else:
        raise ValueError("Unsupported file type")

    running_tasks.append(process)
