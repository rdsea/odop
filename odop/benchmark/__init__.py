#!/bin/python3

from __future__ import annotations

import contextlib
import datetime
import heapq
import json
import logging
import os
import pathlib
import shutil
import tarfile
import uuid

import click
import tinyflux

from odop.common import ODOP_CONF_FILENAME, ODOP_PATH, ODOP_RUNS_PATH, create_logger
from odop.ui import read_config

ODOP_BENCHMARKS_PATH = ODOP_PATH / "benchmarks"

RECORD_INFO_FILENAME = "info.json"

logger = create_logger("benchmark", logging.ERROR)


def _check_uuid(id) -> bool:
    try:
        uuid.UUID(str(id))
    except ValueError:
        return False

    return True


# id
# run_name
# ODOP config
# Metrics (merged and compressed)
# Runtime environment dump
class BenchmarkRecord:
    def __init__(self, id: str):
        self.id: str = id

        self._path: pathlib.Path = ODOP_BENCHMARKS_PATH / self.id
        self._config_path: pathlib.Path = self._path / ODOP_CONF_FILENAME
        self._info_path: pathlib.Path = self._path / RECORD_INFO_FILENAME

        self._validate()

        with open(self._info_path) as f:
            with json.load(f) as info:
                self.run_name = info["run_name"]

    def _validate(self):
        if not self._path.is_dir():
            raise FileNotFoundError
        if not os.access(self._path, os.R_OK | os.W_OK | os.X_OK):
            raise PermissionError

        if not self._config_path.is_file():
            raise FileNotFoundError
        if not os.access(self._config_path, os.R_OK):
            raise PermissionError

        if not self._info_path.is_file():
            raise FileNotFoundError
        if not os.access(self._info_path, os.R_OK):
            raise PermissionError

    @classmethod
    def from_benchmark_record(cls, record_path: pathlib.Path) -> BenchmarkRecord:
        id = record_path.name
        if not _check_uuid(id):
            raise ValueError(f"{id} is not a valid UUID.")

        # TODO: Add parsing of info file

        return cls(id)


def get_benchmark_records() -> list[BenchmarkRecord]:
    records: list[BenchmarkRecord] = []

    logger.info(f"Collecting benchmark records from {ODOP_BENCHMARKS_PATH}.")

    if not ODOP_BENCHMARKS_PATH.is_dir():
        logger.info("The benchmarks directory does not exist.")
        return records

    for path in ODOP_BENCHMARKS_PATH.iterdir():
        if not path.is_dir():
            logger.debug(f"{path} is not a directory. Ignoring it.")
            continue

        record: BenchmarkRecord = BenchmarkRecord.from_benchmark_record(path)
        records.append(record)

    return records
