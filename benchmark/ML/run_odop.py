import os
import time

import odop

if __name__ == "__main__":
    odop.start(run_name="ML_benchmark", config_file="odop_conf.yaml")
    signal_file = os.path.join("signal", "stop")
    while not os.path.exists(signal_file):
        time.sleep(1)
    odop.stop()
