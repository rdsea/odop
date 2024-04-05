# Task specifications


Opportunistic tasks are executable or functions that are run when the scheduler expects sufficient resources
to be available for the duration of the task. A task consists of the actual executable or code to be run
and and scheduling and runtime parameters.

Here is an example of a task specification list in the json format:

```json
[
    {
        "task_id": "task 0",
        "time_limit": "10min",
        "memory_limit": "1G",
        "threads": 1,
    
        "input_folder": "data",
    
        "module": "example_task.py",
        "function": "step_a",
    },
    {
        "task_id": "task 1",
        "time_limit": "5min",
        "memory_limit": "1G",
        "threads": 1,

        "input_file_expression": "processed_data/*.data",

        "executable": "executable_name",
        "parameter_mapping": "--{key} {value} ",
        "dependencies": ["task 0"]
    }
]
```

Here the first task is run when there are files in the `data` folder. The second task is run after the first task
requires files matching the regular expression `processed_data/*.data`.


## Python decorators

Tasks can be specified as Python functions using the odop task decorators. Here is an example
of a task

```python
import odop

@odop.task("task 0")
@odop.time_limit("10min")
@odop.single_file
@odop.input_folder("data")
def step_a():
    print("Running task 0")
```


This is equivalent to directly creating and registering the
task object.

```python
import odop

def step_a():
    print("Running task 0")

task = odop.task.Task("task 0", step_a)
task.memory_limit = "1G"
task.single_file = True
task.input_folder = "data"

odop.tasks.register_task(task)
```


Some common task types have dedicated decorators, such as `for_files_in_folder`

```python
import odop

@odop.for_files_in_folder("output_data")
def step_a(filename):
    print(f"Found file called {filename} in output_data")
```





## Task Spec

Task specification is created by the developer. Most arguments are optional. Can be formatted as
JSON. Specifying parameters as a JSON file is supported. In Python code, these parameters can
be provided using function decorators.

The parameters are stored as a dictionary, but may be communicated a JSON file.

- required:
    - execution parameter:  execution_parameter
        - Specifies how the task is executed

- optional:
    - task id: string
        - An identifier for the task, used to store and retrieve information and for dependencies.
        - Default to random UUID
    - time limit: integer or time_units, default = 1min
        - Upper limit for the tasks runtime in seconds or provided unit
    - memory limit: integer or memory_units, default = 1M
        - Upper limit of memory the task can use in megabytes or provided unit
    - disk space limit: integer or memory units
        - Amount of free disk space required to run the task
    - threads: integer, default=1
        - Maximum number of threads the task will use

    - input path: string, multiple
        - list of files required for the task
        - standard protocol specifications (ftp://, http://, ...). File system is default.
    - input folder: string, multiple
        - folder that must contain a file
    - input file expression: string, multiple
        - regular expression that must match a file
    - single file task: bool, default False
        - Run a separate task for each file in required_folder or matching required_file_expression
    - filepath parameter: string, multiple
        - parameter name for passing a dynamically determined file name to the task

    - ready signal: string, multiple
        - A signal from the main process that the task can be run. (Initial implementation through the files system).
    - output folder: string
        - folder for output files and logs

    - parameters: dict, default = {}
        - A dictionary of parameter names and values
    - checkpointing specification
        - is interruptable: bool = False
            - Whether the task can be interrupted and resumed
        - what to do in case of failure

    - priority: integer, default 0
        - Task priority. Higher priority tasks are executed first.
    - niceness: integer, default 0
        - negated priority 
    - dependency: list of task ids, default []
        - tasks that need to be run first.


### Time_unit

 - timedelta formattable string
 - We only support [pandas.to_timedelta](https://pandas.pydata.org/docs/reference/api/pandas.to_timedelta.html)


### Memory_unit

 - integer followed by "M" or "G"


### Execution parameter

Multiple options:
1. Executable
    - required:
        - Executable: str
            - Full path to an executable file.
        - number of threads
    - optional:
        - Parameter mapping 
2. Python function
    - required:
        - Pickled function file
        - number of threads


### Checkpointing Spec

Specifies whether the task can be interrupted and if it can, when.

A task that runs over its tile limit will be cancelled, but by default we assume it did not complete
any useful work. The task would need to be rerun later with more time.

Options:
1. None
    - The task cannot be interrupted without losing all progress
2. Critical
    - The task cannot be interrupted without compromising the main process.
3. Checkpoint
    - The task creates periodic checkpoint files. The modified timestamp of the file shows when a checkpoint has been created.
    - Filename: str
        - Path to the checkpoint file
4. Process files
    - The task processes files and remove / moves them when done. File removed from a folder corresponds to progress.
    - Filename: str, multiple, optional
        - If provided, when any of these files is removed, we consider that progress in the task.
        - default: List of all input files provided in other options


## Scheduler Spec

JSON formatted information that specifies when and how the task is executed.

Generated by the task reader. 


- required:
    - execution parameter:  execution_parameter

- optional:
    - task id: string
    - time limit: integer or time_units, default = 1min
    - memory limit: integer or memory_units, default = 1M
    - number of threads: integer, default=1
    - disk space limit: integer or memory units

    - priority: integer, default 0
    - niceness: integer, default 0
    - dependency: list of task ids, default []

    - input path: string, multiple
    - input folder: string, multiple
    - input file expression: string, multiple
    - filepath parameter: string, multiple
    - ready signal: string, multiple
    - checkpointing specification

    - single file task: bool, default False
    - output folder: string
    - parameters: dict, default = {}


## Engine spec

- required:
    - Task id
    - execution parameter

    - is interruptable
    - cpu time
    - memory limit

- optional:
    - input file path: file_name, multiple
    - input folder path: folder
