import os
from pathlib import Path

import requests
import streamlit as st
import yaml

from odop.common import ODOP_PATH


def query_data(hostname: str) -> list[dict]:
    response = requests.get(f"http://{hostname}:8001/metrics")
    resources = response.json()
    return resources


def filter_run_dir(run_paths: list[str]):
    return run_paths


@st.cache_data()
def get_config_data(run_path: str):
    config_path = os.path.join(run_path, "odop_conf.yaml")
    if os.path.exists(Path(config_path)):
        with open(config_path) as file:
            return yaml.safe_load(file)
    else:
        return None


base_runs_path = os.path.join(ODOP_PATH, "runs")

run_paths = os.listdir(base_runs_path)
run_paths = filter_run_dir(run_paths)
run_paths.sort()

chosen_run = st.selectbox("Which run you want to check", run_paths)
