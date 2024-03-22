# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.

import odop


@odop.task.task(name="example_task")
@odop.task.time_limit("15min")
@odop.task.memory_limit("1G")
def example_task_function(parameter1):
    # The task can be an arbitrary Python function
    print("Running example task, got parameter:", parameter1)


