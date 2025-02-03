import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

import odop
from odop.engine.engine import Engine, EngineTask, StatusCode, TaskManager

module_dir = os.path.dirname(os.path.abspath(odop.__file__))
examples_dir = os.path.join(module_dir, "example_tasks")


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """Fixture that resets the tasks before and after each test."""
    odop.task.tasks = {}
    yield


test_executable = """#!/usr/bin/env python

import time
time.sleep(0.2)
print(1)
"""


@pytest.fixture()
def executables_folder():
    with tempfile.TemporaryDirectory() as executables_folder:
        yield executables_folder


@pytest.fixture()
def over_time_task(executables_folder):
    @odop.task(name="over_time_task")
    def test_task():
        import time

        time.sleep(10)
        return 1

    with tempfile.TemporaryDirectory() as task_folder:
        odop.task.write_all(task_folder, executables_folder)

    task = EngineTask(
        id=0,
        name="over_time_task",
        execution_type="python_task",
        time=0.0000001,
        memory=1,
        cpus=1,
        ranks=1,
        nodes=1,
        disk_limit=1,
        priority=0,
    )
    yield executables_folder, task


@pytest.fixture()
def script_task(executables_folder):
    with open(os.path.join(executables_folder, "task.py"), "w") as file:
        file.write(test_executable)
    os.chmod(os.path.join(executables_folder, "task.py"), 0o555)

    task = EngineTask(
        id=0,
        name="task",
        execution_type="executable",
        executable="task.py",
        time=10,
        memory=1,
        cpus=1,
        ranks=1,
        nodes=1,
        disk_limit=1,
        priority=0,
    )
    yield executables_folder, task


@pytest.fixture()
def python_task(executables_folder):
    @odop.task(name="test_task_2")
    def test_task():
        return 1

    with tempfile.TemporaryDirectory() as task_folder:
        odop.task.write_all(task_folder, executables_folder)

    task = EngineTask(
        id=0,
        name="test_task_2",
        execution_type="python_task",
        time=10,
        memory=1,
        cpus=1,
        ranks=1,
        nodes=1,
        disk_limit=1,
        priority=0,
    )
    yield executables_folder, task


@pytest.fixture()
def failing_task(executables_folder):
    @odop.task(name="failing_task")
    def test_task():
        raise ValueError("Test error")

    with tempfile.TemporaryDirectory() as task_folder:
        odop.task.write_all(task_folder, executables_folder)

    task = EngineTask(
        id=0,
        name="failing_task",
        execution_type="python_task",
        time=10,
        memory=1,
        cpus=1,
        ranks=1,
        nodes=1,
        disk_limit=1,
        priority=0,
    )
    yield executables_folder, task


def test_run_pickled(script_task):
    executables_folder, task = script_task
    task = TaskManager(task, executables_folder)

    assert task.status == StatusCode.NOT_STARTED

    my_hostname = os.uname().nodename
    task.run({my_hostname: {"cpus": [0], "ranks": 1}})
    time.sleep(0.05)
    assert task.status == StatusCode.RUNNING

    task.wait()
    assert task.start_time is not None
    assert task.returncode == 0
    assert task.status == StatusCode.COMPLETED


def test_run_from_script(python_task):
    executables_folder, task = python_task
    task = TaskManager(task, executables_folder)

    assert task.status == StatusCode.NOT_STARTED

    my_hostname = os.uname().nodename
    task.run({my_hostname: {"cpus": [0], "ranks": 1}})
    task.wait()
    assert task.returncode == 0
    assert task.start_time is not None
    assert task.status == StatusCode.COMPLETED


def test_task_function_failure(failing_task):
    executables_folder, task = failing_task
    task = TaskManager(task, executables_folder)

    my_hostname = os.uname().nodename
    task.run({my_hostname: {"cpus": [0], "ranks": 1}})
    task.wait()
    assert task.returncode == 1
    assert "Test error" in task.stderr
    assert task.status == StatusCode.FAILED


def test_overtime(over_time_task):
    executables_folder, task = over_time_task
    task = TaskManager(task, executables_folder)

    my_hostname = os.uname().nodename
    task.run({my_hostname: {"cpus": [0], "ranks": 1}})
    while task.status in [StatusCode.NOT_STARTED, StatusCode.RUNNING]:
        time.sleep(0.05)
        task.update_status()
    assert task.status == StatusCode.KILLED
    assert task.status_reason == "time limit"


def test_stop(script_task):
    executables_folder, task = script_task
    task = TaskManager(task, executables_folder)

    my_hostname = os.uname().nodename
    task.run({my_hostname: {"cpus": [0], "ranks": 1}})
    time.sleep(0.05)
    assert task.status == StatusCode.RUNNING

    task.stop("test")
    assert task.status == StatusCode.STOPPED
    assert task.status_reason == "test"

    task.restart()
    assert task.status == StatusCode.RUNNING
    assert task.status_reason is None

    task.wait()
    assert task.status == StatusCode.COMPLETED


def test_kill(script_task):
    executables_folder, task = script_task
    task = TaskManager(task, executables_folder)

    my_hostname = os.uname().nodename
    task.run({my_hostname: {"cpus": [0], "ranks": 1}})
    while task.status != StatusCode.RUNNING:
        time.sleep(0.05)
    task.kill("test")
    task.wait()
    assert task.status == StatusCode.KILLED
    assert task.status_reason == "test"


