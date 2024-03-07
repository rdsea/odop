import argparse
import yaml
from odop.odop_obs.odop_obs import OdopObs
from odop.odop_obs.core.common import ODOP_PATH

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="config path", default="config/odop_obs_conf.yaml"
    )
    args = parser.parse_args()
    config_file = args.config
    config = yaml.safe_load(open(ODOP_PATH + config_file))
    odop_obs = OdopObs(config)
    try:
        odop_obs.start()
    except KeyboardInterrupt:
        odop_obs.stop()
