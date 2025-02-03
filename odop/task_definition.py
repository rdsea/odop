"""
The odop task decorators are used to mark tasks in written as
Python functions. Each decorator modifies the task specification
and saves the changes into the task list.

Once the tasks are read, they need to be processed to serialize
the function.
"""

from __future__ import annotations

import inspect
import json
import os
import uuid
from abc import abstractmethod
from typing import Callable

import cloudpickle

from odop.scanner.task_scanner import OdopTaskScanner


def convert_to_megabytes(memory_str):
    """Convert a memory string to megabytes."""
    unit_to_multiplier = {"T": 1024**2, "G": 1024, "M": 1}
    size, unit = memory_str[:-1], memory_str[-1]
    size_in_mb = float(size) * unit_to_multiplier[unit.upper()]
    return size_in_mb


def read_time_string(time_string):
    """Read a time string and convert it to integer seconds."""
    time_unit = time_string[-1]
    time_value = int(time_string[:-1])
    if time_unit == "h":
        time_value = time_value * 3600
    elif time_unit == "m":
        time_value = time_value * 60
    elif time_unit == "s":
        pass
    else:
        raise ValueError("Time unit not recognized. Must be 's', 'm' or 'h'.")
    return time_value


class Trigger:
    def __init__(self, trigger_type: str):
        """Base class for a trigger for an odop task. Three types of triggers are supported:
        - file_in_folder: Triggered when a file is added to a folder
        - file_updated: Triggered when a file is updated
        - timer: Triggered periodically
        """
        self.trigger_type = trigger_type

    def wrap_filename_argument(self, func):
        """Wrap a function to take a filename argument with a function that accepts a filenames
        list.
        """

        def wrapped(filenames):
            return func(filenames[0])

        return wrapped

    @abstractmethod
    def set_task_parameters(self, task: Task):
        pass


class FileIn(Trigger):
    def __init__(
        self, folder_path: str, batch_size: int = 1, filter: str | None = None
    ):
        """File in folder trigger condition. Triggered when a file is added to a folder.

        Parameters:
        -----------
        folder_path: str
            The path to the folder to watch
        batch_size: int, optional
            The number of files to process in a single run
            By default, the task will process one file at a time
        filter: str, optional
            A filter file names must match to be processed. For example "*.csv".
        """
        assert type(folder_path) is str
        assert type(batch_size) is int
        assert filter is None or type(filter) is str
        super().__init__("file_in_folder")
        self.folder_path = folder_path
        self.batch_size = batch_size
        self.filter = filter

    def set_task_parameters(self, task):
        task.folders = [self.folder_path]
        task.batch_size = self.batch_size
        task.filter = self.filter

        # Check that the task takes either "filename" or "filenames" as an argument
        signature = inspect.signature(task.func)
        if self.batch_size == 1:
            if "filename" in signature.parameters.keys():
                task.func = self.wrap_filename_argument(task.func)
            elif "filenames" not in signature.parameters.keys():
                raise ValueError(
                    "A file in folder task must take either 'filename' or 'filenames' as an argument"
                )
        else:
            if "filenames" not in signature.parameters.keys():
                raise ValueError(
                    "A file in folder task must take 'filenames' as an argument when batch_size > 1"
                )


class FileUpdated(Trigger):
    def __init__(self, file_path: str):
        """File updated trigger condition. Triggered when a file is updated.

        Parameters:
        -----------
        file_path: str
            The path to the file to watch.
        """
        assert type(file_path) is str
        super().__init__("file_updated")
        self.file_path = file_path

    def set_task_parameters(self, task):
        task.watch_file = self.file_path

        # Check that the task accepts a filename or filenames parameter
        signature = inspect.signature(task.func)
        if "filename" in signature.parameters.keys():
            task.func = self.wrap_filename_argument(task.func)
        elif "filenames" not in signature.parameters.keys():
            raise ValueError(
                "A file updated task must take either 'filename' or 'filenames' as an argument"
            )


