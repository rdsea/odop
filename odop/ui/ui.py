import contextlib
import multiprocessing
import os
import shutil
import signal
import sys
import time

import odop
import odop.scheduler as scheduler
from odop.common import ODOP_PATH, create_logger
from odop.odop_obs import OdopObs
from odop.ui import Status, read_config

logger = create_logger("odop")


def scan_tasks_folder(
    task_folder, task_parameters_folder=None, executables_folder=None, write=True
):
    """Loads tasks from the task folder path and all
    subpaths."""

    if type(task_folder) is list:
        for folder in task_folder:
            scan_tasks_folder(folder, task_parameters_folder, executables_folder, write)
        return

    task_folder = os.path.abspath(task_folder)
    logger.info(f"Scanning folder: {task_folder}")

    main_script = os.path.abspath(sys.argv[0])

    directories = {task_folder}
    for root, _dirs, _files in os.walk(task_folder):
        if task_folder in root:
            directories.add(root)

    for dir in directories:
        logger.info(f"Scanning folder: {dir}")
        odop.task.load_tasks_folder(
            dir,
            task_parameters_folder,
            exclude_file=main_script,
        )

    if write:
        odop.task.write_all(task_parameters_folder, executables_folder)


class OdopRuntime:
    def __init__(self):
        """Manager for the Odop runtime. Starts the observability, task manager, and controller processes."""
        self.stop_event = None

        self.odop_obs = None
        self.task_manager = None
        self.controller = None
        self.is_local_master = False
        self.is_global_master = False
        self.server_socket = None
        self.stop_event = None
        self.status = None
        self.nodes_folder = None
        self.this_node_folder = None

    def setup_directories(self):
        """Create directories for node information and task parameters."""
        self.hostname = os.uname().nodename
        slurm_id = os.environ.get("SLURM_JOB_ID")
        if slurm_id:
            self.nodes_folder = os.path.join(self.run_folder, slurm_id, "nodes")
            self.this_node_folder = os.path.join(self.nodes_folder, self.hostname)
        else:
            self.nodes_folder = os.path.join(self.run_folder, "nodes")
            self.this_node_folder = os.path.join(self.nodes_folder, self.hostname)

    def get_node_information(self):
        """Choose the master process on the each node. Write process pids into
        files and order timestamp first, then pid.
        """
        os.makedirs(self.this_node_folder, exist_ok=True)
        process_file = os.path.join(self.this_node_folder, f"{os.getpid()}")
        with open(process_file, "w") as f:
            f.write("")
        time.sleep(1)

        pids = os.listdir(self.this_node_folder)
        timestamps = [
            os.path.getmtime(os.path.join(self.this_node_folder, pid)) for pid in pids
        ]
        pids = sorted([int(pid) for pid in pids])
        sorted_by_time = sorted(zip(timestamps, pids))
        main = sorted_by_time[0][1]
        self.is_local_master = main == os.getpid()

    def count_processes(self):
        """Count processes on each node"""
        for node in os.listdir(self.nodes_folder):
            process_count = len(os.listdir(self.this_node_folder))
            self.status.set_nested(["nodes", node], process_count)

    def get_global_information(self):
        """Choose a global master process. Read node names from the nodes folder
        and sort them by the timestamp of the first process file, then alphabetically.
        """
        nodes = os.listdir(self.nodes_folder)
        nodes = sorted(nodes)

        def modified_time(node):
            path = self.this_node_folder
            pids = os.listdir(path)
            timestamps = [os.path.getmtime(os.path.join(path, pid)) for pid in pids]
            return min(timestamps)

        timestamps = [modified_time(node) for node in nodes]
        sorted_by_time = sorted(zip(timestamps, nodes))
        self.main_node = sorted_by_time[0][1]
        self.is_global_master = self.main_node == self.hostname
        if self.is_global_master:
            self.status.set_nested(["main_node"], self.hostname)
            self.main_pid = os.getpid()

    def clean_old_files(self, max_age=300):
        """Clean old process files. Removes files updated more than max_age
        seconds before the
        """
        self.hostname = os.uname().nodename
        current_time = time.time()
        try:
            for filename in os.listdir(self.this_node_folder):
                file_path = os.path.join(self.this_node_folder, filename)
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age:
                    os.remove(file_path)
        except FileNotFoundError:
            pass

    def stop(self):
        """Stop odop.

        - Stops the observability module
        - Stops the task manager
        - Stops the controller
        """
        self.odop_obs.stop()

        if self.is_global_master:
            self.status["runtime_status"] = "stopping"
            self.task_manager.stop()
            self.controller.stop()
            self.status["runtime_status"] = "stopped"
            shutil.rmtree(self.nodes_folder, ignore_errors=True)

    def start(
        self,
        task_folder=".",
        config_file=None,
        run_name=None,
        debug=False,
        pipe=None,
        stop_event=None,
    ):
        """Start odop.

        - Scans the task_folder for task definitions
        - Starts the observability module
        - Starts the task manager
        - Starts the controller

        Parameters
        ----------
        task_folder: str
            The folder containing the task definitions.
        run_name: str
            The name of the run. If None, an unused name is generated.
        """
        try:
            if config_file is None:
                config_file = os.path.join(ODOP_PATH, "odop_conf.yaml")

            self.config = read_config(config_file)
            runtime_config = self.config.get("runtime")
            if run_name is None:
                if "run_name" not in runtime_config:
                    raise ValueError(
                        "run name must be specified in the config file or as an argument"
                    )
                run_name = runtime_config["run_name"]

            self.run_folder = os.path.join(ODOP_PATH, "runs", run_name)
            os.makedirs(self.run_folder, exist_ok=True)
            self.status = Status(os.path.join(self.run_folder, "status"))
            self.status.reset()
            self.setup_directories()
            self.clean_old_files()
            self.get_node_information()
            if self.is_local_master:
                self.get_global_information()
            if self.is_global_master:
                logger.info("ODOP STARTING")

            # all tasks start the observability module
            obs_config = self.config.get("odop_obs")
            self.odop_obs = OdopObs(
                run_folder=self.run_folder,
                is_master=self.is_local_master,
                config=obs_config,
            )
            self.odop_obs.start()
            if self.is_global_master:
                logger.info("Observability module")

            if self.is_global_master:
                # create a status file
                self.status["runtime_status"] = "running"
                self.count_processes()

                # create task folders and delete any contents
                executables_folder = os.path.join(self.run_folder, "executables")
                task_parameters_folder = os.path.join(
                    self.run_folder, "task_parameters"
                )
                self.status["task_parameters_folder"] = task_parameters_folder
                self.status["executables_folder"] = executables_folder
                if os.path.exists(executables_folder):
                    shutil.rmtree(executables_folder, ignore_errors=True)
                if os.path.exists(task_parameters_folder):
                    shutil.rmtree(task_parameters_folder, ignore_errors=True)
                os.makedirs(executables_folder, exist_ok=True)
                os.makedirs(task_parameters_folder, exist_ok=True)

                # scan task_folder and subfolders for tasks
                scan_tasks_folder(
                    task_folder, task_parameters_folder, executables_folder
                )

                # start the task queue and task manager
                task_queue = scheduler.TaskQueue()
                self.task_manager = scheduler.TaskManager(self.status)
                self.task_manager.start(task_queue)

                # start the controller
                runtime_config["executables_folder"] = executables_folder
                self.controller = scheduler.Controller(
                    task_queue, self.status, runtime_config
                )
                self.controller.start(runtime_config)
        except Exception as e:
            # Notify the parent process about the error
            logger.error(str(e))
            pipe.send("error")
            pipe.close()
            raise e

        # Notify the parent process that the runtime has started
        pipe.send("started")
        pipe.close()

        self.stop_event = stop_event

        def handle_sigterm(self, signum, frame):
            """Handle SIGTERM signal."""
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, handle_sigterm)

        # Periodically update the status file and wait for
        # a stop signal
        try:
            while not self.stop_event.is_set():
                time.sleep(2)
                self.count_processes()
        except KeyboardInterrupt:
            # Exit the loop and stop the runtime
            pass
        except Exception as e:
            raise e

        self.stop()


odop_runtime = OdopRuntime()


def stop():
    """Stop the odop runtime by setting the stop event."""
    odop_runtime.stop_event.set()
    odop_runtime.process.join()


def start(task_folder=".", config_file=None, run_name=None, debug=False):
    """Start the odop runtime and set up signal handlers to stop it."""
    parent_conn, child_conn = multiprocessing.Pipe()
    odop_runtime.stop_event = multiprocessing.Event()
    odop_runtime.process = multiprocessing.Process(
        target=odop_runtime.start,
        args=(
            task_folder,
            config_file,
            run_name,
            debug,
            child_conn,
            odop_runtime.stop_event,
        ),
    )

    odop_runtime.process.start()
    message = parent_conn.recv()
    parent_conn.close()
    if message == "error":
        raise RuntimeError("Error starting the runtime")


@contextlib.contextmanager
def runtime(task_folder=".", config_file=None, run_name=None, debug=False):
    start(task_folder, config_file, run_name, debug)
    try:
        yield
    except KeyboardInterrupt:
        logger.info("received keyboard interrupt, stopping")
    finally:
        stop()
