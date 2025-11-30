"""
任务管理 API
"""

from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user_required
from src.api.schemas.task import TaskStatusResponse
from src.core.logging import get_logger
from src.models.user import User
from src.tasks.task import celery_app

logger = get_logger(__name__)

router = APIRouter()


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
        task_id: str,
        current_user: User = Depends(get_current_user_required)
):
    """
    获取任务状态
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_result.status,
        result=task_result.result if task_result.ready() else None
    )


__all__ = ["router"]
