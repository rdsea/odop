import numpy as np

import odop


def derived_task(extra_parameter):
    print("Derived task with extra parameter: ", extra_parameter)
    print(np.sum([1, 2, 3]))
    return odop.task()
