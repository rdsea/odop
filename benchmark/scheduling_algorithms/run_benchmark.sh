#!/bin/bash

# Define your new values
algorithms=("best_fit" "priority" "fifo" "round_robin")

# 1 task reduce task
for algo in "${algorithms[@]}"; do
  echo "[Processing reduce task for algorithm: $algo"
  TASK_FOLDER="./opportunistic_task/1_task/reduce"
  CONFIG_FILE="/users/anhdungn/.odop/${algo}/1_task/reduce/odop_conf_1_task_reduce_${algo}.yaml"

  # Update the script file
  sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call.py
  sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call.py

  echo "Updated script"

  mkdir -p reduced_data
  sbatch --wait python-dispatch.sh

  mv reduced_data "reduced_data_1_task_${algo}"
  mkdir reduced_data
done

# 1 task data movement
for algo in "${algorithms[@]}"; do
  echo "[Processing data movement task for algorithm: $algo"
  TASK_FOLDER="./opportunistic_task/1_task/data_movement"
  CONFIG_FILE="/users/anhdungn/.odop/${algo}/1_task/data_movement/odop_conf_1_task_data_movement_${algo}.yaml"
  BUCKET_NAME="odop-benchmark-1-task-${algo}"

  # Update the script file
  sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call.py
  sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call.py

  # Update bucket to move data to
  sed -i "s|bucket_name = \"[^\"]*\"|bucket_name = \"$BUCKET_NAME\"|" "${TASK_FOLDER}/upload_data.py"

  echo "Updated script"

  cat "${TASK_FOLDER}/upload_data.py"

  sbatch --wait python-dispatch.sh
done

# 1 task data movement splitted
for algo in "${algorithms[@]}"; do
  TASK_FOLDER="./opportunistic_task/1_task/data_movement_splitted"
  CONFIG_FILE="/users/anhdungn/.odop/${algo}/1_task/odop_conf_1_task_data_movement_splitted_${algo}.yaml"
  BUCKET_NAME="odop-benchmark-1-task-splitted-${algo}"

  # Update the script file
  sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call.py
  sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call.py

  # Update bucket to move data to
  sed -i "s|bucket_name = \"[^\"]*\"|bucket_name = \"$BUCKET_NAME\"|" "${TASK_FOLDER}/upload_data_splitted.py"

  echo "Updated script"

  sbatch --wait python-dispatch.sh
done

#  2 tasks
for algo in "${algorithms[@]}"; do
  echo "[Processing reduce and data movement task for algorithm: $algo"
  TASK_FOLDER="./opportunistic_task/2_tasks"
  CONFIG_FILE="/users/anhdungn/.odop/${algo}/2_tasks/odop_conf_2_tasks_${algo}.yaml"

  BUCKET_NAME="odop-benchmark-2-tasks-${algo}"

  # Update the script file
  sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call.py
  sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call.py

  # Update bucket to move data to
  sed -i "s|bucket_name = \"[^\"]*\"|bucket_name = \"$BUCKET_NAME\"|" "${TASK_FOLDER}/upload_data.py"

  echo "Updated script"

  mkdir -p reduced_data
  sbatch --wait python-dispatch.sh

  mv reduced_data "reduced_data_2_tasks_${algo}"
  mkdir reduced_data
done
