import os

import matplotlib.pyplot as plt
from tinyflux import TinyFlux

from .common import extract_data, plot_monitoring_data


def render_monitoring_data(file_path: str, file_name: str, folder_path: str):
    db = TinyFlux(file_path)
    data = db.all()
    # with open(f"./{file_name}.json", "w", encoding="utf-8") as file:
    #     json.dump(converted_system_data, file)
    timestamps, cpu_values, allowed_cpu_values = extract_data(data)

    fig, axs = plt.subplots(4, 2)
    fig.set_figheight(20)
    fig.set_figwidth(50)
    # plot_monitoring_data_window(axs, timestamps, cpu_values, allowed_cpu_values, 3)
    plot_monitoring_data(axs, timestamps, cpu_values, allowed_cpu_values)
    plt.tight_layout()
    plt.savefig(f"./{folder_path}/{file_name}_busy.png", bbox_inches="tight", dpi=500)


def process_folder(folder_path):
    files = sorted(os.listdir(folder_path))
    for file in files:
        if file.endswith(".csv"):  # Check if the file has a .csv extension
            file_path = os.path.join(folder_path, file)
            render_monitoring_data(file_path, file.split(".")[0], folder_path)
