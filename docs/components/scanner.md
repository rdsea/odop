# Task Scanner

The task scanner checks files for Odop tasks at the beginning of a run. Any Python files with
tasks defined at the top level will be identified by the task scanner and the tasks will be
added to the runtime.

The task scanner does not pick up tasks defined in function, classes, loops or any other code
blocks. The task must be at top level and the decorator must be named "odop.task".

It tasks are found, the task scanner runs the Python file until the last line of the last
task. This ensures we capture any task definitions, but do not run any unnecessary code.

The user can define tasks manually in the main code file by creating a task function using
the `@odop.task` decorator. This allows creating tasks programatically.

