import os
import logging
import json
from typing import Optional
from pydantic import BaseModel

ODOP_PATH = os.getenv("ODOP_PATH")
if not ODOP_PATH:
    logging.error("No ODOP_PATH environment variable")


class ProcessMetadata(BaseModel):
    pid: str
    user: str


class SystemMetadata(BaseModel):
    node_name: str


class ResourceReport(BaseModel):
    metadata: Optional[dict] = None
    usage: dict


class ProcessReport(BaseModel):
    metadata: ProcessMetadata
    timestamp: float
    cpu: ResourceReport
    gpu: Optional[ResourceReport] = None
    mem: ResourceReport


class SystemReport(BaseModel):
    metadata: SystemMetadata
    timestamp: float
    cpu: ResourceReport
    gpu: Optional[ResourceReport] = None
    mem: ResourceReport

