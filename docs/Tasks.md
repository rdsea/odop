# Task interface

## Creating a task

```python
from odop import task

@task.task("name")
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
