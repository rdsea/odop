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
converted_data = []
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
        converted_data.append(converted_datapoint)
timestamps = []
cpu_values = []
mem_rss_values = []
mem_vms_values = []

for entry in converted_data:
    timestamps.append(entry["timestamp"])
    cpu_values.append(entry["cpu"]["usage"]["total"])
    mem_rss_values.append(entry["mem"]["usage"]["rss"]["value"])
    mem_vms_values.append(entry["mem"]["usage"]["vms"]["value"])

# Calculate the differences
cpu_diff = np.diff(cpu_values)
timestamps = np.array(timestamps)
timestamps = timestamps - timestamps[0]

plt.figure(figsize=(10, 5))
plt.plot(
    timestamps[1:],
    cpu_diff,
    marker="o",
    color="r",
)
plt.xlabel("Timestamp")
plt.ylabel("Cputime over 1 second")
plt.title("Cputime of process over time")
plt.grid(True)
plt.legend()
plt.show()
