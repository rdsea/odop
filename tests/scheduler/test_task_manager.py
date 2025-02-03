import os
import tempfile
import time

import pytest

import odop
import odop.scheduler.task_manager as tm
from odop.scheduler.task_queue import TaskQueue


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """Fixture that resets the tasks before and after each test."""
    odop.task.tasks = {}
    yield


@pytest.fixture()
def folders():
    with tempfile.TemporaryDirectory() as data_folder:
        with tempfile.TemporaryDirectory() as task_folder:
            with tempfile.TemporaryDirectory() as executables_folder:
                yield data_folder, task_folder, executables_folder


@pytest.fixture()
def folder_task(folders):
    data_folder, task_folder, executables_folder = folders

    @odop.task.for_file_in_folder(
        data_folder,
        name="test_task",
        batch_size=2,
        time="1m",
    )
    def test_task(filenames):
        return "test_task"

    odop.task.write_all(task_folder, executables_folder)

    filename = os.path.join(task_folder, "test_task.json")
    task = tm.TaskDescription(filename)

    return task


class TestTaskDescription:
    def test_task_description(self, folders, folder_task):
        data_folder, task_folder, executables_folder = folders
        assert folder_task.name == "test_task"
        assert folder_task.time == 60
        assert folder_task.memory > 0  # should have a default value
        assert folder_task.cpus == 1  # should have a default value
        assert folder_task.cpus_per_rank == "any"
        assert folder_task.ranks == "any"
        assert folder_task.ranks_per_node == "any"
        assert folder_task.nodes == "any"
        assert folder_task.execution_type == "python_task"
        assert folder_task.priority == 0
        assert folder_task.files == []
        assert folder_task.folders == [data_folder]
        assert folder_task.file_pattern == []
        assert folder_task.filter is None
        assert folder_task.batch_size == 2
        assert folder_task.disk_limit == 1
        assert folder_task.executable == ""
        assert folder_task.filename.endswith("test_task.json")

    def test_list_input_files(self, folders, folder_task):
        data_folder, task_folder, executables_folder = folders

        # Create 4 files in the data folder. Ensure the timestamps are different.
        for i in range(4):
            open(os.path.join(data_folder, f"file{i}"), "w").close()
            time.sleep(0.01)

        files = folder_task.list_input_files()
        assert len(files) == 4
        assert files[0].endswith("file0")

    def test_batch_files(self, folders):
        with tempfile.TemporaryDirectory() as folder:
            data_folder, task_folder, executables_folder = folders

            @odop.task.for_file_in_folder(folder, name="test_task", batch_size=3)
            def test_task(filenames):
                return "test_task"

            odop.task.write_all(task_folder, executables_folder)
            filename = os.path.join(task_folder, "test_task.json")
            task = tm.TaskDescription(filename)

            for i in range(7):
                open(os.path.join(folder, f"file{i}"), "w").close()

            batches = task.batch_files()
            assert len(batches) == 2
            assert len(batches[0]) == 3
            assert len(batches[1]) == 3


class TestTaskManager:
    queue = TaskQueue()

    def test_task_manager(self, folders, folder_task):
        data_folder, task_folder, executables_folder = folders

        status = {"task_parameters_folder": task_folder}
        manager = tm.TaskManager(status)
        assert manager.queue is None
        manager.queue = self.queue
        assert len(manager.queue) == 0
        assert manager.task_folder == task_folder

        manager.scan_tasks()
        assert len(manager.tasks) == 1

    def test_check_tasks(self, folders, folder_task):
        data_folder, task_folder, executables_folder = folders
        status = {"task_parameters_folder": task_folder}
        manager = tm.TaskManager(status)
        manager.queue = self.queue

        for i in range(4):
            open(os.path.join(data_folder, f"file{i}"), "w").close()

        manager.scan_tasks()
        assert len(manager.tasks) == 1
        manager.check_tasks()
        assert len(manager.queue) == 2
