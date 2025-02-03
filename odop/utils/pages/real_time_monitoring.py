import glob
import os
import time
from pathlib import Path

import requests
import streamlit as st
import yaml

from odop.common import ODOP_PATH, create_logger

logger = create_logger("monitoring")


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

chosen_run = st.selectbox("Which run you want to monitor", run_paths)

node_names = list(
    glob.glob(os.path.join(base_runs_path, chosen_run, "metric_database/*.csv"))
)
node_to_choose = [
    Path(filepath).stem
    for filepath in glob.glob(
        os.path.join(base_runs_path, chosen_run, "metric_database/*.csv")
    )
]
node_to_choose.sort()
chosen_node = st.selectbox(
    "Which node to monitor",
    node_to_choose,
)
test = []
if "df" not in st.session_state:
    st.session_state.df = {}

monitoring = st.toggle("Start monitoring")

if monitoring:
    monitoring_data = query_data(chosen_node)
    node_data = {}
    process_data = {}
    has_node_data = False
    for data_point in monitoring_data:
        if data_point["type"] == "node":
            node_data = data_point["cpu"]["usage"]["value"]
            has_node_data = True
        else:
            process_metadata = data_point["metadata"]
            process_data[process_metadata["pid"]] = eval(
                process_metadata["allowed_cpu_list"]
            )
    if has_node_data:
        for pid, allowed_cpu_list in process_data.items():
            if pid not in st.session_state.df.keys():
                st.session_state.df[pid] = {}
            for core_id in allowed_cpu_list:
                if core_id not in st.session_state.df[pid].keys():
                    st.session_state.df[pid][core_id] = []
                st.session_state.df[pid][core_id].append(node_data[f"core_{core_id}"])
    else:
        logger.info(f"{int(time.time())}: No node data")
    # st.write(st.session_state.df)
df = st.session_state.df
pids = list(df.keys())
pids.sort()
for pid in pids:
    st.title(f"PID {pid}")
    st.line_chart(df[pid], width=800, height=400)
time.sleep(1)
st.rerun()
