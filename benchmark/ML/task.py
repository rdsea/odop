import logging
import os
import time

import pandas as pd
from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject

import odop

logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("swiftclient").setLevel(logging.CRITICAL)


model_path = os.getenv("MODEL_PATH")
assert type(model_path) is str


@odop.task(name="Upload_model_to_allas", trigger=odop.FileIn(model_path), replicas=1)
def upload_folder(filename):
    """Upload the model"""
    options = {
        "auth_version": os.getenv("OS_IDENTITY_API_VERSION"),
        "user": os.getenv("OS_USERNAME"),
        "key": os.getenv("OS_PASSWORD"),
        "authurl": os.getenv("OS_AUTH_URL"),
        "os_options": {
            "user_domain_name": os.getenv("OS_USER_DOMAIN_NAME"),
            "project_domain_name": os.getenv("OS_PROJECT_DOMAIN_NAME"),
            "project_name": os.getenv("OS_PROJECT_NAME"),
        },
    }

    bucket_name = "2009846-folder"
    timestamp = int(time.time())
    with SwiftService(options=options) as swift:
        try:
            swift.post(container=bucket_name)
            print(f"Container '{bucket_name}' created or exists.")
        except SwiftError as e:
            print(f"Error creating container '{bucket_name}': {e.value}")
            return

        upload_objects = [
            SwiftUploadObject(
                source=filename,
                object_name=f"{filename}_{timestamp}",
            )
        ]

        try:
            for result in swift.upload(bucket_name, upload_objects):
                if result["success"]:
                    print("Uploaded successfully.")
                else:
                    print("Failed to upload file")
        except SwiftError as e:
            print(f"Error during upload: {e.value}")


@odop.task(
    name="Data processing", trigger=odop.FileIn("unprocessed_data"), cpus=2, replicas=1
)
def process_data(filenames):
    """Additional data processing task that would trigger on files unrelated to the main task.

    This is unlikely to trigger, since
    the training task should reserve all CPUs, and exists mainly
    for benchmarking."""
    for filename in filenames:
        try:
            data = pd.read_csv(filename)
            mean = data.mean()
            output_path = filename.replace("unprocessed_data", "processed_data")
            output_path = output_path.replace(".csv", ".txt")
            with open(output_path, "w") as f:
                f.write(f"Mean: {mean}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")


if __name__ == "__main__":
    files = os.listdir(model_path)
    upload_folder(files)
