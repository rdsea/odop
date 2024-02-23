# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.

from odop import task_manager

@task_manager.odop_task(name="example_task", time="2h", cpu="2", memory="2G")
def example_task_function():
    # The task can be an arbitrary Python function
    print("Running example task")

