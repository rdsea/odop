#!/bin/bash

# Define your new values
NEW_TASK_FOLDER="./my_custom_task"
NEW_CONFIG_FILE="/users/myuser/.odop/my_custom_conf.yaml"

# Update the script file
sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$NEW_TASK_FOLDER\"|" script.py
sed -i "s|config_file=\"[^\"]*\"|config_file=\"$NEW_CONFIG_FILE\"|" script.py

echo "Updated script.py with task_folder=$NEW_TASK_FOLDER and config_file=$NEW_CONFIG_FILE"

rm ./reduced_data
