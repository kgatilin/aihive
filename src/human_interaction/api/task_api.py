import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from aiohttp import web
import json

from src.task_management.application.task_service import TaskService
from src.task_management.domain.task import TaskStatus, TaskPriority


logger = logging.getLogger(__name__)


class TaskApi:
    """API handler for task-related operations."""
    
    def __init__(self, task_service: TaskService):
        self.task_service = task_service
    
    async def create_task(self, request: web.Request) -> web.Response:
        """Create a new task."""
        try:
            # Parse request body
            data = await request.json()
            
            # Validate required fields
            required_fields = ["title", "description", "priority", "created_by"]
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {"error": f"Missing required field: {field}"},
                        status=400
                    )
            
            # Create the task
            task = await self.task_service.create_task(
                title=data["title"],
                description=data["description"],
                priority=data["priority"],
                created_by=data["created_by"],
                assignee=data.get("assignee"),
                due_date=data.get("due_date"),
                requirements_ids=data.get("requirements_ids"),
                parent_task_id=data.get("parent_task_id"),
                tags=data.get("tags")
            )
            
            # Return the created task
            return web.json_response({
                "status": "success",
                "data": {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status.value,
                    "message": f"Task created successfully with ID {task.task_id}"
                }
            }, status=201)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def get_task(self, request: web.Request) -> web.Response:
        """Get a task by ID."""
        try:
            # Get task ID from URL
            task_id = request.match_info.get("task_id")
            if not task_id:
                return web.json_response({"error": "Task ID is required"}, status=400)
            
            # Get the task
            task = await self.task_service.get_task(task_id)
            if not task:
                return web.json_response({"error": f"Task with ID {task_id} not found"}, status=404)
            
            # Convert task to dictionary for JSON response
            task_data = {
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "created_by": task.created_by,
                "assignee": task.assignee,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "requirements_ids": task.requirements_ids,
                "parent_task_id": task.parent_task_id,
                "tags": task.tags,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            
            return web.json_response({"status": "success", "data": task_data})
        except Exception as e:
            logger.error(f"Error retrieving task: {str(e)}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def list_tasks(self, request: web.Request) -> web.Response:
        """List tasks with optional filtering."""
        try:
            # Parse query parameters
            status = request.query.get("status")
            assignee = request.query.get("assignee")
            
            tasks = []
            if status:
                # Get tasks by status
                tasks = await self.task_service.find_tasks_by_status(status)
            elif assignee:
                # Get tasks by assignee
                tasks = await self.task_service.find_tasks_by_assignee(assignee)
            else:
                # Get all tasks (using an empty criteria)
                tasks = await self.task_service.find_tasks_by_criteria({})
            
            # Convert tasks to dictionaries for JSON response
            tasks_data = []
            for task in tasks:
                tasks_data.append({
                    "task_id": task.task_id,
                    "title": task.title,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "assignee": task.assignee,
                    "created_at": task.created_at.isoformat()
                })
            
            return web.json_response({
                "status": "success",
                "data": tasks_data,
                "count": len(tasks_data)
            })
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def update_task_status(self, request: web.Request) -> web.Response:
        """Update a task's status."""
        try:
            # Get task ID from URL
            task_id = request.match_info.get("task_id")
            if not task_id:
                return web.json_response({"error": "Task ID is required"}, status=400)
            
            # Parse request body
            data = await request.json()
            
            # Validate required fields
            required_fields = ["new_status", "changed_by"]
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {"error": f"Missing required field: {field}"},
                        status=400
                    )
            
            # Update the task status
            task = await self.task_service.update_task_status(
                task_id=task_id,
                new_status=data["new_status"],
                changed_by=data["changed_by"],
                reason=data.get("reason"),
                related_artifact_ids=data.get("related_artifact_ids")
            )
            
            return web.json_response({
                "status": "success",
                "data": {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "message": f"Task status updated to {task.status.value}"
                }
            })
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def assign_task(self, request: web.Request) -> web.Response:
        """Assign a task to someone."""
        try:
            # Get task ID from URL
            task_id = request.match_info.get("task_id")
            if not task_id:
                return web.json_response({"error": "Task ID is required"}, status=400)
            
            # Parse request body
            data = await request.json()
            
            # Validate required fields
            required_fields = ["assignee", "assigned_by"]
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {"error": f"Missing required field: {field}"},
                        status=400
                    )
            
            # Assign the task
            task = await self.task_service.assign_task(
                task_id=task_id,
                assignee=data["assignee"],
                assigned_by=data["assigned_by"],
                reason=data.get("reason")
            )
            
            return web.json_response({
                "status": "success",
                "data": {
                    "task_id": task.task_id,
                    "assignee": task.assignee,
                    "message": f"Task assigned to {task.assignee}"
                }
            })
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error assigning task: {str(e)}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def complete_task(self, request: web.Request) -> web.Response:
        """Mark a task as completed."""
        try:
            # Get task ID from URL
            task_id = request.match_info.get("task_id")
            if not task_id:
                return web.json_response({"error": "Task ID is required"}, status=400)
            
            # Parse request body
            data = await request.json()
            
            # Validate required fields
            required_fields = ["completed_by", "outcome_summary"]
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {"error": f"Missing required field: {field}"},
                        status=400
                    )
            
            # Complete the task
            task = await self.task_service.complete_task(
                task_id=task_id,
                completed_by=data["completed_by"],
                outcome_summary=data["outcome_summary"],
                deliverable_ids=data.get("deliverable_ids"),
                quality_metrics=data.get("quality_metrics")
            )
            
            return web.json_response({
                "status": "success",
                "data": {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "message": "Task marked as completed"
                }
            })
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error completing task: {str(e)}")
            return web.json_response({"error": "Internal server error"}, status=500)


def setup_routes(app: web.Application, task_api: TaskApi) -> None:
    """Set up routes for the task API."""
    app.router.add_post("/api/tasks", task_api.create_task)
    app.router.add_get("/api/tasks", task_api.list_tasks)
    app.router.add_get("/api/tasks/{task_id}", task_api.get_task)
    app.router.add_patch("/api/tasks/{task_id}/status", task_api.update_task_status)
    app.router.add_patch("/api/tasks/{task_id}/assign", task_api.assign_task)
    app.router.add_patch("/api/tasks/{task_id}/complete", task_api.complete_task) 