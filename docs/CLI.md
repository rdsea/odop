# Command Line Interface

The Odop command line interface accepts 2 commands.

 - The `odop scan_tasks_folder` command scans the tasks folder for tasks and
   adds them to a running odop instance. Run it as

```bash
odop scan_tasks_folder RUN_NAME TASK_FOLDER
```


 - The `visualize_folder` command creates a visualization of resource usage
   for a given run. It is useful for understanding what resources you have
   available for opportunistic tasks. Run it as

```bash
odop visualize_folder RUN_NAME
```