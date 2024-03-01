# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.

from odop import task_manager

@task_manager.odop_task(
    name="example_task", time="2h", cpu="2-4", memory="2G",
    filenames = ["input_data_1", "input_data_2"],
    arguments={"parameter1": "str"}
)
def example_task_function(parameter1):
    # The task can be an arbitrary Python function
    print("Running example task, got parameter:", parameter1)

