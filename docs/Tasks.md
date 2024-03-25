# Task interface

## Creating a task

```python
from odop import task

@task.task("name")
@odop.memory_limit("1G")
@odop.single_file
def my_task():
    print("Hello, world!")
```


## Reading tasks in a folder

The `scheduler.read_folder` function reads all the tasks in a folder
and registers them in the task scheduler. The task information is also
pickled and stored as files for the engine.

```python
from odop import scheduler

scheduler.read_folder("odop/example_tasks")
```

## Running a task

The engine can run a pickled task given the file name. Json files containing
a dictionary of task parameters, including execution parameters, are also
supported.

```python
from odop import engine

engine.run("example_task.pickle")
```


