import os
import random
import sys
import time

import odop

# add the module path to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import task_scanner_dependency


@odop.task("name")
def task():
    print("Task")
    return 1


@task_scanner_dependency.derived_task("extra_parameter")
def not_recognized_task():
    print("Task")
    return 1


# This is a script section that does heavy computation
start_time = time.time()
sum = 0
for _i in range(100):
    r = random.random()
    sum += r
print(f"Sum: {sum}")
print(f"Time: {time.time() - start_time}")


if __name__ == "__main__":
    raise Exception("This is a module, not a script")
