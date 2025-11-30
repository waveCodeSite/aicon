"""
任务相关的Pydantic模式
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    result: Optional[Any] = Field(None, description="任务结果")

    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "SUCCESS",
                "result": {"success": True, "message": "任务完成"}
            }
        }
    }


__all__ = ["TaskStatusResponse"]
