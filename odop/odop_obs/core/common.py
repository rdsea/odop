import logging
import os

ODOP_PATH = os.getenv("ODOP_PATH")
if not ODOP_PATH:
    logging.error("No ODOP_PATH environment variable")
