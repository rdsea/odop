# Tasks

## The task decorator

An opportunistic task is defined using the `@odop.task` decorator above the
task function. For example:

```python
import odop

@odop.task(
    name="task_name",
    trigger=odop.Timer("1h"),
)
def task_function():
    # Your task implementation here
    print(f"This task runs every hour.")
```

The task_function defines the actual task to run and the decorator takes
parameters used to find opportunities to execute the task. The decorator
accepts a number of parameters. The `name` parameter is required and must
be unique for each task. All other parameters are optional.

Optional parameters include 
- `trigger` which specifies when the task should be run.
- `priority` which specifies the priority of the in the queue. Priority
             applies when the task has been triggered, and higher priority tasks
             run more quickly.
- `cpus` which specifies the number of CPUs to use for the task.
- `memory` which specifies the amount of memory to use for the task.
- `ranks` which specifies the number of ranks to use for the task.
- `nodes` which specifies the number of nodes to use for the task.

Several other parameters are available. See the [API documentation](/api/odop.rst#odop.task_definition.TaskDefinitionManager.task)
for details.

## Task scanner

Odop will automatically identify task decorators in python files in the working
directory, if they appear at top level in the file. For example, the following
task will be identified by Odop:

```python
import odop

@odop.task(name="task_name")
def task_function():
    ...
```

The task scanner will not pick up tasks defined in functions, classes, loops and
so on. To define a task, the task decorator must be at the top level of the file.

Instead, you can create a task manually in your main code file:

```python
import odop

def function_that_defines_a_task(index):
    @odop.task(name=f"task_{index}")
    def task_function():
        ...

for i in range(10):
    function_that_defines_a_task(i)

if __name__ == "__main__":
    odop.start(run_name="monitor", config_file=config_file)
    # Your code here
    ...
    odop.stop()
```

In this case, the tasks must be defined before calling `odop.start()`.


