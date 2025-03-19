import time

# from odop.odop_obs import OdopObs
# import odop.odop_obs
from ctypes import CDLL

import odop

so_file = "./src/libPC.so"
my_funcs = CDLL(so_file)


def main():
    # odop_obs = OdopObs()
    # odop_obs.start()
    # odop.start(task_folder="./tasks", config_file="/users/anhdungn/.odop/odop_conf_1_task_data_movement_round_robin.yaml")
    odop.start(
        task_folder="./tasks",
        config_file="/users/anhdungn/.odop/odop_conf_1_task_data_movement_round_robin.yaml",
    )

    my_funcs.run_start()
    # print("End from python")

    odop.stop()
    # odop_obs.stop()


if __name__ == "__main__":
    main()
