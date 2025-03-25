#!/bin/bash

NUM_NODE=4
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

  mv reduced_data "reduced_data_${NUM_NODE}_1_task_${algo}"
  mkdir reduced_data
done

# 1 task data movement splitted
#
for algo in "${algorithms[@]}"; do
  TASK_FOLDER="./opportunistic_task/0_task/"
  CONFIG_FILE="/users/anhdungn/.odop/${algo}/1_task/data_movement_splitted/odop_conf_1_task_data_movement_splitted_${algo}.yaml"
  BUCKET_NAME="odop-benchmark-num_node-${NUM_NODE}-1-task-splitted-${algo}"

  # Update the script file
  sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call_splitted.py
  sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call_splitted.py

  # Update bucket to move data to
  sed -i "s|bucket_name = \"[^\"]*\"|bucket_name = \"$BUCKET_NAME\"|" "call_splitted.py"

  # Update number of node
  sed -i "s|NUM_NODE = \"[^\"]*\"|NUM_NODE = \"$NUM_NODE\"|" "call_splitted.py"

  echo "Updated script"

  sbatch --wait python-dispatch-splitted.sh
done

#  2 tasks
for algo in "${algorithms[@]}"; do
  echo "[Processing reduce and data movement task for algorithm: $algo"
  TASK_FOLDER="./opportunistic_task/2_tasks"
  CONFIG_FILE="/users/anhdungn/.odop/${algo}/2_tasks/odop_conf_2_tasks_${algo}.yaml"

  BUCKET_NAME="odop-benchmark-num_nodes-${NUM_NODE}-2-tasks-${algo}"

  # Update the script file
  sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call_splitted.py
  sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call_splitted.py

  # Update bucket to move data to
  sed -i "s|bucket_name = \"[^\"]*\"|bucket_name = \"$BUCKET_NAME\"|" "call_splitted.py"

  echo "Updated script"

  mkdir -p reduced_data
  sbatch --wait python-dispatch.sh

  mv reduced_data "reduced_data_${NUM_NODE}_2_tasks_${algo}"
  mkdir reduced_data
done

# No optask
echo "[No optask"
TASK_FOLDER="./opportunistic_task/0_task"
CONFIG_FILE="/users/anhdungn/.odop/no_optask.yaml"

# Update the script file
sed -i "s|task_folder=\"[^\"]*\"|task_folder=\"$TASK_FOLDER\"|" call.py
sed -i "s|config_file=\"[^\"]*\"|config_file=\"$CONFIG_FILE\"|" call.py

echo "Updated script"

sbatch --wait python-dispatch.sh

mv ~/.odop/runs ~/.odop/runs_${NUM_NODE}
