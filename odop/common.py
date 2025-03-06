import logging
import os
from pathlib import Path

LARGE_INT = 100000


def create_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s -- %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = create_logger("odop")

try:
    ODOP_PATH = os.getenv("ODOP_PATH")
except KeyError:
    logger.info("ODOP_PATH not sent. Defaulting to ~/.odop")
    ODOP_PATH = None

if ODOP_PATH is None:
    user_home = Path.home()
    # assume that we have odop dir
    ODOP_PATH = user_home / ".odop"
else:
    ODOP_PATH = Path(ODOP_PATH)

if not ODOP_PATH.is_dir():
    os.makedirs(ODOP_PATH, exist_ok=True)

RUN_ID = os.getenv("RUN_ID")

ODOP_RUNS_PATH = ODOP_PATH / "runs"

def get_runs() -> list[Path]:
    runs = []

    logger.info(f"Collecting runs from {ODOP_RUNS_PATH}.")

    if not ODOP_RUNS_PATH.is_dir():
        logger.info("The runs directory does not exist.")
        return runs

    for path in ODOP_RUNS_PATH.iterdir():
        if not path.is_dir():
            logger.debug(f"{path} is not a directory. Ignoring it.")
            continue

        runs.append(path)

    return sorted(runs)
