import yaml


def read_config(config_file):
    """Reads the configuration file"""
    with open(config_file) as f:
        config = yaml.safe_load(f)

    assert "runtime" in config, "runtime key not found in config file"
    obs_hostname = config["odop_obs"]["exporter"]["host"]
    obs_port = config["odop_obs"]["exporter"]["port"]
    config["runtime"]["obs_port"] = config["odop_obs"]["exporter"]["port"]
    config["runtime"]["odop_endpoint"] = f"http://{obs_hostname}:{obs_port}/metrics"
    config["runtime"]["scheduling_interval"] = config["runtime"].get("frequency", 1)
    return config
