from ctypes import *

# from odop.odop_obs import OdopObs
# import odop.odop_obs
import odop
import time

# so_file = "./src/libPC.so"
# my_funcs = CDLL(so_file)


def main():
    # odop_obs = OdopObs()
    # odop_obs.start()
    # odop.start(task_folder="./tasks", config_file="/users/anhdungn/.odop/odop_conf_1_task_data_movement_round_robin.yaml")
    odop.start(
        task_folder="./tasks",
        config_file="/users/anhdungn/.odop/odop_conf_1_task_data_movement_round_robin.yaml",
    )

    # my_funcs.run_start()
    # start_time = time.time()
    while time.time() - start_time < 480:
        time.sleep(1)
    # print("End from python")

    odop.stop()
    # odop_obs.stop()


if __name__ == "__main__":
    main()
