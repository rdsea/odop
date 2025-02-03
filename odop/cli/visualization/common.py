from datetime import datetime

import numpy as np
import yaml
from flatten_dict import unflatten
from tinyflux import TinyFlux

from odop.common import ODOP_PATH


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


def extract_data(data):
    odop_obs_config = yaml.safe_load(open(f"{ODOP_PATH}/odop_conf.yaml"))
    unit_conversion = odop_obs_config["odop_obs"]["exporter"]["node_aggregator"][
        "unit_conversion"
    ]
    converted_process_data = {}
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
            pid = converted_datapoint["metadata"]["pid"]
            if pid in converted_process_data:
                converted_process_data[pid].append(converted_datapoint)
            else:
                converted_process_data[pid] = [converted_datapoint]
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
    timestamps = {}
    cpu_values = {}
    allowed_cpu_values = {}
    mem_rss_values = {}
    mem_vms_values = {}
    # print(f"System data length: {len(converted_system_data)} ")
    # for pid, value in converted_process_data.items():
    #     print(f"PID {pid} has {len(value)}")
    # allowed_memory_size = -1
    for pid in converted_process_data.keys():
        timestamps[pid] = []
        cpu_values[pid] = []
        allowed_cpu_values[pid] = {}
        mem_rss_values[pid] = []
        mem_vms_values[pid] = []
        for process_entry, system_entry in zip(
            converted_process_data[pid], converted_system_data
        ):
            timestamps[pid].append(process_entry["timestamp"])
            cpu_values[pid].append(process_entry["cpu"]["usage"]["total"])
            mem_rss_values[pid].append(process_entry["mem"]["usage"]["rss"]["value"])
            mem_vms_values[pid].append(process_entry["mem"]["usage"]["vms"]["value"])
            cpu_allowed_list = eval(process_entry["metadata"]["allowed_cpu_list"])
            # cpu_allowed_list = cpu_allowed_list + [val + 64 for val in cpu_allowed_list]
            system_cpu = system_entry["cpu"]["usage"]["value"]
            # allowed_memory_size = process_entry["metadata"]["allowed_memory_size"]
            for key in list(system_cpu.keys()):
                if int(key.split("_")[1]) in cpu_allowed_list:
                    if key in allowed_cpu_values[pid]:
                        allowed_cpu_values[pid][key].append(
                            max(
                                system_cpu[key],
                                system_cpu["core_" + str(int(key.split("_")[1]) + 64)],
                            )
                        )
                    else:
                        allowed_cpu_values[pid][key] = [
                            max(
                                system_cpu[key],
                                system_cpu["core_" + str(int(key.split("_")[1]) + 64)],
                            )
                        ]

    # with open(f"./process_usage.json", "w", encoding="utf-8") as file:
    #     json.dump(converted_process_data, file)
    return timestamps, cpu_values, allowed_cpu_values


def average_tumbling_windows(data, window_size):
    num_windows = len(data)
    windows = []

    for i in range(0, num_windows, window_size):
        windows.append(np.average(data[i : (i + window_size)]))

    return windows


def plot_monitoring_data_window(
    axs, timestamps, cpu_values, allowed_cpu_values, window_size
):
    for i, (key, values) in enumerate(sorted(cpu_values.items())):
        cpu_diff = np.diff(values)
        cpu_diff = average_tumbling_windows(cpu_diff, window_size)
        timestamps[key] = np.array(timestamps[key])
        timestamps[key] = timestamps[key] - timestamps[key][0]
        row = i // 2
        col = i % 2
        axs[row, col].plot(
            timestamps[key][0 : len(cpu_diff)], cpu_diff, "b", label="process cputime"
        )
        axs[row, col].set_xlabel("Timestamp")
        axs[row, col].set_ylabel(f"Average Cputime over {window_size} second")
        axs[row, col].set_title("Cputime of process over time")
        ax2 = axs[row, col].twinx()

        for core in allowed_cpu_values[key].keys():
            ax2.plot(
                timestamps[key][0 : len(cpu_diff)],
                average_tumbling_windows(
                    allowed_cpu_values[key][core][1:], window_size
                ),
                label=f"{core} util",
                linestyle="--",
            )

        ax2.set_ylabel("CPU Utilization Percentage")
        ax2.legend(loc="lower left")
        lines, labels = axs[row, col].get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc="best")


def plot_monitoring_data(axs, timestamps, cpu_values, allowed_cpu_values):
    for i, (key, values) in enumerate(sorted(cpu_values.items())):
        print(key, len(values))
        np.diff(values)
        timestamps[key] = np.array(timestamps[key])
        timestamps[key] = timestamps[key] - timestamps[key][0]
        row = i // 2
        col = i % 2
        # axs[row, col].plot(timestamps[key][1:], cpu_diff, "b", label="process cputime")
        axs[row, col].set_xlabel("Timestamp")
        # axs[row, col].set_ylabel("Cputime over 1 second")
        # axs[row, col].set_title("Cputime of process over time")
        # ax2 = axs[row, col].twinx()
        axs[row, col].set_yticks([0, 25, 50, 75, 100])
        for core in allowed_cpu_values[key].keys():
            print(core, len(allowed_cpu_values[key][core]))
            _core = core.replace("_", " ")
            axs[row, col].plot(
                timestamps[key][1:],
                allowed_cpu_values[key][core][1:],
                label=f"{_core} busy",
                linestyle="--",
            )

        axs[row, col].set_ylabel("CPU Busy Percentage")
        axs[row, col].legend(loc="best")
        # lines, labels = axs[row, col].get_legend_handles_labels()
        # lines2, labels2 = ax2.get_legend_handles_labels()
        # ax2.legend(lines + lines2, labels + labels2, loc="best")
        #


def extract_data_from_file_path(file_path: str):
    db = TinyFlux(file_path)
    data = db.all()
    return extract_data(data)
