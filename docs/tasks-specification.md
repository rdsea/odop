# Task Specification


## Use cases

### Slice Renderer

When the user signals for the slice renderer to run, it
reads in data from a known set of files (or files listed
in a signal file). Runs on a single nodes and outputs files
into a folder.


### Periodic Rendering or Health check

Runs periodically, based on real time and not simulation time.

Reads current data files from a known location and outputs 
files to a set output folder.


### Heavy threaded + MPI data processing time series data

For example Fourier transform.

The main process appends blocks to a large data file. The task runs for each appended block in order. The file is not deleted.

Implementation: The main process writes an info file with one line per task. A task is created for each line in order. When the task is complete, the corresponding line is appended to a another line indicating the line is processed.

Runs on every node in the simulation. Reads data from a local 
disk or a shared disk. Uses all available CPUs. Writes results
to shared disk or local disk.

- The same number of nodes and tasks as the main program
- The same number of CPUs per task as the main program


### Process Pre-existing Data

Triggers when a given folder matching pattern exists. Folder is not deleted.

Runs on every node in the simulation. Reads data from a local 
disk or a shared disk. Uses all available CPUs. Writes results
to shared disk or local disk.


### Process a Snapshot

Triggers when main process creates a file. The file is deleted when the task is done.

Runs on every node in the simulation. Reads data from a local 
disk or a shared disk. Uses all available CPUs. Writes a smaller file.


### Independent MPI tasks on all nodes

For each MPI process, run a task. These tasks do not communicate with each other.

Triggers when a file is created
 1. One big file. Maybe deleted at the end?
 2. Many files, one for each MPI process. Fully independent.

Each task has and index from 0 to the highest MPI rank.


### Training an ML model based on output data

Training on the GPU or the CPU?

A full MPI task running for a relatively long time. Reads an output file from the main
program stored in local disk. Outputs trained models into shared disk.



## Task type implementations:

 - for_line_in_file
 - periodic
 - when file or folder exists (then delete)

Modifiers and options
 - MPI option
 - Threaded option (what is the default)


API for communicating with the main process
 - Odop notifies the main process that a task is completed
 - Main process polls Odop for task status
 - If niceness level is not sufficient, main process notifies Odop when it starts and stops

### Related to user triggered jobs

Odop client: a UI
 - how many tasks are running
 - resources available
 - queue length
 - ...



## Task specification

Opportunistic tasks are executables or functions that are run when the scheduler expects sufficient resources
to be available for the duration of the task. A task consists of the actual executable or code to be run
and scheduling and runtime parameters.

Here is an example of a task specification list in the json format:

```json
[
    {
        "task_id": "task 0",
        "time": "10min",
        "memory": "1G",
        "threads": 1,
    
        "input_folder": "data",
    
        "module": "example_task.py",
        "function": "step_a",
    },
    {
        "task_id": "task 1",
        "time": "5min",
        "memory": "1G",
        "threads": 1,

        "input_file_expression": "processed_data/*.data",

        "executable": "executable_name",
        "parameter_mapping": "--{key} {value}",
        "dependencies": ["task 0"]
    }
]
```

Here the first task is run when there are files in the `data` folder. The second task is run after the first task
requires files matching the regular expression `processed_data/*.data`.


## Python decorators

Tasks can be specified as Python functions using the odop task decorators. Here is an example
of a task

```{literalinclude} examples/task_specification_decorator.py
:start-after: "# example 1"
:end-before: "# end 1"
```


This is equivalent to directly creating and registering the
task object.

```{literalinclude} examples/task_specification_decorator.py
:start-after: "# example 2"
:end-before: "# end "
```

    
Some common task types have dedicated decorators, such as `for_file_in_folder`

```{literalinclude} examples/task_specification_decorator.py
:start-after: "# example 3"
:end-before: "# end 3"
```


## Task Spec

### Scheduler specification

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
    - time: time_unit, default 20min
        - Estimate of the time the task will take. Can be used for scheduling, but not a hard limit.
    - memory: integer or memory_units, default = 1M
        - Estimate of memory used by the program. Can be used for scheduling, but overflow needs to be reserved.
    - memory: integer or memory_units, default = 1M
        - Upper limit of memory the task will use. No need to reserve extra.
    - disk space limit: integer or memory units, default = 100M
        - Amount of free disk space required to run the task
    - cores: integer or "all", default="all"
        - The number of cpu cores the task reserves for each MPI rank.
        - "all" means only one rank can run on each node.
    - ranks_per_node: integer or "all", default=1
        - The number of MPI ranks to start on each node.
        - "all" sets this to the number of mpi ranks on the main process.
        - If this is not 1, we use `srun` to start the task
    - nodes: integer or "all", default = 1
        - The number of nodes the task reserves.
        - "all" means the task requires all nodes to be available.
        - If this is not 1, we use `srun` to start the task

    - io_task: bool, default False
        - Whether the task is IO bound. If True, we don't run multiple at a time, but can run non-io tasks
    - network_task: bool, default False
        - Whether the task is network bound. If True, we don't run multiple at a time, but can run
          non-network tasks.

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
    - rerun_on_change: bool, default False
        - If True, the task is rerun if any of the input files change.

    - ready signal: string, multiple
        - A signal from the main process that the task can be run. (Initial implementation through the files system).
    - output_file: string, multiple
        - If there is a file with this name, the task is considered done.
    - output folder: string
        - Outputs are moved to this folder if it is specified. Otherwise they are left where they are.

    - checkpointing specification
        - is interruptable: bool = False
            - Whether the task can be interrupted and resumed
        - what to do in case of failure
        - Is SIG-STOP an option?

    - priority: integer, default 0
        - Task priority. Higher priority tasks are executed first.
    - dependency: slist of task ids, default []
        - tasks that need to be run first.


### Time_unit

 - integer followed by "s", "m" or "h"


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
    - file_path: str
        - Path to the checkpoint file
4. Process files
    - The task processes files and remove / moves them when done. File removed from a folder corresponds to progress.
    - file_path: str, multiple, optional
        - If provided, when any of these files is removed, we consider that progress in the task.
        - default: List of all input files provided in other options



