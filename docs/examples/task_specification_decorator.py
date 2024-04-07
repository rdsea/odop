import odop

#example 1
@odop.task.task("task 0")
@odop.task.time_limit("10min")
@odop.task.single_file
@odop.task.input_folder("data")
def step_a():
    print("Running task 0")
#end 1


#example 2
def step_a():
    print("Running task 0")

task = odop.task.Task("task 0", step_a)
task.memory_limit = "1G"
task.single_file = True
task.input_folder = "data"

odop.tasks.register_task(task)
#end 2


#example 3
@odop.task.for_files_in_folder("output_data")
def step_a(filename):
    print(f"Found file called {filename} in output_data")
#end 3

