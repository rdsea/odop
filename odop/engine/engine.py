import logging
import os
import signal
import subprocess
import threading
import time
import traceback
from enum import Enum
from typing import Any
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

import psutil
import yaml
from pydantic import BaseModel

logger = logging.getLogger("engine")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s:engine:%(levelname)s -- %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class StatusCode(Enum):
    """Status codes for tasks"""

    PENDING = "pending"
    NOT_STARTED = "not_started"
    FAILED_TO_START = "failed_to_start"
    RUNNING = "running"
    STOPPED = "stopped"
    KILLED = "killed"
    COMPLETED = "completed"
    FAILED = "failed"


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)


class EngineTask(BaseModel):
    """Task definition for the engine. Most parameters are passed directly by
    the scheduler. Parameters are modified by the engine and the process and
    start time are set when the task is run.
    """

    id: int
    name: str
    execution_type: str
    time: float
    memory: int
    disk_limit: int
    priority: int
    parameters: dict = {}

    executable: str = ""

    status: StatusCode = StatusCode.NOT_STARTED
    status_reason: str = ""
    stderr: str = ""
    process: Any = None
    start_time: Any = None
    age: Any = None


class TaskManager:
    def __init__(self, task, executables_folder):
        """TaskManager represents a task in the main engine process. It manages the state
        parameters of a task, whether it is running or not.
        """
        self.process = None
        self.stderr = None
        self.stdout = None
        self.returncode = None
        self.pid = None
        self.executables_folder = executables_folder

        # copy the properties of the task over. These are defined in EngineTask above
        for key, value in task.dict().items():
            setattr(self, key, value)

    def get_slurm_resources(self):
        if "SLURM_JOB_ID" in os.environ:
            self.is_slurm = os.environ["SLURM_JOB_ID"] != ""
        else:
            self.is_slurm = False

        if self.is_slurm:
            if "SLURM_MEM_PER_NODE" in os.environ:
                self.slurm_memory = int(os.environ["SLURM_MEM_PER_NODE"])
            elif "SLURM_MEM_PER_CPU" in os.environ:
                cpus = int(os.environ["SLURM_CPUS_ON_NODE"])
                mem_per_cpu = int(os.environ["SLURM_MEM_PER_CPU"])
                self.slurm_memory = cpus * mem_per_cpu
            else:
                self.slurm_memory = 0

            if "SLURM_CPU_BIND" in os.environ:
                self.cpu_bind_command = "--cpu_bind=cores"
            else:
                self.cpu_bind_command = ""

    def format_mpi_command(self, command, placement):
        if "SLURM_JOB_ID" in os.environ:
            self.get_slurm_resources()
            node1 = placement[next(iter(placement.keys()))]
            nodelist = ",".join(placement.keys())
            nodes = len(placement.keys())
            ranks = node1["ranks"]
            cpus = len(node1["cpus"]) // ranks
            run_command = f"srun --overlap {self.cpu_bind_command} --nice=20 -N {nodes} --mem={self.slurm_memory} --ntasks-per-node={ranks} --cpus-per-task={cpus} --nodelist {nodelist} {command}"
            return run_command
        else:
            os.makedirs(
                os.path.join(self.executables_folder, "hostfiles"), exist_ok=True
            )
            hostfile_path = os.path.join(
                self.executables_folder, "hostfiles", f"{self.name}_{self.id}.hostfile"
            )
            total_ranks = 0
            with open(hostfile_path, "w") as f:
                for node in placement.keys():
                    ranks = placement[node]["ranks"]
                    total_ranks += ranks
                    f.write(f"{node} slots={ranks}\n")
            command = f"mpirun -n {total_ranks} --hostfile {hostfile_path} {command}"
            return command

    def run_command_on_nodes(self, command, placement):
        """Runs a command using ssh, mpirun or srun"""
        working_dir = os.getcwd()
        command = " ".join(command)

        n_ranks = 0
        for node in placement.keys():
            n_ranks += placement[node]["ranks"]

        if n_ranks == 1 and "SLURM_JOB_ID" not in os.environ:
            my_hostname = os.uname().nodename
            node = next(iter(placement.keys()))
            if node not in ["localhost", my_hostname]:
                command = f"ssh {node} 'cd {working_dir}; {command}'"
        else:
            command = self.format_mpi_command(command, placement)

        logger.info(f"COMMAND {command}")
        self.process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
        self.pid = self.process.pid

    def run_serialized(self, placement):
        """Run the task if it is serialized as a cloudpickle file."""
        assert self.execution_type == "python_task"
        executable_path = os.path.join(self.executables_folder, f"{self.name}.pickle")
        config_data = {
            "task_file": executable_path,
            "parameters": self.parameters,
            "placement": placement,
        }

        config_path = os.path.join(
            self.executables_folder, "task_configs", f"{self.name}_{self.id}.py"
        )
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            yaml.safe_dump(config_data, f)

        script_path = __file__.replace("engine.py", "execute_task.py")

        self.run_command_on_nodes(
            ["nice", "-n", "20", "python", script_path, "--config", config_path],
            placement,
        )

    def run_executable(self, placement):
        """Run the task if it is an executable."""
        assert self.execution_type == "executable"

        executable_path = os.path.join(self.executables_folder, f"{self.executable}")
        parameters = [f"{key}={value}" for key, value in self.parameters.items()]

        self.run_command_on_nodes(
            ["nice", "-n 20", executable_path, *parameters], placement
        )

    def get_stderr(self):
        """Get the stderr of the task"""
        if self.stderr:
            return

        if self.process.poll() is None:
            stdout, stderr = self.process.communicate()
            self.stdout = stdout
            self.stderr = stderr
            return
        else:
            try:
                self.stderr = self.process.stderr.read().decode("iso-8859-1")
                self.stdout = self.process.stdout.read().decode("iso-8859-1")
            except Exception:
                pass

    def run(self, placement):
        """Run the task

        Parameters:
        cpu_list: list
            List of CPUs to run the task on
        """

        try:
            if self.execution_type == "python_task":
                self.run_serialized(placement)
            elif self.execution_type == "executable":
                self.run_executable(placement)
            else:
                raise ValueError("Task type not recognized")

            self.status = StatusCode.RUNNING
            self.start_time = time.time()
        except Exception:
            logger.info(f"Failed to run task {self.name}")
            traceback.print_exc()

    def kill(self, reason="killed by signal"):
        """Kill the task

        Independent of current status, this function will send
        a kill signal even if the task is already killed.
        """
        self.status = StatusCode.KILLED
        self.status_reason = reason
        self.process.kill()

    def stop(self, reason="stopped by signal"):
        """Send stop signal to the task"""
        if self.status == StatusCode.RUNNING:
            process = psutil.Process(self.pid)
            process.send_signal(signal.SIGSTOP)
            self.status = StatusCode.STOPPED
            self.status_reason = reason

    def restart(self):
        """Continue a stopped task"""
        if self.status == StatusCode.STOPPED:
            process = psutil.Process(self.pid)
            process.send_signal(signal.SIGCONT)
            self.status = StatusCode.RUNNING
            self.status_reason = None
        else:
            raise ValueError("Continuing a task that is not stopped")

    def wait(self):
        """Wait for the task to finish."""
        self.process.wait()
        self.handle_exit()

    def update_status(self):
        """Check and update the status of the task"""
        if self.status == StatusCode.STOPPED:
            if not self.is_stopped():
                # it's not stopped, even though the signal was sent. Just kill it
                self.kill("sent stop signal but task is not stopped")
            return

        if self.status != StatusCode.RUNNING:
            return

        # The process is running. Check for completion and time limit
        if self.is_active():
            if self.time is not None:
                if time.time() - self.start_time > self.time:
                    self.kill("time limit")
        else:
            self.handle_exit()

    def is_stopped(self):
        """Check if the process is stopped"""
        p = psutil.Process(self.process.pid)
        if p.status() == psutil.STATUS_STOPPED:
            if self.status != StatusCode.STOPPED:
                self.status = StatusCode.STOPPED
                self.status_reason = "unknown"
            return True

    def is_active(self):
        """Check if the process is active (not sleeping or stopped)"""
        return self.process.poll() is None

    def handle_exit(self):
        """Process has exited. Check the return value and update the status."""
        if self.status == StatusCode.KILLED:
            logger.info(f"task {self.name} was killed")
            return

        return_value = self.process.poll()
        self.returncode = self.process.returncode
        logger.info(f"task {self.name} exited with return value {return_value}")
        if return_value != 0:
            self.get_stderr()
            logger.info(f"stdout: {self.stdout}")
            logger.info(f"stderr: {self.stderr}")
            self.status = StatusCode.FAILED
        else:
            self.status = StatusCode.COMPLETED


