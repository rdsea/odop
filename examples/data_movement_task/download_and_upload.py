# An example task with parameters provided using an @odop decorator
#
# The implementation of the odop parameter is trivial here and only meant
# to get around the syntax error. Although I think we can expand it to
# implement the task reading functionality.

import os
import random
import shutil
import time

import odop


@odop.task(
    name="download",
    time="1m",
    memory="1G",
    priority=0,
    trigger=odop.Timer("1s"),
)
def download_task():
    """Example task that simulates downloading a data file"""
    print("Downloading data")

    # Before running the example program creates files to download
    # Check if there is a file left and if so, copy one to a data folder.
    remote_files = os.listdir("remote_unprocessed_folder")
    local_files = os.listdir("unprocessed_data")
    for file in remote_files:
        if file not in local_files:
            shutil.copy("remote_unprocessed_folder/" + file, "unprocessed_data/")
            time.sleep(1)
            break

    print("Download complete")


@odop.task(
    name="process",
    time="1m",
    memory="1G",
    priority=10,
    trigger=odop.FileIn("unprocessed_data"),
)
def process_task(filename):
    """Example task that simulates processing a downloaded data file"""
    print("Processing data")
    filename = os.path.basename(filename)

    # generate CPU load for 5 seconds
    start_time = time.time()
    sum = 0
    while time.time() - start_time < 5:
        r = random.random()
        sum += r
    print("random sum:", sum)

    shutil.copy("unprocessed_data/" + filename, "processed_data/")

    print("Processing complete")


@odop.task(
    name="upload",
    time="1m",
    memory="1G",
    priority=0,
    trigger=odop.FileIn("processed_data"),
)
def upload_task(filenames):
    """Example task that simulates uploading a processed data file"""
    print("Uploading data")
    file_path = filenames[0]
    filename = os.path.basename(file_path)

    # Before running the example program creates files to upload
    # Check if there is a file left and if so, copy one to a data folder.
    shutil.copy("processed_data/" + filename, "remote_processed_folder/")
    time.sleep(1)

    print("Upload complete")
