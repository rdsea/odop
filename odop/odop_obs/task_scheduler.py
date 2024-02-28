import requests
import time
import json, math

url = "http://127.0.0.1:8000/metrics"
interval = 1
json_filename = "latest_timestamp.json"

while True:
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(data)
        # with open(json_filename, 'w') as json_file:
        #    json.dump(data, json_file)
        #    print("Data written to", json_filename)
    else:
        print("Failed to retrieve latest timestamp. Status code:", response.status_code)

    time.sleep(1)
