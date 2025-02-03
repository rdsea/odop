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
    ODOP_PATH = os.path.join(user_home, ".odop")
    os.makedirs(ODOP_PATH, exist_ok=True)

RUN_ID = os.getenv("RUN_ID")
