import os
import pathlib

import click
import requests

import odop
from odop.common import ODOP_RUNS_PATH, get_runs
from odop.ui import Status


def get_status(run_name):
    run_folder = os.path.join(ODOP_RUNS_PATH, run_name)
    status_file = os.path.join(run_folder, "status")
    status = Status(status_file)
    return status


@click.group()
@click.version_option()
def odop_cli():
    """CLI group for ODOP commands."""
    pass


@odop_cli.command()
@click.argument("run_name", nargs=1)
@click.argument(
    "task_folder",
    required=False,
    default=".",
    type=click.Path(exists=True, file_okay=False),
)
def scan_tasks_folder(run_name, task_folder):
    """Loads tasks from the task folder path and all subpaths."""
    print("Task folder:", task_folder)

    run_folder = os.path.join(ODOP_RUNS_PATH, run_name)
    executables_folder = os.path.join(run_folder, "executables")
    task_parameters_folder = os.path.join(run_folder, "task_parameters")

    odop.scan_tasks_folder(task_folder, task_parameters_folder, executables_folder)


@odop_cli.command()
@click.argument("run_name", type=str)
@click.argument("task_name", type=str)
def remove_task(run_name, task_name):
    """Removes a task from a run"""
    status = get_status(run_name)
    task_parameters_folder = status["task_parameters_folder"]
    task_file = os.path.join(task_parameters_folder, f"{task_name}.json")
    if os.path.exists(task_file):
        os.remove(task_file)
        print(f"Task {task_name} removed from run {run_name}")
    else:
        print(f"Task {task_name} not found in run {run_name}")


@odop_cli.command()
def list_runs():
    """List all known runs and their statuts"""
    runs: list[pathlib.Path] = get_runs()

    run_name_len = 0
    for run in runs:
        if len(run.name) <= run_name_len:
            continue
        run_name_len = len(run.name)
    run_name_len = min(run_name_len, 20)

    print(f"{'': <2}\t{'RUN NAME': <{run_name_len}}\t{'STATUS': <8}")
    for idx, run in enumerate(runs):
        run_name = run.name
        status: Status = get_status(run_name)

        print(f"{idx: <2}\t{run_name: <{run_name_len}}\t{status['runtime_status']: <8}")


@odop_cli.command()
@click.argument("run_name", type=str)
def list_tasks(run_name):
    """List task names in given run"""
    status = get_status(run_name)
    task_parameters_folder = status["task_parameters_folder"]
    task_files = os.listdir(task_parameters_folder)
    print(f"Tasks in run {run_name}:")
    for task_file in task_files:
        print(task_file.replace(".json", ""))


@odop_cli.command()
@click.argument("run_name", type=str)
def visualize_folder(run_name):
    """Visualize cpu utilization of all core"""
    from .visualization.visualize_all_folder import process_folder

    run_folder = os.path.join(ODOP_RUNS_PATH, run_name)
    data_folder = os.path.join(run_folder, "metric_database")

    process_folder(data_folder)


def request_api(run_name, endpoint):
    try:
        status = get_status(run_name)
        api_address = status["api_address"]
        result = requests.get(f"{api_address}/{endpoint}").json()
        return result

    except Exception as e:
        print(e)
        print("Could not connect to the API")
        return {}


@odop_cli.command()
@click.argument("run_name", type=str)
def queue_summary(run_name):
    """Return a summary of the task queue for a given run."""
    summaries = request_api(run_name, "")
    print("Task status summary:")
    for status in summaries:
        print(f"{status}: {summaries[status]}")


@odop_cli.command()
@click.argument("run_name", type=str)
def queue_status(run_name):
    """Return the status of tasks in a given run."""
    status = request_api(run_name, "status")
    print("Tasks:")
    for task in status:
        print(f"{task['name']} {task['task_id']}:")
        for key in task:
            print(f"   {key}: {task[key]}")
        print()


@odop_cli.command()
@click.argument("run_name", type=str)
@click.argument("task_id", type=int)
def queue_detail(run_name, task_id):
    """Return a summary of a task in the queue for a given run."""
    task_info = request_api(run_name, f"status/{task_id}")
    print("Task info:", task_info)


@odop_cli.command()
@click.argument(
    "task_folder",
    required=False,
    default=".",
    type=click.Path(exists=True, file_okay=False),
)
def check_tasks(task_folder):
    """Loads tasks from the task folder path and all subpaths."""
    print("Task folder:", task_folder)

    odop.scan_tasks_folder(task_folder, write=False)


if __name__ == "__main__":
    odop_cli()