class Timer(Trigger):
    def __init__(self, interval: str | int):
        """Timer trigger condition. Triggered periodically.

        Parameters:
        -----------
        interval: str or int
            The time between runs. Must be a string formatted as a number
            followed by a time unit. Either 's', 'm' or 'h' for seconds,
            minutes or hours.
        """
        assert type(interval) is str or type(interval) is int
        super().__init__("timer")
        self.interval = interval

    def set_task_parameters(self, task):
        if type(self.interval) is int:
            task.interval = self.interval
        else:
            task.interval = read_time_string(self.interval)


class Task:
    """An odop task definition. Wraps a function and a set of task parameters"""

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        priority: int = 0,
        time: str | int = "60m",
        memory: str | int = "100M",
        nodes: int | str = "any",
        ranks_per_node: int | str = "any",
        ranks: int = "any",
        cpus_per_rank: int | str = "any",
        cpus: int | str = "any",
        disk_limit: str | int = 0,
        io_bound: bool = False,
        network_bound: bool = False,
        depends_on: str | None = None,
        max_runs: int | None = None,
        replicas: int = 1,
    ):
        """Initialize the task and provide the task function"""
        # Task parameters
        if depends_on is None:
            depends_on = []
        self.execution_type = "python_task"
        self.func = func
        if name is not None:
            self.name = name
        else:
            self.name = str(uuid.uuid4())
        self.priority = priority

        # Resource parameters
        self.time = read_time_string(time)
        self.memory = convert_to_megabytes(memory)
        self.nodes = nodes
        self.ranks_per_node = ranks_per_node
        self.ranks = ranks
        self.cpus_per_rank = cpus_per_rank
        self.cpus = cpus
        self.disk_limit = convert_to_megabytes(disk_limit)
        self.io_bound = io_bound
        self.network_bound = network_bound
        if type(depends_on) is str:
            self.depends_on = [depends_on]
        else:
            self.depends_on = depends_on
        self.max_runs = max_runs
        self.replicas = replicas

        if nodes != "any":
            assert (
                cpus == "any"
            ), f"Cannot specify cpus and nodes at the same time. Use ranks_per_node and cpus_per_rank instead. cpus = {cpus}"
            assert (
                ranks == "any"
            ), f"Cannot specify ranks and nodes at the same time. Use ranks_per_node instead. ranks = {ranks}"
            if ranks_per_node == "any":
                ranks_per_node = 1
            if cpus_per_rank == "any":
                cpus_per_rank = 1
        else:
            assert (
                ranks_per_node == "any"
            ), f"Cannot specify ranks_per_node without specifying nodes. ranks_per_node = {ranks_per_node}"

        if ranks != "any":
            assert (
                nodes == "any"
            ), f"Cannot specify nodes with ranks. Use ranks_per_node instead. nodes = {nodes}"
            assert (
                cpus == "any" or cpus == "all"
            ), f"Cannot specify cpus with ranks. Use cpus_per_rank instead. cpus = {cpus}"
            if cpus_per_rank == "any":
                cpus_per_rank = 1
        else:
            assert (
                cpus_per_rank == "any" or ranks_per_node != "any"
            ), f"Cannot specify cpus_per_rank without specifying ranks. cpus_per_rank = {cpus_per_rank}"

        if nodes == "any" and ranks == "any" and cpus == "any":
            cpus = 1

        if ranks_per_node == "all" or ranks == "all":
            assert (
                cpus_per_rank == "any"
            ), f"Cannot specify cpus_per_rank with ranks_per_node or ranks = all. cpus_per_rank = {cpus_per_rank}"
            assert (
                cpus == "any"
            ), f"Cannot specify cpus with ranks_per_node or ranks = all. cpus = {cpus}"
            cpus = "all"

        if ranks == "all":
            nodes = "all"
            ranks_per_node = "all"

        self.nodes = nodes
        self.ranks_per_node = ranks_per_node
        self.ranks = ranks
        self.cpus_per_rank = cpus_per_rank
        self.cpus = cpus

        # Trigger parameters, set by job type
        self.watch_file: str | None = None
        self.files = []
        self.folders = []
        self.file_pattern = []
        self.filter: str | None = None
        self.batch_size = 1
        self.interval = 0

    def to_dict(self):
        """Create a dictionary of the task parameters and the function.
        This is used to serialize the task for the scheduler and the engine.
        """
        return dict(self.__dict__)

    def __call__(self, *args, **kwargs):
        """Enable the instance to be called like a function"""
        return self.func(*args, **kwargs)


