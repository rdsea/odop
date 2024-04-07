import odop
import pandas as pd


def test_task():
    @odop.task.task("test_task")
    def test_task_function():
        return 1

    assert test_task_function.name == "test_task"

    assert len(odop.task.tasks) == 1
    assert odop.task.tasks[0] == test_task_function


def test_decorators():
    @odop.task.task("test_task")
    @odop.task.time_limit("2h")
    @odop.task.memory_limit("2G")
    def test_task_function():
        return 1

    assert test_task_function.name == "test_task"
    assert test_task_function.time_limit == pd.to_timedelta("2h")
    assert test_task_function.memory_limit == "2G"