class Engine:
    def __init__(self, executables_folder):
        self.tasks = []
        self.executables_folder = executables_folder

    def run(self, task, cpu_list):
        """Run a task.

        Parameters:

        task: EngineTask
            Task to run
        executables_folder: str
            Path to the folder where executables are stored
        """
        logger.info(f"running task {task['name']}")
        try:
            task = EngineTask(**task)
            task = TaskManager(task, self.executables_folder)
            task.run(cpu_list)
        except Exception:
            logger.info(f"failed to run task {task['name']}")
            traceback.print_exc()
            return None, StatusCode.FAILED_TO_START
        self.tasks.append(task)

        task_dict = {
            "name": task.name,
            "id": task.id,
            "status": task.status.name.lower(),
            "status_reason": task.status_reason if task.status_reason else "none",
            "pid": task.pid if task.pid else "none",
        }
        return task_dict

    def update(self):
        """Update the status of all tasks"""
        logger.info("updating tasks")
        for task in self.tasks:
            task.update_status()

    def main_loop(self, stop_event):
        """Main loop of the engine"""
        try:
            while not stop_event.is_set():
                self.update()
                time.sleep(1)
        except KeyboardInterrupt:
            # Wait for subprocesses to finish and exit
            self.wait()

    def kill_all(self, reason="killed by signal"):
        """Kill all tasks"""
        for task in self.tasks:
            task.kill(reason)

    def stop_all(self):
        """Stop all tasks"""
        for task in self.tasks:
            task.stop()

    def get_task(self, task_id):
        """Get a task by id. RPC cannot return the thread object, so we return
        the PID instead.
        """
        for task in self.tasks:
            if task.id == task_id:
                task_dict = {
                    "name": task.name,
                    "id": task.id,
                    "status": task.status.name.lower(),
                    "status_reason": task.status_reason,
                    "pid": task.pid if task.pid else "none",
                }
                return task_dict
        return {}

    def is_running(self):
        return True

    def serve_rpc(self):
        with SimpleXMLRPCServer(
            (self.hostname, self.port), requestHandler=RequestHandler
        ) as server:
            self.rpc_server = server
            server.register_introspection_functions()
            server.register_instance(self)
            server.serve_forever()

    def start(self, stop_event, hostname="localhost", port=8003):
        logger.info("ENGINE STARTING")
        self.hostname = hostname
        self.port = port
        self.rpc_thread = threading.Thread(target=self.serve_rpc)
        self.rpc_thread.daemon = True
        self.rpc_thread.start()

        self.main_loop(stop_event)

        # wait for the rpc thread to exit
        self.rpc_server.shutdown()
        self.rpc_server.server_close()
        self.rpc_thread.join()

    def wait(self):
        """Wait the engine process"""
        logger.info("Waiting for tasks to finish")
        for task in self.tasks:
            logger.info(f"Waiting for task {task.name}")
            task.wait()
        logger.info("All tasks finished")
        return True
