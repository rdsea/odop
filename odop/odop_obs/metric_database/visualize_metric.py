import json
from tinyflux import TinyFlux, Point, TimeQuery
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import yaml
from flatten_dict import flatten, unflatten


def revert_unit(unit_conversion, converted_report: dict):
    original_report = converted_report.copy()
    for key, value in converted_report.items():
        if "unit" in key:
            if "frequency" in key:
                for original_unit, converted_unit in unit_conversion[
                    "frequency"
                ].items():
                    if converted_unit == value:
                        original_report[key] = original_unit
                        break
            elif "mem" in key:
                for original_unit, converted_unit in unit_conversion["mem"].items():
                    if converted_unit == value:
                        original_report[key] = original_unit
                        break
            elif "cpu" in key:
                if "usage" in key:
                    for original_unit, converted_unit in unit_conversion["cpu"][
                        "usage"
                    ].items():
                        if converted_unit == value:
                            original_report[key] = original_unit
                            break
            elif "gpu" in key:
                if "usage" in key:
                    for original_unit, converted_unit in unit_conversion["gpu"][
                        "usage"
                    ].items():
                        if converted_unit == value:
                            original_report[key] = original_unit
                            break
    return original_report


unit_conversion = yaml.safe_load(open("../config/unit_conversion.yaml"))
db = TinyFlux("./db.csv")
time_query = TimeQuery()
now = datetime.now()
data = db.all()
converted_process_data = []
converted_system_data = []
for datapoint in data:
    if datapoint.tags["type"] == "process":
        converted_datapoint = {
            **datapoint.tags,
            **datapoint.fields,
            "timestamp": datetime.timestamp(datapoint.time),
        }
        converted_datapoint = unflatten(
            revert_unit(unit_conversion, converted_datapoint), "dot"
        )
        converted_process_data.append(converted_datapoint)
    else:
        converted_datapoint = {
            **datapoint.tags,
            **datapoint.fields,
            "timestamp": datetime.timestamp(datapoint.time),
        }
        converted_datapoint = unflatten(
            revert_unit(unit_conversion, converted_datapoint), "dot"
        )
        converted_system_data.append(converted_datapoint)
# with open("./resources_usage.json", "w", encoding="utf-8") as file:
#    json.dump(converted_data, file)
timestamps = []
cpu_values = []
allowed_cpu_values = {}
mem_rss_values = []
mem_vms_values = []

allowed_memory_size = -1
for process_entry, system_entry in zip(converted_process_data, converted_system_data):
    timestamps.append(process_entry["timestamp"])
    cpu_values.append(process_entry["cpu"]["usage"]["total"])
    mem_rss_values.append(process_entry["mem"]["usage"]["rss"]["value"])
    mem_vms_values.append(process_entry["mem"]["usage"]["vms"]["value"])
    cpu_allowed_list = process_entry["metadata"]["allowed_cpu_list"]
    system_cpu = system_entry["cpu"]["usage"]["value"]
    allowed_memory_size = process_entry["metadata"]["allowed_memory_size"]
    for key in list(system_cpu.keys()):
        if key.split("_")[1] in cpu_allowed_list:
            if key in allowed_cpu_values:
                allowed_cpu_values[key] = allowed_cpu_values[key] + [system_cpu[key]]
            else:
                allowed_cpu_values[key] = [system_cpu[key]]

# Calculate the differences
cpu_diff = np.diff(cpu_values)
timestamps = np.array(timestamps)
timestamps = timestamps - timestamps[0]

fig, ax1 = plt.subplots(figsize=(10, 5))

# Plot cpu_diff on the first y-axis
ax1.plot(timestamps[1:], cpu_diff)

ax1.set_xlabel("Timestamp")
ax1.set_ylabel("Cputime over 1 second")
ax1.set_title("Cputime of process over time")

# Create a second y-axis
ax2 = ax1.twinx()

# Plot allowed_cpu_values on the second y-axis
for core in allowed_cpu_values.keys():
    ax2.plot(
        timestamps[1:],
        allowed_cpu_values[core][1:],
        label=f"{core}",
        linestyle="--",
    )

ax2.set_ylabel("CPU Utilization Percentage")

# Display grid and legend
ax1.grid(True)
ax2.legend(loc="lower left")
plt.savefig("process_resources_usage.png")

fig, ax1 = plt.subplots(figsize=(10, 5))

ax1.plot(timestamps, mem_rss_values)
allowed_memory_size = float(allowed_memory_size) / 1024.0 / 1024.0
plt.axhline(allowed_memory_size, color="r")  # vertical
ax1.set_xlabel("Timestamp")
ax1.set_ylabel("RSS in Mb")
ax1.set_title("Process memory usage over time")
plt.savefig("memory_usage.png")
plt.show()
