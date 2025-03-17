import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.task_management.application.services.task_service import TaskService
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.dependencies import get_task_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    created_by: str = Field(...)
    due_date: Optional[datetime] = None
    requirements_ids: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """Response model for a task."""
    task_id: str
    title: str
    description: str
    priority: str
    status: str
    created_by: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    requirements_ids: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    artifact_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TaskStatusUpdate(BaseModel):
    """Request model for updating a task status."""
    status: str = Field(..., pattern="^(created|assigned|in_progress|blocked|review|completed|canceled)$")
    changed_by: str
    reason: Optional[str] = None


class TaskAssignment(BaseModel):
    """Request model for assigning a task."""
    assignee: str
    assigned_by: str


class TaskCompletion(BaseModel):
    """Request model for completing a task."""
    completed_by: str
    artifact_ids: Optional[List[str]] = None
    completion_notes: Optional[str] = None


class TaskCancellation(BaseModel):
    """Request model for canceling a task."""
    canceled_by: str
    reason: Optional[str] = None


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """Create a new task."""
    try:
        created_task = await task_service.create_task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            created_by=task.created_by,
            due_date=task.due_date,
            requirements_ids=task.requirements_ids,
            parent_task_id=task.parent_task_id,
            tags=task.tags
        )
        
        return created_task.to_dict()
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """Get a task by ID."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return task.to_dict()


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    tag: Optional[str] = None,
    task_service: TaskService = Depends(get_task_service)
) -> List[Dict[str, Any]]:
    """Get tasks with optional filters."""
    try:
        tasks = []
        
        if status:
            try:
                tasks = await task_service.find_tasks_by_status(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status value: {status}"
                )
        elif assignee:
            tasks = await task_service.find_tasks_by_assignee(assignee)
        elif tag:
            tasks = await task_service.find_tasks_by_criteria({"tags": tag})
        else:
            # Default to returning all tasks in CREATED or ASSIGNED status
            created_tasks = await task_service.find_tasks_by_status(TaskStatus.CREATED.value)
            assigned_tasks = await task_service.find_tasks_by_status(TaskStatus.ASSIGNED.value)
            tasks = created_tasks + assigned_tasks
        
        return [task.to_dict() for task in tasks]
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tasks: {str(e)}"
        )


@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """Update a task's status."""
    try:
        task = await task_service.update_task_status(
            task_id=task_id,
            new_status=status_update.status,
            changed_by=status_update.changed_by,
            reason=status_update.reason
        )
        
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task status: {str(e)}"
        )


@router.put("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    assignment: TaskAssignment,
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """Assign a task to a user."""
    try:
        task = await task_service.assign_task(
            task_id=task_id,
            assignee=assignment.assignee,
            assigned_by=assignment.assigned_by
        )
        
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning task: {str(e)}"
        )


@router.put("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    completion: TaskCompletion,
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """Mark a task as completed."""
    try:
        task = await task_service.complete_task(
            task_id=task_id,
            completed_by=completion.completed_by,
            artifact_ids=completion.artifact_ids,
            completion_notes=completion.completion_notes
        )
        
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing task: {str(e)}"
        )


@router.put("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    cancellation: TaskCancellation,
    task_service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """Cancel a task."""
    try:
        task = await task_service.cancel_task(
            task_id=task_id,
            canceled_by=cancellation.canceled_by,
            reason=cancellation.reason
        )
        
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error canceling task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling task: {str(e)}"
        ) 