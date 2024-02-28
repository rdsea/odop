import math
import socket
import pickle
from threading import Thread
import time

import yaml
from pydantic import BaseModel, ValidationError
from tinyflux.storages import MemoryStorage
from tinyflux import TinyFlux, Point, TimeQuery
from datetime import datetime
from fastapi import APIRouter, FastAPI
from flatten_dict import flatten, unflatten


class ProcessReport(BaseModel):
    metadata: dict
    timestamp: float
    usage: dict


class SystemReport(BaseModel):
    node_name: str
    timestamp: float
    cpu: dict
    gpu: dict
    mem: dict


class Request(BaseModel):
    timestamp: float


class NodeAggregator:
    def __init__(self, config, unit_conversion):
        self.config = config
        self.unit_conversion = unit_conversion
        # self.db = TinyFlux(storage=MemoryStorage)
        self.db = TinyFlux("./db.csv")
        self.last_timestamp = time.time()
        self.server_thread = Thread(
            target=self.start_handling, args=("127.0.0.1", 12345)
        )
        self.server_thread.daemon = True
        self.started = False
        self.router = APIRouter()
        self.router.add_api_route(
            "/metrics", self.get_lastest_timestamp, methods=["GET"]
        )

    def insert_metric(self, timestamp: float, tags: dict, fields: dict):
        timestamp_datetime = datetime.fromtimestamp(timestamp)
        datapoint = Point(
            time=timestamp_datetime, tags=tags, fields=fields
        )
        self.db.insert(datapoint, compact_key_prefixes=True)

    def start_handling(self, host, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        while self.started:
            client_socket, addr = server_socket.accept()
            self.handle_client(client_socket)

    def handle_client(self, client_socket):
        data = b""
        while True:
            packet = client_socket.recv(4096)
            if not packet:
                break
            data += packet

        report_dict = pickle.loads(data)
        try:
            if "node_name" in report_dict:
                report = SystemReport(**report_dict)
            else:
                report = ProcessReport(**report_dict)
            self.process_report(report)
        except ValidationError as e:
            print("Validation error:", e)
        except Exception as e:
            print("Error processing report:", e)

        client_socket.close()

    def process_report(self, report):
        try:
            if isinstance(report, SystemReport):
                node_name = report.node_name
                timestamp = report.timestamp
                del report.node_name, report.timestamp
                fields = self.convert_unit(flatten(report.__dict__, "dot"))
                self.insert_metric(
                    timestamp,
                    {
                        "type": "node",
                        "node_name": node_name,
                    },
                    fields,
                )
            else:
                metadata = flatten({"metadata": report.metadata}, "dot")
                timestamp = report.timestamp
                del report.metadata, report.timestamp
                fields = self.convert_unit(flatten(report.__dict__, "dot"))
                self.insert_metric(timestamp, {"type": "process", **metadata}, fields)
        except Exception as e:
            print("Error processing report:", e)

    def convert_unit(self, report: dict):
        converted_report = report
        for key, value in report.items():
            if isinstance(value, str):
                if "frequency" in key:
                    converted_report[key] = self.unit_conversion["frequency"][value]
                elif "mem" in key:
                    converted_report[key] = self.unit_conversion["mem"][value]
                elif "cpu" in key:
                    if "usage" in key:
                        converted_report[key] = self.unit_conversion["cpu"]["usage"][
                            value
                        ]
                elif "gpu" in key:
                    if "usage" in key:
                        converted_report[key] = self.unit_conversion["gpu"]["usage"][
                            value
                        ]
        return converted_report

    def get_lastest_timestamp(self):
        time_query = TimeQuery()
        timestamp = datetime.fromtimestamp(math.floor(time.time()))
        data = self.db.search(
            time_query >= timestamp) 
        print(data)
        return [
            unflatten({**datapoint.tags, **datapoint.fields}, "dot")
            for datapoint in data
        ]

    def start(self):
        self.started = True
        self.server_thread.start()

    def stop(self):
        self.started = False
        self.server_thread.join()
