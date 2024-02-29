from fastapi import FastAPI
import uvicorn
from node_aggregator import NodeAggregator


class Exporter:
    def __init__(self, unit_conversion_config) -> None:
        self.app = FastAPI()
        self.node_aggregator = NodeAggregator({}, unit_conversion_config)
        self.app.include_router(self.node_aggregator.router)

    def start(self):
        self.node_aggregator.start()
        uvicorn.run(self.app, host="127.0.0.1", port=8000)

