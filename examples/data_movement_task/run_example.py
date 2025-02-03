import os

import odop
import odop.simulation

if __name__ == "__main__":
    # Create 4 folders, "remote_unprocessed_folder", "unprocessed_data",
    # "processed_data" and "remote_processed_folder". The "remote_" folders
    # simulate a server we can download data from.
    #
    # There are 3 tasks in download_and_upload.py, "download", "process" and
    # "upload". Each of these copies a file from one folder to another.
    # in the end, each file should end up in the "remote_processed_folder".

    os.makedirs("remote_unprocessed_folder", exist_ok=True)
    os.makedirs("unprocessed_data", exist_ok=True)
    os.makedirs("processed_data", exist_ok=True)
    os.makedirs("remote_processed_folder", exist_ok=True)

    # delete any existing files in the folders
    for folder in [
        "remote_unprocessed_folder",
        "unprocessed_data",
        "processed_data",
        "remote_processed_folder",
    ]:
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))

    for i in range(30):
        with open(f"remote_unprocessed_folder/file_{i}.txt", "w") as f:
            f.write("This is a file")

    # Now run the simulation. Odop will run the tasks when resources
    # are available.
    odop.start(run_name="run_1", task_folder=".", config_file="../odop_conf.yaml")
    odop.simulation.simulate_cyclical_process()
    odop.stop()
