from pydantic import BaseModel 
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
