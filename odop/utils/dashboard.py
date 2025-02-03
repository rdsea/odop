import glob
import os
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from odop.cli.visualization.common import extract_data_from_file_path
from odop.common import ODOP_PATH


@st.cache_data()
def load_data(file_path):
    return extract_data_from_file_path(file_path)


def plot_monitoring_data_with_slider(timestamps, cpu_values, allowed_cpu_values):
    for i, (key, _values) in enumerate(sorted(cpu_values.items())):
        st.write(f"**{key} - CPU Busy Percentage Over Time**")

        timestamps[key] = np.array(timestamps[key])
        timestamps[key] -= timestamps[key][0]

        max_time = timestamps[key][-1]
        time_range = st.slider(
            "Select Time Range (seconds)",
            min_value=0.0,
            max_value=float(max_time),
            value=(0.0, float(max_time)),
            key=i,
        )

        mask = (timestamps[key] >= time_range[0]) & (timestamps[key] <= time_range[1])
        filtered_timestamps = timestamps[key][mask]

        data = {"Timestamp": filtered_timestamps}
        for core in allowed_cpu_values[key].keys():
            core_label = core.replace("_", " ")
            data[core_label] = np.array(allowed_cpu_values[key][core])[mask]

        df = pd.DataFrame(data)
        df.set_index("Timestamp", inplace=True)

        df = df.reset_index().melt("Timestamp", var_name="Core", value_name="CPU Usage")
        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("Timestamp:Q", title="Time (seconds)"),
                y=alt.Y("CPU Usage:Q", title="CPU Usage (%)"),
                color="Core:N",
            )
            .properties(width=700, height=400)
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)


base_runs_path = os.path.join(ODOP_PATH, "runs")
chosen_run = st.selectbox("Which run you want to see", os.listdir(base_runs_path))
node_to_choose = [
    Path(filepath).stem
    for filepath in glob.glob(
        os.path.join(base_runs_path, chosen_run, "metric_database/*.csv")
    )
]
chosen_node = st.selectbox(
    "Which node to use",
    node_to_choose,
)

timestamps, cpu_values, allowed_cpu_values = load_data(
    os.path.join(
        base_runs_path,
        chosen_run,
        "metric_database",
        f"{chosen_node}.csv",
    )
)

plot_monitoring_data_with_slider(timestamps, cpu_values, allowed_cpu_values)
