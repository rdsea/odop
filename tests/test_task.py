import os
import tempfile

import pytest

import odop

module_dir = os.path.dirname(os.path.abspath(__file__))
examples_dir = os.path.join(module_dir, "..", "examples", "example_tasks")


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """Fixture that resets the tasks before and after each test."""
    odop.task.tasks = {}
    yield


def test_task():
    n_tasks = len(odop.task.tasks)

    @odop.task(name="test_task_1")
    def test_task():
        return 1

    assert test_task.name == "test_task_1"

    assert len(odop.task.tasks) == n_tasks + 1
    assert odop.task.tasks["test_task_1"] == test_task
    assert test_task.func() == 1
    assert hasattr(test_task, "time")


def test_background():
    n_tasks = len(odop.task.tasks)

    @odop.task(name="test_task_1")
    def test_task():
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1


def test_file_in():
    n_tasks = len(odop.task.tasks)

    @odop.task(name="test_task_1", trigger=odop.FileIn("."))
    def test_task(filename):
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.folders == ["."]
    assert test_task.batch_size == 1


def test_file_updated():
    n_tasks = len(odop.task.tasks)

    @odop.task(name="test_task_1", trigger=odop.FileUpdated("test_file"))
    def test_task(filename):
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.watch_file == "test_file"


def test_timer():
    n_tasks = len(odop.task.tasks)

    @odop.task(name="test_task_1", trigger=odop.Timer("1s"))
    def test_task():
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.interval == 1


def test_for_file_in_folder():
    n_tasks = len(odop.task.tasks)

    @odop.task.for_file_in_folder(name="test_task_1", folder_path=".")
    def test_task(filename):
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.folders == ["."]
    assert test_task.batch_size == 1


def test_file_updates():
    n_tasks = len(odop.task.tasks)

    @odop.task.file_updates(name="test_task_1", filename="test_file")
    def test_task(filename):
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.watch_file == "test_file"


def test_periodic():
    n_tasks = len(odop.task.tasks)

    @odop.task.periodic(name="test_task_1", interval="1s")
    def test_task():
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.interval == 1


def test_run_once():
    n_tasks = len(odop.task.tasks)

    @odop.task.run_once(name="test_task_1")
    def test_task():
        return 1

    assert test_task.name == "test_task_1"
    assert len(odop.task.tasks) == n_tasks + 1
    assert test_task.max_runs == 1


def test_time_and_memory():
    @odop.task(name="test_task_2", time="2h", memory="2G")
    def test_task():
        return 1

    assert test_task.name == "test_task_2"
    assert test_task.time == 2 * 3600
    assert test_task.memory == 2 * 1024


def test_task_list():
    @odop.task(name="task_1")
    def task_1():
        print("task_1")

    @odop.task(name="task_2")
    def task_2():
        print("task_2")

    @odop.task(name="task_3")
    def task_3():
        print("task_3")

    assert task_1.name == "task_1"
    assert task_2.name == "task_2"
    assert task_3.name == "task_3"

    assert odop.task.tasks["task_1"].name == "task_1"
    assert odop.task.tasks["task_2"].name == "task_2"
    assert odop.task.tasks["task_3"].name == "task_3"


def test_import_module():
    tasks = len(odop.task.tasks)
    path = os.path.join(examples_dir, "example_task_with_decorator_1.py")
    odop.task.read_module(path)

    assert len(odop.task.tasks) == tasks + 1
    assert odop.task.tasks["example_task_2"].name == "example_task_2"


def test_write_all():
    @odop.task(name="test_task_3")
    def test_task():
        return "test_task_3"

    with tempfile.TemporaryDirectory() as task_folder:
        with tempfile.TemporaryDirectory() as executables_folder:
            odop.task.write_all(task_folder, executables_folder)
            assert os.path.exists(os.path.join(task_folder, "test_task_3.json"))
            assert os.path.exists(
                os.path.join(executables_folder, "test_task_3.pickle")
            )


def test_tasks_same_name():
    with pytest.raises(ValueError):

        @odop.task(name="test_task_1")
        def test_task():
            return 1

        @odop.task(name="test_task_1")
        def also_test_task():
            return 1
