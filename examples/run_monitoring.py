import argparse

import yaml

from odop.common import ODOP_PATH
from odop.odop_obs import OdopObs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="config path", default="odop_conf.yaml")
    args = parser.parse_args()
    with open(ODOP_PATH / args.config) as config_file:
        config = yaml.safe_load(config_file)
    odop_obs = OdopObs(config)
    try:
        odop_obs.start()
    except KeyboardInterrupt:
        odop_obs.stop()
