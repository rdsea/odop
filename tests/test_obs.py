import os
import shutil
import time

from odop.common import ODOP_PATH
from odop.odop_obs import OdopObs
from odop.ui import read_config

N = 5000


def test_obs(runtime=1):
    config = read_config(os.path.join("tests", "odop_conf.yaml"))
    obs_config = config.get("odop_obs")
    run_folder = os.path.join(ODOP_PATH, ".test")
    odop_obs = OdopObs(run_folder=run_folder, is_master=True, config=obs_config)
    odop_obs.start()
    start_time = time.time()
    while time.time() - start_time < runtime:
        sum = 0
        for i in range(10**8):
            sum += i
    odop_obs.stop()
    shutil.rmtree(run_folder)


if __name__ == "__main__":
    test_obs(N)
