""" Tests for the task_manager module. """

import os
import odop
import pandas as pd

module_dir = os.path.dirname(os.path.abspath(odop.__file__))
examples_dir = os.path.join(module_dir, 'example_tasks')


def test_task():
    @odop.task.task("test_name")
    def test_task():
        return "success"

    assert type(test_task) == odop.task.Task

    assert test_task.name == "test_name"
    assert test_task.func() == "success"
    assert test_task.time_limit is None


def test_time_limit_and_memory():
    @odop.task.task("test_name")
    @odop.task.time_limit("5min")
    @odop.task.memory_limit("5G")
    def test_task():
        return "success"

    assert type(test_task) == odop.task.Task

    assert test_task.name == "test_name"
    assert test_task.func() == "success"
    assert test_task.time_limit == pd.to_timedelta("5min")
    assert test_task.memory_limit == "5G"


def test_task_list():
    @odop.task.task("task 1")
    def task_1():
        print("task 1")

    @odop.task.task("task 2")
    def task_2():
        print("task 2")

    @odop.task.task("task 3")
    def task_3():
        print("task 3")


    assert task_1.name == "task 1"
    assert task_2.name == "task 2"
    assert task_3.name == "task 3"

    assert odop.task.tasks[-3].name == "task 1"
    assert odop.task.tasks[-2].name == "task 2"
    assert odop.task.tasks[-1].name == "task 3"


def test_import_module():
    tasks = len(odop.task.tasks)
    odop.task.read_module(os.path.join(examples_dir, "example_task_with_decorator.py"))

    assert len(odop.task.tasks) == tasks + 1
    assert odop.task.tasks[-1].name == "example_task"
