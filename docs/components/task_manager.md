# Task Manager

The task manager is a component of the Odop runtime. The user does not directly interact with
the task manager. It is started by the `odop.start()` function.

The task manager periodically scans the runtime folder for task specifications and checks
their trigger conditions. When they are met, it creates an scheduler task and adds it to the
queue.

## Task Queue

The task queue is a shared resource that holds tasks that are ready to run. The scheduler
pulls tasks from the queue when resources are available and sends them to the engine.