def test_engine_run(script_task, python_task, failing_task):
    executables_folder, task1 = script_task
    _, task2 = python_task
    _, task3 = failing_task

    engine = Engine(executables_folder)

    assert task1.status == StatusCode.NOT_STARTED
    assert task2.status == StatusCode.NOT_STARTED
    assert task3.status == StatusCode.NOT_STARTED

    my_hostname = os.uname().nodename
    engine.run(task1.__dict__, {my_hostname: {"cpus": [0], "ranks": 1}})
    engine.run(task2.__dict__, {my_hostname: {"cpus": [0], "ranks": 1}})
    engine.run(task3.__dict__, {my_hostname: {"cpus": [0], "ranks": 1}})

    for task in engine.tasks:
        task.wait()

    assert engine.tasks[0].status == StatusCode.COMPLETED
    assert engine.tasks[1].status == StatusCode.COMPLETED
    assert engine.tasks[2].status == StatusCode.FAILED


def test_task_manager_format_mpi_command_slurm(executables_folder, python_task):
    # mock environment to add "SLURM_JOB_ID"
    os.environ["SLURM_JOB_ID"] = "1234"
    _, task = python_task
    task_manager = TaskManager(task, executables_folder)
    task_manager.nodes = 2
    base_command = "command"
    placement = {
        "node1": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
        "node2": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
    }
    command = task_manager.format_mpi_command(base_command, placement)
    assert (
        command
        == "srun --overlap  --nice=20 -N 2 --mem=0 --ntasks-per-node=2 --cpus-per-task=3 --nodelist node1,node2 command"
    )
    os.environ.pop("SLURM_JOB_ID")


def test_task_manager_format_mpi_command(executables_folder, python_task):
    _, task = python_task
    task_manager = TaskManager(task, executables_folder)
    task_manager.nodes = 2
    base_command = "command"
    placement = {
        "node1": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
        "node2": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
    }
    command = task_manager.format_mpi_command(base_command, placement)
    assert (
        command
        == f"mpirun -n 4 --hostfile {executables_folder}/hostfiles/test_task_2_0.hostfile command"
    )

    with open(f"{executables_folder}/hostfiles/test_task_2_0.hostfile") as file:
        content = file.read()
        assert content == "node1 slots=2\nnode2 slots=2\n"


def test_task_manager_command_mpi(executables_folder, python_task):
    # mock subprocess.Popen to get the command string instead of running it
    _, task = python_task
    task_manager = TaskManager(task, executables_folder)
    task_manager.nodes = 2
    base_command = ["command"]
    placement = {
        "node1": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
        "node2": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
    }

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        task_manager.run_command_on_nodes(base_command, placement)

        command_passed = mock_popen.call_args[0][0]

    assert (
        command_passed
        == f"mpirun -n 4 --hostfile {executables_folder}/hostfiles/test_task_2_0.hostfile command"
    )


def test_task_manager_command_mpi_2(executables_folder, python_task):
    # mock subprocess.Popen to get the command string instead of running it
    _, task = python_task
    task_manager = TaskManager(task, executables_folder)
    task_manager.nodes = 2
    base_command = ["command"]
    placement = {
        "node1": {
            "ranks": 2,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
        "node2": {
            "ranks": 1,
            "cpus": ["cpu0", "cpu1", "cpu3"],
        },
    }

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        task_manager.run_command_on_nodes(base_command, placement)

        command_passed = mock_popen.call_args[0][0]

    assert (
        command_passed
        == f"mpirun -n 3 --hostfile {executables_folder}/hostfiles/test_task_2_0.hostfile command"
    )

    with open(f"{executables_folder}/hostfiles/test_task_2_0.hostfile") as file:
        content = file.read()
        assert content == "node1 slots=2\nnode2 slots=1\n"


def test_task_manager_command_single_rank(executables_folder, python_task):
    # mock subprocess.Popen to get the command string instead of running it

    _, task = python_task
    task_manager = TaskManager(task, executables_folder)
    task_manager.nodes = 1
    base_command = ["command"]
    placement = {
        "node1": {
            "ranks": 1,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
    }

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        task_manager.run_command_on_nodes(base_command, placement)

        command_passed = mock_popen.call_args[0][0]

    working_dir = os.getcwd()
    assert command_passed == f"ssh node1 'cd {working_dir}; command'"


def test_task_manager_command_single_slurm(executables_folder, python_task):
    os.environ["SLURM_JOB_ID"] = "1234"

    _, task = python_task
    task_manager = TaskManager(task, executables_folder)
    task_manager.nodes = 1
    base_command = ["command"]
    placement = {
        "node1": {
            "ranks": 1,
            "cpus": ["cpu0", "cpu1", "cpu3", "cpu4", "cpu5", "cpu6"],
        },
    }

    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        task_manager.run_command_on_nodes(base_command, placement)

        command_passed = mock_popen.call_args[0][0]

    assert (
        command_passed
        == "srun --overlap  --nice=20 -N 1 --mem=0 --ntasks-per-node=1 --cpus-per-task=6 --nodelist node1 command"
    )
