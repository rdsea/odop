import multiprocessing, subprocess, os
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
        self.system_probe.start_reporting()
        self.process_probe.start_reporting()
        self.exporter.start()

    def stop(self):
        self.process_probe.stop_reporting()
        self.system_probe.stop_reporting()
        self.exporter.stop()
