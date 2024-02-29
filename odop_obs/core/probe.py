import math, logging
import time, json
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import requests, pickle, socket

from core.common import ODOP_PATH

logging.basicConfig(
    format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO
)
class Probe:
    __slots__ = [
        "config",
        "node_name",
        "frequency",
        "obs_service_url",
        "cpu_metadata",
        "gpu_metadata",
        "mem_metadata",
        "current_report",
        "execution_flag",
        "report_thread",
        "monitoring_service_url",
        "metrics",
        "report_url",
        "monitoring_interval",
        "logging_path",
        "max_latency",
    ]

    def __init__(self, config: dict) -> None:
        self.config = config
        self.frequency = self.config["frequency"]
        self.monitoring_interval = 1.0 / self.frequency
        self.execution_flag = False
        self.report_thread = None
        self.report_url = config["request_url"]
        self.logging_path = ODOP_PATH + config["logging_path"]
        self.current_report = {}
        self.max_latency = 0.0

    def register(self, cpu_metadata: dict, gpu_metadata: dict, mem_metadata: dict):
        cpu_metadata = cpu_metadata
        gpu_metadata = gpu_metadata
        mem_metadata = mem_metadata
        data = {
            "node_name": self.node_name,
            "metadata": {"cpu": cpu_metadata, "gpu": gpu_metadata, "mem": mem_metadata},
        }
        response = requests.post(self.obs_service_url, json=data)
        if response.status_code == 200:
            register_info = json.loads(response.text)
            self.monitoring_service_url = register_info["reportUrl"]
            self.metrics = register_info["metrics"]
            self.frequency = register_info["frequency"]
        else:
            raise Exception(f"Can't register probe {self.node_name}")

    def create_report(self):
        pass

    def reporting(self):
        current_time = time.time()
        time.sleep(math.ceil(current_time) - current_time)
        while self.execution_flag:
            start = time.time()
            self.create_report()
            self.send_report_socket(self.current_report)
            self.max_latency = max(time.time() - start, self.max_latency)
            time.sleep(round(time.time()) + self.monitoring_interval - self.max_latency - time.time())

    def start_reporting(self):
        self.execution_flag = True
        self.report_thread = Thread(target=self.reporting)
        self.report_thread.daemon = self.config["thread_daemon"]
        self.report_thread.start()

    def stop_reporting(self):
        self.execution_flag = False

    def send_report(self, report: dict):
        start = time.time()
        response = requests.post(self.report_url, json=report)
        print(f"Sending data latency {(time.time() - start)*1000}ms")

    def send_report_socket(self, report: dict):
        start = time.time()
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.config["aggregator_host"], self.config["aggregator_port"]))
            serialized_dict = pickle.dumps(report)
            client_socket.sendall(serialized_dict)
            client_socket.close()
        except ConnectionRefusedError:
            logging.error("Connection to aggregator refused")
        self.write_log(
            (time.time() - start) * 1000, self.logging_path + "report_latency.txt"
        )

    def write_log(self, latency, filepath: str):
        with open(filepath, "a") as file:
            # Append the number to the file
            file.write(str(latency) + "\n")
