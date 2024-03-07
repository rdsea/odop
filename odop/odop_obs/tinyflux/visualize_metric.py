from tinyflux import TinyFlux, Point, TimeQuery
import time
import json
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
timestamp = now - timedelta(hours=10)
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
with open("./mahti.json", "w", encoding="utf-8") as file:
    json.dump(converted_data, file)
timestamps = []
cpu_values = []
mem_rss_values = []
mem_vms_values = []

for entry in converted_data:
    timestamps.append(
        entry["timestamp"]
    )  # Assuming there's a "timestamp" field in each entry
    cpu_values.append(entry["cpu"]["usage"]["total"])
    mem_rss_values.append(entry["mem"]["usage"]["rss"]["value"])
    mem_vms_values.append(entry["mem"]["usage"]["vms"]["value"])

plt.figure(figsize=(10, 5))
plt.plot(timestamps, cpu_values, marker="o", color="b", label="CPU Usage")
plt.xlabel("Timestamp")
plt.ylabel("CPU Usage (%)")
plt.title("CPU Usage Over Time")
plt.grid(True)
plt.legend()
plt.show()

# Plotting Memory Usage
plt.figure(figsize=(10, 5))
plt.plot(timestamps, mem_rss_values, marker="o", color="r", label="RSS Memory Usage")
plt.plot(timestamps, mem_vms_values, marker="o", color="g", label="VMS Memory Usage")
plt.xlabel("Timestamp")
plt.ylabel("Memory Usage (MB)")
plt.title("Memory Usage Over Time")
plt.grid(True)
plt.legend()
plt.show()
