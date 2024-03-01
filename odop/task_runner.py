import json
import cloudpickle

def engine_run_task_from_serialized(task_name):
    """ Run a task from a serialized file. This is a function that the engine would use
    to run a task on a node.

    Example 1: Running the function from a serialized file

    This should be ran and monitored by the engine.
    """
    with open(f"{task_name}.pickle", "rb") as file:
        task = cloudpickle.load(file)
    task()


def engine_run_task_from_script(task_name):
    """ Run a task from a script. This is a function that the engine would use
    to run a task on a node.

    Example 2: Running the function from a script

    Capture the process for monitoring and killing if time runs out.
    """
    import subprocess
    process = subprocess.run(["python", f"{task_name}_runner.py"])
