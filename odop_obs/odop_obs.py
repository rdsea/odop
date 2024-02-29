import multiprocessing, subprocess, os

import yaml
from process_monitoring_probe import ProcessMonitoringProbe
from system_monitoring_probe import SystemMonitoringProbe
from exporter import Exporter


class OdopObs:
    def __init__(self, config: dict) -> None:
        self.process_config = config["process"]
        self.system_config = config["system"]
        self.exporter_config = config["exporter"]
        self.process_probe = ProcessMonitoringProbe(self.process_config)
        self.system_probe = SystemMonitoringProbe(self.system_config)
        self.exporter = Exporter(self.exporter_config["unit_conversion"])


    def start(self):
        self.monitoring_process = multiprocessing.Process(target=self.start_monitoring)
        self.monitoring_process.start()

    def start_monitoring(self):
        self.system_probe.start_reporting()
        self.process_probe.start_reporting()
        self.exporter.start()

    def stop(self):
        self.process_probe.stop_reporting()
        self.system_probe.stop_reporting()
        self.monitoring_process.terminate()

if __name__ == "__main__":
    config = yaml.safe_load(open("./config/odop_obs_conf.yaml"))
    odop_obs = OdopObs(config)
    odop_obs.start()
