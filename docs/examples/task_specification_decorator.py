import json

import odop
import odop.task_definition

# example 1
parameters = json.read("run_params.json")
step_a_memory = f"{parameters["grid_size"] * 10}"


@odop.task(
    name="task 0",
    trigger="file_in_folder",
    folder_path="data",
    time="10min",
    memory=step_a_memory,
    batch_size=1,
)
def step_a():
    print("Running task 0")


# end 1


# example 2
def step_b():
    print("Running task 0")


task = odop.task_definition.Task("task 1", step_a)
task.memory = "1G"
task.single_file = True
task.input_folder = "data"

odop.task.register_task(task)
# end 2


# example 3
@odop.task.for_file_in_folder("output_data")
def step_a(file_path):
    print(f"Found file called {file_path} in output_data")


# end 3
