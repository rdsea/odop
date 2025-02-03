import glob
import json
import logging
import os
import re
import subprocess
import time
import traceback
from multiprocessing import Event, Process

from .scheduler_task import SchedulerTask

logger = logging.getLogger("task_manager")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s:task manager:%(levelname)s -- %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class TaskDescription:
    """Task description that reflects the information in the json file."""

    def __init__(self, filename):
        """Initialize from a json file.

        Checks that required parameters are present and sets defaults.
        """
        with open(filename) as file:
            logger.info(f"reading {filename}")
            json_text = file.read()
            dict_from_json = json.loads(json_text)

        # Required
        self.name = dict_from_json["name"]
        self.time = dict_from_json["time"]
        self.memory = dict_from_json["memory"]
        self.nodes = dict_from_json["nodes"]
        self.ranks = dict_from_json["ranks"]
        self.ranks_per_node = dict_from_json["ranks_per_node"]
        self.cpus = dict_from_json["cpus"]
        self.cpus_per_rank = dict_from_json["cpus_per_rank"]

        self.execution_type = dict_from_json["execution_type"]

        # Optional
        self.priority = dict_from_json.get("priority", 0)
        self.max_runs = dict_from_json.get("max_runs", 0)
        self.replicas = dict_from_json.get("replicas", 0)
        self.interval = dict_from_json.get("interval", 0)
        self.files = dict_from_json.get("files", [])
        self.folders = dict_from_json.get("folders", [])
        self.file_pattern = dict_from_json.get("file_pattern", [])
        self.filter = dict_from_json.get("filter", None)
        self.batch_size = dict_from_json.get("batch_size", None)
        self.watch_file = dict_from_json.get("watch_file", None)
        self.disk_limit = dict_from_json.get("disk_limit", 0)
        self.executable = dict_from_json.get("executable", "")

        if self.filter:
            self.filter = re.compile(self.filter.strip())

        self.filename = filename

        # parameters used for resubmitting the task
        self.file_modified = os.path.getmtime(filename)
        self.index = 0
        self.last_run = time.time()
        self.used_input_files = {}

    def filter_files(self, filenames):
        """Filter files based on the filter regular expression."""
        if self.filter is None:
            return filenames

        filtered_files = []
        if self.filter:
            for filename in filenames:
                if re.match(self.filter, filename):
                    filtered_files.append(filename)

        return filtered_files

    def list_input_files(self):
        """List input files from the folders and files."""
        files = []

        for file in self.files:
            if os.path.exists(file):
                files.append(file)

        for folder in self.folders:
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    files.append(os.path.join(root, filename))

        for pattern in self.file_pattern:
            for file in glob.glob(pattern):
                files.append(file)

        files = self.filter_files(files)
        if self.replicas > 0:
            unused_files = []
            for file in files:
                if file not in self.used_input_files:
                    unused_files.append(file)
                elif self.used_input_files[file] < self.replicas:
                    unused_files.append(file)
        else:
            unused_files = [file for file in files if file not in self.used_input_files]

        # Sort file by modification time to ensure reproducibility
        unused_files.sort(key=os.path.getmtime)

        return unused_files

    def mark_used_files(self, files):
        for file in files:
            if file in self.used_input_files:
                self.used_input_files[file] += 1
            else:
                self.used_input_files[file] = 1

    def batch_files(self):
        """Batch files according to the batch size."""
        files = self.list_input_files()

        if self.batch_size is None:
            return [files]

        batches = []
        for i in range(0, len(files), self.batch_size):
            batch = files[i : i + self.batch_size]
            if len(batch) == self.batch_size:
                batches.append(batch)

        return batches


class TaskManager:
    def __init__(self, status):
        """A task manager, that reads task descriptions from a folder and
        builds runnable task objects when required inputs are available.

        Another API for receiving tasks may be implemented later.

        Parameters:
        ------------
        task_folder: str
            Path to the folder containing task descriptions
        """

        self.queue = None
        self.status = status
        self.task_folder = self.status["task_parameters_folder"]

        self.tasks = {}

    def scan_tasks(self):
        """Read the task folder and construct a list of task types."""
        modified = False

        for task_file in os.listdir(self.task_folder):
            task_path = os.path.join(self.task_folder, task_file)

            if task_file in self.tasks:
                # Already loaded. Refresh if modified.
                task = self.tasks[task_file]
                modified_time = os.path.getmtime(task_path)
                if task.file_modified == modified_time:
                    continue

            modified = True
            old_task = self.tasks.get(task_file)

            task = TaskDescription(task_path)
            task.used_input_files = old_task.used_input_files if old_task else {}
            task.index = old_task.index if old_task else 0
            self.tasks[task_file] = task

        if modified:
            logger.info(f"{len(self.tasks)} tasks")

    def file_is_open(self, file_path):
        """Check if a file is open by another process."""
        try:
            result = subprocess.run(["lsof", file_path], stdout=subprocess.PIPE)
            if result.stdout:
                logger.info(f"File is open {file_path}")
                return True
        except Exception:
            logger.info(f"Error in file is open {file_path}")
            traceback.print_exc()
        return False

    def check_tasks(self):
        """construct runnable tasks and submit to queue."""

        for task in self.tasks.values():
            if task.max_runs > 0 and task.index >= task.max_runs:
                continue

            if task.interval > 0 and task.index > 0:
                if time.time() - task.last_run < task.interval:
                    continue

            requires_file = len(task.files)
            requires_file += len(task.folders)
            requires_file += len(task.file_pattern)
            if requires_file > 0:
                batches = task.batch_files()
                for batch in batches:
                    logger.info(
                        f"Queueing {task.name} with a batch of {len(batch)} files"
                    )
                    self.queue.push(SchedulerTask(task, batch))
                    task.mark_used_files(batch)
                    task.index += 1

            else:
                if task.replicas > 0:
                    if self.queue.n_replicas(task) >= task.replicas:
                        continue
                if task in self.queue:
                    continue
                if task.watch_file is not None:
                    if not os.path.exists(task.watch_file):
                        continue
                    if os.path.getmtime(task.watch_file) <= task.last_run:
                        continue
                    if self.file_is_open(task.watch_file):
                        continue
                    logger.info(
                        f"Queueing {task.name} with watch file {task.watch_file}"
                    )
                    self.queue.push(SchedulerTask(task, [task.watch_file]))
                else:
                    logger.info(f"Queueing {task.name}")
                    self.queue.push(SchedulerTask(task))
                task.last_run = time.time()
                task.index += 1

        logger.info(f"Queue length {len(self.queue)}")

    def start(self, queue):
        """Starts the task_manager in a process."""
        logger.info("starting task manager")
        self.status["task_manager_status"] = "starting"
        self.stop_event = Event()
        self.process = Process(
            target=self.main_loop,
            args=(
                self.stop_event,
                queue,
            ),
        )
        self.process.start()
        self.status["task_manager_status"] = "running"

    def stop(self):
        """Stop the task manager."""
        logger.info("Stopping")
        self.status["task_manager_status"] = "stopping"
        self.stop_event.set()
        self.process.join()
        self.status["task_manager_status"] = "stopped"
        logger.info("Stopped")

    def main_loop(self, stop_event, queue, period=1):
        """Periodically check for tasks."""
        self.queue = queue

        try:
            while not stop_event.is_set():
                self.scan_tasks()
                self.check_tasks()
                time.sleep(period)
        except KeyboardInterrupt:
            # Exit silently for keyboard interrupt
            # The main process should call stop()
            pass
        except BrokenPipeError:
            logger.info(
                "Task queue not available. The main process has exited without stopping the task manager. Exiting."
            )
