# An example tasks for the opportunistic scheduler. This file contains the
# task function. The corresponding json file contains the parameters. Later,
# these can be provided using @decorators.

import time

def example_task_function():
    # The task can be an arbitrary Python function
    print("Starting the task")
    time.sleep(60*4)
    print("Done with the task")