class TaskDefinitionManager:
    def __init__(self):
        self.tasks = {}

    def register_task(self, task):
        """Register a task for the scheduler.

        Currently just adds it to the list.
        """
        if task.name in self.tasks:
            if task.func != self.tasks[task.name].func:
                raise ValueError(f"Task with name {task.name} already exists.")
        self.tasks[task.name] = task

    def task(
        self,
        name: str | None = None,
        trigger: Trigger | None = None,
        priority: int = 0,
        time: str | int = "60m",
        memory: str | int = "100M",
        nodes: int | str = "any",
        ranks_per_node: int | str = "any",
        ranks: int = "any",
        cpus_per_rank: int | str = "any",
        cpus: int | str = "any",
        disk_limit: str | int = "1M",
        io_bound: bool = False,
        network_bound: bool = False,
        depends_on: str | None = None,
        max_runs: str | int = 0,
        replicas: str | int = 0,
    ):
        """Create an Odop task. This is the primary Odop task decorator.
        Any other decorators call this one and set parameters or wrap the
        task function.

        Parameters:
        -----------
        name: str
            The name of the task
        trigger: odop.Trigger (optional)
            A trigger condition for the task
        priority: int (optional)
            The priority of the task
        time: str (optional)
            The time limit for the task
        memory: str (optional)
            The memory limit for the task
        cpus: int, "all" (optional)
            The number of CPUs to reserve
        ranks: int (optional)
            The number of mpi ranks to create
        nodes: int (optional)
            The number of nodes to run on
        disk_limit: int (optional)
            The disk space limit for the task
        io_bound: bool (optional)
            Whether the task is I/O bound
        network_bound: bool (optional)
            Whether the task is network bound
        depends_on: str (optional)
            The name of a task this task depends on
        max_runs: int (optional)
            The maximum number of times the task can run
        replicas: int (optional)
            The maximum number of copies exact of the task that can be queued
            at once
        """

        # assert all type hints
        assert name is None or type(name) is str
        assert isinstance(trigger, Trigger) or trigger is None
        assert type(priority) is int
        assert type(time) is str or type(time) is int
        assert type(nodes) is str or type(nodes) is int
        assert type(ranks_per_node) is str or type(ranks_per_node) is int
        assert type(ranks) is str or type(ranks) is int
        assert type(cpus_per_rank) is str or type(cpus_per_rank) is int
        assert type(cpus) is str or type(cpus) is int
        assert type(disk_limit) is str or type(disk_limit) is int
        assert type(io_bound) is bool
        assert type(network_bound) is bool
        assert depends_on is None or type(depends_on) is str
        assert type(max_runs) is int or type(max_runs) is str
        assert type(replicas) is int or type(replicas) is str

        def decorator(task):
            assert callable(task)
            if type(task) is Task:
                task = task.func

            task = Task(
                task,
                name=name,
                priority=priority,
                time=time,
                memory=memory,
                nodes=nodes,
                ranks_per_node=ranks_per_node,
                ranks=ranks,
                cpus_per_rank=cpus_per_rank,
                cpus=cpus,
                disk_limit=disk_limit,
                io_bound=io_bound,
                network_bound=network_bound,
                depends_on=depends_on,
            )

            if isinstance(trigger, Trigger):
                trigger.set_task_parameters(task)

            _max_runs = max_runs
            if type(_max_runs) is str:
                if _max_runs == "MANY":
                    _max_runs = 0
                elif _max_runs == "ONCE":
                    _max_runs = 1
                elif _max_runs == "ONE":
                    _max_runs = 1
            task.max_runs = _max_runs

            _replicas = replicas
            if type(_replicas) is str:
                if _replicas == "MANY":
                    _replicas = 0
                elif _replicas == "ONCE":
                    _replicas = 1
                elif _replicas == "ONE":
                    _replicas = 1
            task.replicas = _replicas

            self.register_task(task)

            return task

        return decorator

    def for_file_in_folder(self, folder_path, batch_size=1, filter=None, **kwargs):
        """Create a task that iterates over all files in a folder.

        Parameters:

        folder_path: str
            The path to the folder_path to iterate over

        task_name: str, optional
            The name of the task
            By default, a random string ID is used

        batch_size: int, optional
            The number of files to process in a single run
            By default, the task will process one file at a time

        filter: str, optional
            A filter file names must match to be processed. For example "*.csv".
        """

        return self.task(
            trigger=FileIn(
                folder_path=folder_path, batch_size=batch_size, filter=filter
            ),
            **kwargs,
        )

    def file_updates(self, filename, **kwargs):
        """Create a task that watches a file for changes. This is a primary
        task definition decorator. It registers the task to the task list.

        Parameters:

        filename: str
            The path to the file to watch

        priority: int, optional
            The priority of the task
        """

        return self.task(trigger=FileUpdated(file_path=filename), **kwargs)

    def periodic(self, interval, **kwargs):
        """Create a task that runs periodically. This is a primary task
        definition decorator. It registers the task to the task list.

        Parameters:

        interval: str
            The time between runs. Must be a string formatted as a number
            followed by a time unit. Either 's', 'm' or 'h' for seconds,
            minutes or hours
        """

        return self.task(trigger=Timer(interval=interval), **kwargs)

    def run_once(self, **kwargs):
        """Create a task that runs once. The task does not depend on any
        trigger conditions. This is a primary task definition decorator.
        It registers the task to the task list.

        Parameters:

        task_name: str, optional
            The name of the task
            By default, a random string ID is used
        """

        return self.task(
            max_runs=1,
            **kwargs,
        )

    def background(self, **kwargs):
        """create a background task. This is a low priority task that
        can be run when no other tasks are available. This is a primary
        task decorator. It registers the task to the task list.

        Parameters:

        name: str
            The name of the background task
        """

        return self.task(
            replicas=0,
            **kwargs,
        )

    def read_module(self, module):
        """Read a module and find all tasks in it. It's actually enough to just execute it.

        Parameters:

        module: module
            The module to read tasks from
        """
        if not module.endswith(".py"):
            module = module + ".py"

        scanner = OdopTaskScanner(module)
        scanner.import_tasks()
        print("tasks:", self.tasks)

    def write_all(self, task_folder="tasks", executables_folder="executables"):
        """Write the task list to a file. This is used to serialize the tasks
        for the scheduler and the engine.
        """
        os.makedirs(task_folder, exist_ok=True)
        os.makedirs(executables_folder, exist_ok=True)
        for name, task in self.tasks.items():
            task_dict = task.to_dict()
            function = task_dict.pop("func")

            json_path = f"{task_folder}/{name}.json"
            if not os.path.exists(json_path):
                with open(json_path, "w", encoding="utf-8") as file:
                    print("writing to", json_path)
                    json.dump(task_dict, file, indent=4)

                function_path = f"{executables_folder}/{name}.pickle"
                with open(function_path, "wb") as file:
                    cloudpickle.dump(function, file)

    def load_tasks_folder(
        self,
        folder,
        task_folder="tasks",
        exclude_file=None,
    ):
        """Find odop tasks in all Python modules in a folder. Tasks are saved
        to an output folder with the information necessary to run them.

        Parameters:

        folder: str
            A folder containing Python modules with odop tasks
        """

        files = os.listdir(folder)
        for file in files:
            path = os.path.join(folder, file)
            if path == exclude_file:
                continue
            if file.endswith(".py"):
                # If it's a python module, run it to create task objects
                task.read_module(path)

    __call__ = task


"""The main task decorator object, which contains the other
decorators. Singleton."""
task = TaskDefinitionManager()
