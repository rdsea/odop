# Tutorial

## Installation

To install odop, run the following command:

```bash
pip install git://github.com/rdsea/odop.git
```

## Monitoring

Odop provides a monitoring tool for identifying opportunities to run tasks.
Monitoring runs automatically as a part of Odop. If you do not have any Odop
tasks, you can start monitoring by calling `odop.start()` and `odop.stop()`.

```python
import odop

odop.start(run_name="monitor", config_file=config_file)

# Your code here

odop.stop()
```

## Defining an opportunistic task

To define an opportunistic task, use the `@odop.task` decorator. See
[Tasks](tasks.md) for information about specifying different types of
opportunistic tasks using triggers and scheduling parameters.

Odop will automatically identify task decorators in python files in
the working directory, if they appear at top level in the file.

```python
import odop

@odop.task(
    name="optask_name",
    trigger=odop.FileIn("data_folder"),
)
def task_function(filename):
    # Your task implementation here
    print(f"File {filename} has been added to the data folder.")
```

See [Triggers](triggers.md) for more information on trigger conditions.

You can specify different directory to search for using the `task_folder`
parameter:

```python
import odop

odop.start(run_name="monitor", config_file=config_file, task_folder="tasks")

# Your code here

odop.stop()
```

The `task_folder` parameter can be a path (string) or a list of paths (list of
strings).


