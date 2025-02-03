import argparse
import importlib
import multiprocessing
import os
import pathlib
import socket
import time
from typing import Optional

from qoa4ml.config.configs import OdopObsConfig
from qoa4ml.connector.socket_connector import SocketConnector
from qoa4ml.observability.odop_obs.exporter import Exporter
from qoa4ml.probes.process_monitoring_probe import ProcessMonitoringProbe
from qoa4ml.probes.system_monitoring_probe import SystemMonitoringProbe

from odop.common import ODOP_PATH


class OdopObs:
    def __init__(
        self,
        run_folder: str,
        is_master: bool,
        config: Optional[dict] = None,
        config_path: Optional[str] = None,
    ) -> None:
        if config_path:
            with open(config_path, encoding="utf-8") as file:
                yaml = importlib.import_module("yaml")
                self.config = OdopObsConfig(**yaml.safe_load(file))
        elif config:
            self.config = OdopObsConfig(**config)
        else:
            config_path = os.path.join(ODOP_PATH, "odop_conf.yaml")
            with open(config_path, encoding="utf-8") as file:
                yaml = importlib.import_module("yaml")
                self.config = OdopObsConfig(**yaml.safe_load(file))

        self.run_folder = run_folder
        self.master_process_flag = is_master
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.process_probe_connector = SocketConnector(self.config.probe_connector)
        self.process_probe = ProcessMonitoringProbe(
            self.config.process, self.process_probe_connector
        )
        self.monitoring_process = multiprocessing.Process(target=self.start_monitoring)

    def start(self):
        self.monitoring_process.start()

    def start_monitoring(self):
        if not self.master_process_flag:
            self.process_probe.start_reporting(background=False)
        else:
            self.system_probe_connector = SocketConnector(self.config.probe_connector)
            self.system_probe = SystemMonitoringProbe(
                self.config.system, self.system_probe_connector
            )
            self.exporter = Exporter(
                self.config.exporter, pathlib.Path(self.run_folder)
            )
            self.process_probe.start_reporting()
            self.system_probe.start_reporting()
            self.exporter.start()

    def stop(self):
        self.server_socket.close()
        self.monitoring_process.terminate()


def do_something(n_times: int):
    test = 0
    for _ in range(1, n_times):
        test = 0
        for j in range(1, 2**24):
            test += j


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="config path", default="config/odop_conf.yaml"
    )
    args = parser.parse_args()
    config_file_path = args.config
    odop_obs = OdopObs(config_path=config_file_path)
    odop_obs.start()
    time.sleep(5)
    # n_times = 20
    # processes = [
    #     multiprocessing.Process(target=do_something, args=(n_times,)) for i in range(3)
    # ]
    # for process in processes:
    #     process.start()
    # do_something(n_times)
    # for process in processes:
    #     process.join()
    odop_obs.stop()
