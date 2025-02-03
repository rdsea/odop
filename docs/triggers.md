# Triggers

The task is queued when the trigger condition is fulfilled. Odop defines
three trigger conditions: `FileIn`, `FileUpdated`, and `Timer`.

If a task does not have a trigger condition, it is queued immediately and
requeued whenever it leaves the queue. This is useful for a low priority
task that should run whenever the queue is empty.

```python
@odop.task(
    name="low_priority_task",
)
def task_function():
    # Your task implementation here
    print("This task runs whenever the queue is empty.")
```

## FileUpdated

A task with a `FileUpdated` trigger is queued when the specified file changes.

```python
@odop.task(
    name="file_updated_task",
    trigger=odop.FileUpdated("data_folder/file.txt"),
)
def task_function(filename):
    # Check that writing to the file has finished
    with open(filename, "r") as f:
        data = f.read()
    if len(data) > 0:
        # Your task implementation here
        print(f"File {filename} has been updated.")
```

Note that we cannot guarantee that the file is properly formatted when the task
is triggered.

The task triggers whenever the timestamp of the file changes. This can happen when
the file is opened for writing, even if no data is written to the file. In the above
example, we check that the file is not empty before running the task.


## FileIn

A task with a `FileIn` trigger is queued when a file is added to the specified
folder.

```python
@odop.task(
    name="file_in_folder_task",
    trigger=odop.FileIn("data_folder"),
)
def task_function(filename):
    while not is_formatted_correctly(filename):
        time.sleep(1)
    # Your task implementation here
    print(f"File {filename} has been added to the data folder.")
```

As above, we cannot guarantee that the file is properly formatted when the task
is triggered. However, the FileIn trigger only triggers once for each file. In
the example we use a `while` loop to wait untill the file has finished writing.


## Timer

A task with a `Timer` trigger is queued at regular intervals.

```python
@odop.task(
    name="timer_task",
    trigger=odop.Timer(60),
)
def task_function():
    # Your task implementation here
    print("This task runs every 60 seconds.")
```
