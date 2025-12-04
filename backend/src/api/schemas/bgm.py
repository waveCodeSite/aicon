"""
BGM相关的Pydantic模式
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import PaginatedResponse, UUIDMixin


class BGMUploadResponse(UUIDMixin):
    """BGM上传响应模型"""
    id: UUID = Field(..., description="BGM ID")
    user_id: UUID = Field(..., description="用户ID")
    name: str = Field(..., description="BGM名称")
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_url: Optional[str] = Field(None, description="文件预签名URL")
    duration: Optional[int] = Field(None, description="音频时长（秒）")
    status: str = Field(..., description="BGM状态")
    created_at: str = Field(..., description="创建时间")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "BGMUploadResponse":
        """从字典创建响应对象"""
        # 处理时间字段
        if 'created_at' in data and data['created_at'] is not None:
            if hasattr(data['created_at'], 'isoformat'):
                data['created_at'] = data['created_at'].isoformat()
        return cls(**data)


class BGMResponse(UUIDMixin):
    """BGM响应模型"""
    id: UUID = Field(..., description="BGM ID")
    user_id: UUID = Field(..., description="用户ID")
    name: str = Field(..., description="BGM名称")
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_url: Optional[str] = Field(None, description="文件预签名URL")
    duration: Optional[int] = Field(None, description="音频时长（秒）")
    status: str = Field(..., description="BGM状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    model_config = {"from_attributes": True}

    @classmethod
    def from_dict(cls, data: dict) -> "BGMResponse":
        """从字典创建响应对象"""
        # 处理时间字段
        time_fields = ['created_at', 'updated_at']
        for field in time_fields:
            if field in data and data[field] is not None:
                if hasattr(data[field], 'isoformat'):
                    data[field] = data[field].isoformat()
        return cls(**data)


class BGMListResponse(PaginatedResponse):
    """BGM列表响应模型"""
    bgms: List[BGMResponse] = Field(..., description="BGM列表")


class BGMDeleteResponse(BaseModel):
    """BGM删除响应模型"""
    success: bool = Field(True, description="删除是否成功")
    message: str = Field("删除成功", description="响应消息")
    bgm_id: str = Field(..., description="删除的BGM ID")


class BGMStatsResponse(BaseModel):
    """BGM统计响应模型"""
    total_count: int = Field(0, description="总BGM数量")
    total_size: int = Field(0, description="总文件大小（字节）")
    total_size_mb: float = Field(0.0, description="总文件大小（MB）")


__all__ = [
    "BGMUploadResponse",
    "BGMResponse",
    "BGMListResponse",
    "BGMDeleteResponse",
    "BGMStatsResponse",
]
