
# Scheduler

## Input Specification
- Whenever a new simulation result is ready, the processing task will be put into the task queue to wait for processing with the specific execution ID.
- Using the execution ID we can start, stop, skip (or pause) the task.
- Queue element specification:

```json
{
    "execution_id": <UUID>,
    "task_id": <UUID>,
    "execution_metadata": {
        "execution_option":{},
    },
    ...
}
```
- Based on ``task_id``, the schedule will get information including ``task specification`` as ``task profile``
### 1. Task Profiles
Task specification includes the task identifier (``task_id``), metadata, information to execute the task (``input_folder, module, function``), and execution requirements including time and computing resources .
- Example:
```json
{
    "task_id": <uuid>,
    "metadata":{},
    "execution_method":{
        "input_folder": "data",
        "module": "example_task.py",
        "function": "step_a",
    },
    "execution_requirement":{
        "time": "10min",
        "cpus": {
            "max": "1000mcpu",
            "min": "500mcpu"
        },
        "memory": {
            "max": "2G",
            "min": "1G"
        },
        "threads": {
            "max": "4",
            "min": "2"
        },
    }
}
```
### 2. System monitoring
The scheduler needs a monitoring system to infer (or predict) utilization pattern, to determine when the task is executed, and where (which core) without affecting the main simulation process.
```json
{
    // specification in docs/observation/monitoring.md
    "system_monitoring":{
        "cpu": {}, 
        "memory": {},
        "GPU": {},
        // and other resource e.g. network,...
    }
}
```
### 3. Process monitoring
- The main simulation's resource usage is monitor to combine with system monitoring in making execution decisions

- The tasks will be monitored and updated constantly at runtime


```json
{
    // specification in docs/observation/monitoring.md
    "process_monitoring":{
        "cpu": {}, 
        "memory": {},
        "GPU": {}, // not implemented
        // and other resource e.g. network,...
    }
}
```

## Output Specification
- When the task is executed, its resource usage will be measured again to update the task profiles
### 1. Profile Update
```json
{
    "task_id": <uuid>,
    "command": "update",
    "execution_requirement":{
        "time": "10min",
        "cpus": {
            "max": "1000mcpu",
            "min": "500mcpu"
        },
        "memory": {
            "max": "2G",
            "min": "1G"
        },
        "threads": {
            "max": "4",
            "min": "2"
        },
    }
}
```

### 2. Orchestration Command
- Once the time and place of execution have been determined, the schedule will send commands to the execution engine to start (or stop) the task.
```json
{
    "execution_id": <UUID>,
    "command": "start",  // stop, etc
    "task_id": <UUID>,
    "execution_metadata": {
        "execution_option":{},
    },
    "task_specification": {} // task profiles
    ...
}
```

## Test Scheduler

### Requirement
- Python > 3.10
- mpich
```bash
sudo apt install mpich
```
- libopenmpi-dev
```bash
sudo apt-get install libopenmpi-dev
```
- mpi4py == 3.1.6
```bash
pip install mpi4py
```

### Install `odop`
Note: navigate to `/odop` folder
```bash
pip install -e .
```
### Run Scheduler
Note: navigate to `/odop/scripts/` folder, create `/tasks` and `executables` folders, then export `$ODOP_PATH`

```bash
cd <$PATH_TO_ODOP_REPO>/odop/scripts/
mkdir tasks
mkdir executables
export ODOP_PATH="<PATH_TO_ODOP_REPO>/odop/odop/odop_obs/" 
python scheduler.py
```

### Debug
1. Error: "Failed building wheel for mpi4py"
- Log:
```bash
...
<$SOME_PATH/ld:>/usr/lib/x86_64-linux-gnu/openmpi/lib/libmpi.so: undefined reference to 'opal_list_t_class'
...
```
- Quick fix:
```bash
rm <$SOME_PATH/ld>
```