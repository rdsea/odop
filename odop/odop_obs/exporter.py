from multiprocessing import Process
from fastapi import FastAPI
import uvicorn
from node_aggregator import NodeAggregator


class Exporter:
    def __init__(self, unit_conversion_config) -> None:
        self.app = FastAPI()
        self.node_aggregator = NodeAggregator({}, unit_conversion_config)
        self.app.include_router(self.node_aggregator.router)
        self.server_process = Process(target=self.run_server, args=[self.app])

    def start(self):
        self.node_aggregator.start()
        self.server_process.start()

    def run_server(self, app):
        uvicorn.run(app, host="127.0.0.1", port=8000)

    def stop(self):
        self.server_process.terminate()
