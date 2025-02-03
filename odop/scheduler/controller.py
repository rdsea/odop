import importlib
import multiprocessing
import os
import sys
import threading
import time
import traceback
import xmlrpc.client
from multiprocessing import Event, Process
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

import requests

from odop.common import create_logger
from odop.engine.engine import Engine, StatusCode
from odop.scheduler.algorithms import Algorithm
from odop.scheduler.api import start_api_server

logger = create_logger("controller")


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)


class Controller:
    def __init__(
        self,
        queue,
        status,
        config,
    ):
        """A simple controller for ODOP tasks. Receives tasks from a scheduler queue
        object and runs them when resources are available.

        parameters
        ----------
        """
        self.manager = multiprocessing.Manager()
        self.tasks = self.manager.dict()

        self.queue = queue
        self.status = status
        self.start_time = time.time()
        self.engine = None
        self.engine_process = None

        algorithm = config.get("algorithm", "priority")
        self.load_algorithm(algorithm)

        self.scheduling_interval = config.get("frequency", 1)
        self.executables_folder = status.get("executables_folder", "executables")
        self.obs_port = config.get("obs_port")
        self.n_stored_metric = config.get("n_stored_metric", 100)
        self.cpu_free_threshhold = config.get("cpu_free_threshhold", 10)
        self.excluded_cpus = config.get("excluded_cpus", [])
        self.resubmit_wait_time = config.get("resubmit_wait_time", 60)

        # Store for monitoring data and task status
        self.monitoring_data = {}

    def load_algorithm(self, algorithm):
        """Load the scheduling and assignment algorithm"""
        assert isinstance(algorithm, str)
        logger.info(f"Loading algorithm {algorithm}")
        if algorithm.endswith(".py"):
            algorithm = algorithm[:-3]

        filename = f"{algorithm}.py"

        # check if the working directory contains the file
        if os.path.exists(filename):
            spec = importlib.util.spec_from_file_location(algorithm, filename)
            module = importlib.util.module_from_spec(spec)
            sys.modules[algorithm] = module
        elif algorithm in ["fifo", "priority", "best_fit", "round_robin"]:
            module = __import__(f"odop.scheduler.algorithms.{algorithm}", fromlist=[""])
            logger.info(f"Loaded scheduling algorithm module {module}")
        else:
            raise ValueError(f"Algorithm {algorithm} not found")

        # find a class in the module that is a subclass of Algorithm
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Algorithm):
                cls = obj
                break

        self.algorithm = cls()

    def execute_task(self, task, placement):
        """Execute a task on the engine."""

        try:
            logger.info(f"Executing task {task.name}")
            task_dict = task.dict()
            task_dict["nodes"] = len(placement.keys())
            task_dict = self.engine.run(task.dict(), placement)
            task.status = StatusCode(task_dict["status"].lower())
            task.task_id = task_dict["id"]
            task.pid = task_dict["pid"]
        except Exception:
            logger.info(f"Error executing task {task.name}")
            traceback.print_exc()
            task.status = StatusCode.FAILED
            task.end_time = time.time()

    def get_metrics(self, node):
        """Returns a list of available resources from the metrics endpoint."""
        if node not in self.monitoring_data:
            self.monitoring_data[node] = []

        try:
            endpoint = f"http://{node}:{self.obs_port}/metrics"
            response = requests.get(endpoint)
            resources = response.json()
        except Exception:
            return

        self.monitoring_data[node].extend(resources)
        self.monitoring_data[node] = self.monitoring_data[node][-self.n_stored_metric :]

    def get_node_resources(self, node):
        """Returns the available resources based on the last monitoring data."""
        # Check if any task is running on the node
        running_tasks = [
            task for task in self.tasks.values() if task.status == StatusCode.RUNNING
        ]
        node_tasks = [task for task in running_tasks if node in task.execution_nodes]
        node_free = len(node_tasks) > 0

        # current usage is the last element with "type": "node"
        self.get_metrics(node)
        node_data = [m for m in self.monitoring_data[node] if m["type"] == "node"]
        process_data = [m for m in self.monitoring_data[node] if m["type"] == "process"]
        if len(node_data) == 0 or len(process_data) == 0:
            return None

        free_cpus = []
        usages = node_data[-1]["cpu"]["usage"]["value"].values()
        for cpu, usage in enumerate(usages):
            if usage < self.cpu_free_threshhold:
                free_cpus.append(cpu)

        # Now calculate free CPU and memory
        memory_use = process_data[-1]["mem"]["usage"]["rss"]["value"]
        memory = 8 * 1024 - memory_use

        return {
            "free": node_free,
            "memory": memory,
            "cpus": free_cpus,
            "private_disk": 0,
        }

    def resources_available(self):
        """Get resources available on all nodes."""
        resources = {"nodes": {}}
        for node in self.status["nodes"].keys():
            node_resource = self.get_node_resources(node)
            if node_resource is not None:
                resources["nodes"][node] = node_resource
        resources["shared_disk"] = 0
        return resources

    def check_running_tasks(self):
        for task_id in self.tasks.keys():
            task = self.tasks[task_id]
            if task.status == StatusCode.RUNNING:
                enginetask = self.engine.get_task(task.id)
                logger.info(f"Task {task.name} status: {enginetask['status']}")
                task.status = StatusCode(enginetask["status"])
            elif task.status == StatusCode.COMPLETED:
                logger.info(f"Task {task.name} completed")
                task.end_time = time.time()
            elif task.status == StatusCode.FAILED:
                logger.info(f"Task {task.name} failed")
                if (
                    task.times_failed < 3
                    and time.time() - task.end_time > self.resubmit_wait_time
                ):
                    task.times_failed += 1
                    task.status = StatusCode.PENDING
                    task.end_time = time.time()
            self.tasks[task_id] = task

    def start(
        self,
        config,
    ):
        """Starts the controller and the engine processes."""
        logger.info("engine starting")
        self.hostname = config.get("host", "0.0.0.0")
        self.controller_port = config.get("controller_port", 8002)
        self.engine_port = config.get("engine_port", 8003)
        self.info_api_port = config.get("info_api_port", 8004)

        self.stop_event = Event()
        self.engine_stop_event = Event()

        engine = Engine(self.executables_folder)
        self.engine_process = Process(
            target=engine.start,
            args=(
                self.engine_stop_event,
                self.hostname,
                self.engine_port,
            ),
        )
        self.engine_process.start()
        self.status["engine_status"] = "running"

        logger.info("controller starting")
        self.process = Process(
            target=self.main_loop,
            args=(
                self.queue,
                self.stop_event,
                self.tasks,
            ),
        )
        self.process.start()
        self.status["controller_status"] = "running"

        logger.info("api starting")
        self.api_process = Process(
            target=start_api_server,
            args=(
                self.hostname,
                self.info_api_port,
                self.tasks,
            ),
        )
        self.api_process.start()
        self.status["api_status"] = "running"
        self.status["api_address"] = f"http://{self.hostname}:{self.info_api_port}"

    def connect_engine(self):
        """Start the engine process in a separate process."""
        logger.info("connecting to engine")
        self.engine = xmlrpc.client.ServerProxy(
            f"http://{self.hostname}:{self.engine_port}/RPC2"
        )
        while True:
            try:
                self.engine.is_running()
                break
            except ConnectionRefusedError:
                time.sleep(1)
        logger.info("Connected to engine")

    def serve_rpc(self, port):
        """Start the controller rpc server in a separate process."""
        with SimpleXMLRPCServer(
            ("localhost", port), requestHandler=RequestHandler
        ) as server:
            self.rpc_server = server
            server.register_introspection_functions()
            server.register_instance(self)
            server.serve_forever()

    def start_rpc_server(self, port):
        """Start the controller rpc server in a separate thread."""
        self.rpc_thread = threading.Thread(target=self.serve_rpc, args=(port,))
        self.rpc_thread.daemon = True
        self.rpc_thread.start()

    def stop_rpc_server(self):
        """Stop the controller rpc server."""
        if self.rpc_server:
            self.rpc_server.shutdown()
            self.rpc_server.server_close()
            self.rpc_thread.join()

    def stop(self):
        """Stop the controller process."""
        logger.info("Stopping")
        self.stop_event.set()
        self.api_process.terminate()
        self.api_process.join()
        self.status["api_status"] = "stopped"
        self.process.join()
        self.engine_process.join()
        self.status["engine_status"] = "stopped"
        logger.info("Stopped")
        self.status["controller_status"] = "stopped"

    def main_loop(self, queue, stop_event, tasks):
        """The controller main loop periodically checks for tasks in the queue
        and runs them when resources are available.

        The controller also tracks the main task resource usage and stops tasks
        at the end of each cycle. The tasks are restarted when resources are available.
        """
        sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)
        sys.stderr = os.fdopen(sys.stderr.fileno(), "w", buffering=1)
        self.queue = queue
        self.tasks = tasks
        self.start_rpc_server(self.controller_port)
        self.connect_engine()

        while not stop_event.is_set():
            try:
                logger.info("main loop")
                time.sleep(self.scheduling_interval)
                self.check_running_tasks()

                resources = self.resources_available()

                queue_dict = self.queue.dict()
                task_placement = self.algorithm.next_tasks(queue_dict, resources)

                if task_placement is None:
                    continue

                for task_id, placement in task_placement.items():
                    self.execute_task(queue_dict[task_id], placement)
                    self.tasks[task_id] = queue_dict[task_id]
                    self.tasks[task_id].execution_timestamp = time.time()
                    self.tasks[task_id].execution_nodes = placement.keys()
                    self.queue.delete_id(task_id)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt")
                break
            except BrokenPipeError:
                logger.info(
                    "Task queue not available. The main process has exited without stopping the controller. Exiting."
                )
                break
            except Exception:
                logger.info("Error in main loop")
                traceback.print_exc()

        self.engine_stop_event.set()
        self.stop_rpc_server()

    def reload_algorithm(self, algorithm):
        """Reload the algorithm used to evaluate resource availability.

        This should be called from a different process, and requires an endpoint.
        """
        pass

    def task_stopped(self, task_id):
        """Receive notification from the engine that a task has been stopped."""
        for task_id in self.tasks.keys():
            task = self.tasks[task_id]
            if task.task_id == task_id:
                task.status = StatusCode.PENDING
                break

    def task_complete(self, task_id):
        """Receive notification from the engine that a task has been finished."""
        for task_id in self.tasks.keys():
            task = self.tasks[task_id]
            if task.task_id == task_id:
                task.status = StatusCode.COMPLETED
                break
