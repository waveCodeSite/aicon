"""
存储源数据模型
"""

from sqlalchemy import Column, String, Text, Boolean
from src.models.base import BaseModel


class StorageSource(BaseModel):
    """存储源模型 - 支持多个存储配置"""
    __tablename__ = 'storage_sources'

    name = Column(String(100), nullable=False, comment="存储源名称")
    provider = Column(String(50), nullable=False, default="minio", comment="提供商: minio, aws, aliyun, tencent")
    endpoint = Column(String(255), nullable=False, comment="服务端点")
    access_key = Column(String(255), nullable=False, comment="访问密钥ID")
    secret_key = Column(Text, nullable=False, comment="访问密钥Secret(加密存储)")
    bucket = Column(String(100), nullable=False, comment="存储桶名称")
    region = Column(String(50), default="us-east-1", comment="区域")
    secure = Column(Boolean, default=False, comment="是否使用HTTPS")
    is_active = Column(Boolean, default=False, index=True, comment="是否启用")


__all__ = ["StorageSource"]
