import ctypes
import os
import time

import odop


def main():
    heatlib = ctypes.cdll.LoadLibrary("solver/src/libheat_equation-shared.so")
    heatlib.run.argtypes = [ctypes.c_char_p]
    heatlib.run(b"solver/input.json")


if __name__ == "__main__":
    start_time = time.time()
    # create the pngs directory
    os.makedirs("data", exist_ok=True)

    # start odop and run the simulation
    odop.start(run_name="heat_equation", config_file="odop_conf.yaml")
    main()
    odop.stop()

    print("Elapsed time:", time.time() - start_time)
