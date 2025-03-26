import logging
import os
import time
from ctypes import CDLL

from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject

import odop

logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("swiftclient").setLevel(logging.CRITICAL)


NUM_NODE = 4


def get_upload_folder(folder_name):
    @odop.task(
        name=f"upload_data_to_allas_{folder_name}",
        trigger=odop.FileUpdated(
            f"/scratch/project_462000759/pencil-code2/samples/gputest/data/{folder_name}/var.dat"
        ),
        cpus=7,
    )
    def upload_folder(filenames=None):
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

        bucket_name = "odop-benchmark-num_node--1-task-splitted-round_robin"
        timestamp = int(time.time())
        with SwiftService(options=options) as swift:
            try:
                swift.post(container=bucket_name)
                print(f"Container '{bucket_name}' created or exists.")
            except SwiftError as e:
                print(f"Error creating container '{bucket_name}': {e.value}")
                return

            upload_objects = []
            folder = f"/scratch/project_462000759/pencil-code2/samples/gputest/data/{folder_name}"
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    upload_objects.append(
                        SwiftUploadObject(
                            source=file_path,
                            object_name=f"{file_path}_{timestamp}",
                        )
                    )

            try:
                for result in swift.upload(bucket_name, upload_objects):
                    if result["success"]:
                        pass
                    else:
                        print("Failed to upload file")
            except SwiftError as e:
                print(f"Error during upload: {e.value}")
        print("---------------------- DONE --------------------")

    return upload_folder


for proc_number in range(NUM_NODE * 8):
    get_upload_folder(f"proc{proc_number}")


def main():
    os.environ["LD_PRELOAD"] = ""
    odop.start(
        config_file="/users/anhdungn/.odop/round_robin/1_task/data_movement_splitted/odop_conf_1_task_data_movement_splitted_round_robin.yaml",
        task_folder="./opportunistic_task/1_task/data_movement_splitted",
    )

    so_file = "./src/libPC.so"
    my_funcs = CDLL(so_file)
    my_funcs.run_start()
    odop.stop()


if __name__ == "__main__":
    main()
