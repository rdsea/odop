# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.

import odop
from odop import task_manager


@odop.task.task(name="example_task")
@odop.task.time("15min")
def example_task_function(parameter1):
    # The task can be an arbitrary Python function
    print("Running example task, got parameter:", parameter1)


