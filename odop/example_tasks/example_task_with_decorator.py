# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.

import time
from odop import task_manager

@task_manager.odop_task(name="example_task", time="2h")
def example_task_function():
    # The task can be an arbitrary Python function
    print("Starting the task")
    time.sleep(60*4)
    print("Done with the task")

