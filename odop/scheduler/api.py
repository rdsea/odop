"""An API for retrieving information about running jobs and resource from the scheduler."""

import uvicorn
from fastapi import FastAPI

from odop.engine.engine import StatusCode


def create_app(tasks):
    app = FastAPI()

    @app.get("/")
    def summary():
        """Return a summary of the task queue."""
        summary = {
            "running_tasks": len(
                [
                    tasks[id]
                    for id in tasks.keys()
                    if tasks[id].status == StatusCode.RUNNING
                ]
            ),
            "pending_tasks": len(
                [
                    tasks[id]
                    for id in tasks.keys()
                    if tasks[id].status == StatusCode.PENDING
                ]
            ),
            "finished_tasks": len(
                [
                    tasks[id]
                    for id in tasks.keys()
                    if tasks[id].status == StatusCode.COMPLETED
                ]
            ),
            "failed_tasks": len(
                [
                    tasks[id]
                    for id in tasks.keys()
                    if tasks[id].status == StatusCode.FAILED
                ]
            ),
        }
        return summary

    @app.get("/status")
    def get_status():
        """Return the current status of all tasks."""
        status = []
        for id in tasks.keys():
            task = tasks[id]
            status.append(
                {
                    "name": task.name,
                    "task_id": task.task_id,
                    "index": task.index,
                    "status": task.status.value,
                }
            )
        return status

    @app.get("/status/{task_id}")
    def get_task_status(task_id: int):
        """Return information about a given task, provided a task_id."""
        for id in tasks.keys():
            task = tasks[id]
            if task.id == task_id:
                task_dict = {
                    "name": task.name,
                    "task_id": task.task_id,
                    "index": task.index,
                    "status": task.status.value,
                    "pid": task.pid,
                    "times_failed": task.times_failed,
                }
                if hasattr(task, "parameters"):
                    task_dict["parameters"] = task.parameters
                if hasattr(task, "start_time"):
                    task_dict["start_time"] = task.start_time
                if hasattr(task, "end_time"):
                    task_dict["end_time"] = task.end_time
                return task_dict

        return {"error": "Task not found"}

    return app


def start_api_server(hostname, port, tasks):
    app = create_app(tasks)
    uvicorn.run(app, host=hostname, port=port)
