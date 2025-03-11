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

METRICS_TAR_FILENAME = "metrics.tar.gz"
RECORD_INFO_FILENAME = "info.json"

logger = create_logger("benchmark", logging.ERROR)


def _check_uuid(id) -> bool:
    try:
        uuid.UUID(str(id))
    except ValueError:
        return False

    return True


# TODO: Cleanup the in-progress benchmark directory in case there was a problem during the process.
def _process_run_metrics(metrics_path: pathlib.Path, output_path: pathlib.Path):
    """
    Read all metrics and re-save by adding a new tag that identifies the machine where the measurement was taken. If
    there are too many, split them across multiple files ordered by the time of measurements.

    """
    logger.info("Merging run metric databases into a single stream.")

    if not metrics_path.is_dir():
        raise FileNotFoundError(f"Metrics directory {metrics_path} does not exist.")

    if not output_path.is_dir():
        raise FileNotFoundError(f"Output directory {output_path} does not exist.")

    if not os.access(output_path, os.W_OK | os.X_OK):
        raise PermissionError(f"Output directory {output_path} is not writeable.")

    max_records_in_db = 100000

    def create_db(time: datetime.datetime) -> tinyflux.TinyFlux:
        time_str = time.strftime("%s")
        db_path = output_path / f"metrics-{time_str}.csv"
        return tinyflux.TinyFlux(db_path), db_path

    metric_files = list(
        filter(lambda p: p.is_file() and p.suffix == ".csv", metrics_path.iterdir())
    )

    # Merge the per-node metric file into a single ordered time-series database. Only if the number of records starts
    # exceeding a certain threshold, create a new DB which will contain entries from a specific timestamp.
    db: tinyflux.TinyFlux = None
    db_path: pathlib.Path = None

    run_metrics_dbs: list[tinyflux.TinyFlux] = [
        iter(tinyflux.TinyFlux(path)) for path in metric_files
    ]
    with tarfile.open(output_path / METRICS_TAR_FILENAME, "w:gz") as tar:
        it = heapq.merge(*run_metrics_dbs, key=lambda point: point.time)
        for point in it:
            if db is None:
                db, db_path = create_db(point.time)

            if len(db) >= max_records_in_db:
                # Store the now saturated database in the compressed tarball.
                tar.add(db_path)
                db_path.unlink()

                db, db_path = create_db(point.time)

            # TODO: Add node identifier to the point
            db.insert(point)

        # There is always at least one database left.
        tar.add(db_path)
        db_path.unlink()


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
        self._metrics_path: pathlib.Path = self._path / METRICS_TAR_FILENAME

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

    @classmethod
    def from_run(cls, run_path: pathlib.Path) -> BenchmarkRecord:
        """

        Returns:

        Raises:
        """
        run_name: str = run_path.name

        if not run_path.is_dir():
            logger.errorf("Run directory {run_path} does not exist.")
            raise FileNotFoundError

        logger.info(f"Creating a new benchmark record from run {run_name}.")

        # Create an identifier and prepare a directory for the benchmark record data.
        # In case the identifier is not unique, try again with a new one.
        while True:
            id = str(uuid.uuid4())

            record_path: pathlib.Path = ODOP_BENCHMARKS_PATH / id
            try:
                record_path.mkdir(0o755, True, False)
            except FileExistsError:
                continue

            break

        # Populate the info file of the record.
        info = {
            "run_name": run_name,
        }

        record_info_path: pathlib.Path = record_path / RECORD_INFO_FILENAME
        with open(record_info_path, "w+") as f:
            json.dump(info, f)

        # Archive the odop_conf.yaml used in the run.
        odop_conf_src_path: pathlib.Path = run_path / ODOP_CONF_FILENAME
        if odop_conf_src_path.is_file():
            odop_conf_dst_path: pathlib.Path = record_path / ODOP_CONF_FILENAME
            shutil.copy2(odop_conf_src_path, odop_conf_dst_path)
        else:
            logger.warning(
                f"The {run_path} directory does not contain the {ODOP_CONF_FILENAME} used in the run. It cannot be included with the benchmark."
            )

        # TODO: How to capture the environment information? Should this already be marked down by the OdopObs since it
        # tracks it?

        # Find and merge the node-specific metrics into a single time-ordered stream.
        metrics_path: pathlib.Path = run_path / "metric_database"
        try:
            _process_run_metrics(metrics_path, record_path)
        except:
            raise

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
