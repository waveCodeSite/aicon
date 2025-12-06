"""
系统设置数据模型
"""

from sqlalchemy import Column, String, Text
from src.models.base import BaseModel


class SystemSetting(BaseModel):
    """系统设置模型 - 键值对存储"""
    __tablename__ = 'system_settings'

    key = Column(String(100), unique=True, nullable=False, index=True, comment="设置键")
    value = Column(Text, nullable=True, comment="设置值")
    description = Column(String(255), nullable=True, comment="设置描述")


__all__ = ["SystemSetting"]
