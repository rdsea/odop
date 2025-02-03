import logging
import os
import time

from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject

import odop

logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("swiftclient").setLevel(logging.CRITICAL)


@odop.task(
    name="Upload_data_to_allas",
    trigger="file_in_folder",
    folder_path="/users/anhdungn/pencil-code2/samples/gputest/data/proc0",
)
def upload_folder(filenames):
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

        upload_objects = []
        for file in filenames:
            upload_objects.append(
                SwiftUploadObject(
                    source=file,
                    object_name=f"{file}_{timestamp}",
                )
            )

        try:
            for result in swift.upload(bucket_name, upload_objects):
                if result["success"]:
                    print("Uploaded successfully.")
                else:
                    print("Failed to upload file")
        except SwiftError as e:
            print(f"Error during upload: {e.value}")


if __name__ == "__main__":
    base_path = "/users/anhdungn/pencil-code2/samples/gputest/data"
    test = [
        f"{base_path}/proc0/VAR0",
        f"{base_path}/proc0/var.dat",
        f"{base_path}/proc0/VAR0",
    ]
    upload_folder(test)
