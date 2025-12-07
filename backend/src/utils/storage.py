"""
S3兼容对象存储客户端 - 支持动态配置
支持: AWS S3, MinIO, 阿里云OSS, 腾讯云COS, 华为云OBS等
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class StorageError(Exception):
    """存储异常"""
    pass


class StorageConfig:
    """存储配置"""
    def __init__(
        self,
        provider: str = "minio",
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "aicg-files",
        region: str = "us-east-1",
        secure: bool = False,
    ):
        self.provider = provider
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.region = region
        self.secure = secure

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageConfig":
        return cls(
            provider=data.get("provider", "minio"),
            endpoint=data.get("endpoint", "localhost:9000"),
            access_key=data.get("access_key", "minioadmin"),
            secret_key=data.get("secret_key", "minioadmin"),
            bucket=data.get("bucket", "aicg-files"),
            region=data.get("region", "us-east-1"),
            secure=data.get("secure", False),
        )

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """从环境变量创建配置"""
        return cls(
            provider="minio",
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET_NAME,
            region=settings.MINIO_REGION,
            secure=settings.MINIO_SECURE,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "bucket": self.bucket,
            "region": self.region,
            "secure": self.secure,
        }

    @property
    def endpoint_url(self) -> str:
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}"


class S3Storage:
    """S3兼容对象存储客户端"""

    def __init__(self, config: Optional[StorageConfig] = None):
        self._config = config or StorageConfig.from_env()
        self._client = None

    @property
    def config(self) -> StorageConfig:
        return self._config

    @config.setter
    def config(self, value: StorageConfig):
        self._config = value
        self._client = None  # 重置客户端

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._config.endpoint_url,
                aws_access_key_id=self._config.access_key,
                aws_secret_access_key=self._config.secret_key,
                region_name=self._config.region,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    @property
    def bucket_name(self) -> str:
        return self._config.bucket

    def reload_config(self, config: StorageConfig):
        """重新加载配置"""
        self._config = config
        self._client = None
        logger.info(f"存储配置已更新: provider={config.provider}, endpoint={config.endpoint}")

    async def ensure_bucket_exists(self) -> None:
        """确保存储桶存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                try:
                    self.client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self._config.region}
                        if self._config.region != "us-east-1" else {}
                    )
                    logger.info(f"创建存储桶: {self.bucket_name}")
                except ClientError as ce:
                    logger.error(f"创建存储桶失败: {ce}")
                    raise StorageError(f"无法创建存储桶: {str(ce)}")
            else:
                logger.error(f"检查存储桶失败: {e}")
                raise StorageError(f"存储桶访问失败: {str(e)}")

    def generate_object_key(self, user_id: str, filename: str, prefix: str = "uploads") -> str:
        """生成对象键"""
        file_ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{file_ext}"
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{prefix}/{user_id}/{date_str}/{unique_name}"

    async def upload_file(
        self,
        user_id: str,
        file: UploadFile,
        object_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """上传文件"""
        try:
            await self.ensure_bucket_exists()

            if not object_key:
                object_key = self.generate_object_key(user_id, file.filename)

            if metadata is None:
                metadata = {}

            import urllib.parse
            encoded_filename = urllib.parse.quote(file.filename or "", safe="") if file.filename else ""

            metadata.update({
                "original_filename": encoded_filename,
                "content_type": file.content_type or "application/octet-stream",
                "upload_time": datetime.now().isoformat(),
                "user_id": str(user_id),
            })

            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

            self.client.upload_fileobj(
                file.file,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": file.content_type or "application/octet-stream",
                    "Metadata": metadata,
                }
            )

            logger.info(f"文件上传成功: {object_key}, 大小: {file_size} bytes")

            return {
                "bucket": self.bucket_name,
                "object_key": object_key,
                "size": file_size,
                "url": self.get_presigned_url(object_key),
            }

        except ClientError as e:
            logger.error(f"上传失败: {e}")
            raise StorageError(f"文件上传失败: {str(e)}")

    async def upload_file_from_path(
        self,
        user_id: str,
        file_path: str,
        original_filename: str,
        object_key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """从本地路径上传文件"""
        try:
            if not object_key:
                object_key = self.generate_object_key(user_id, original_filename)

            if metadata is None:
                metadata = {}

            file_size = Path(file_path).stat().st_size

            import urllib.parse
            encoded_filename = urllib.parse.quote(original_filename or "", safe="")

            metadata.update({
                "original_filename": encoded_filename,
                "upload_time": datetime.now().isoformat(),
                "user_id": str(user_id),
            })

            self.client.upload_file(
                file_path,
                self.bucket_name,
                object_key,
                ExtraArgs={"Metadata": metadata}
            )

            logger.info(f"文件上传成功: {object_key}, 大小: {file_size} bytes")

            return {
                "bucket": self.bucket_name,
                "object_key": object_key,
                "size": file_size,
                "url": self.get_presigned_url(object_key),
            }

        except ClientError as e:
            logger.error(f"上传失败: {e}")
            raise StorageError(f"文件上传失败: {str(e)}")

    def get_presigned_url(
        self,
        object_key: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """获取预签名URL"""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=int(expires.total_seconds()),
            )
            return url
        except ClientError as e:
            logger.error(f"获取预签名URL失败: {e}")
            raise StorageError(f"获取预签名URL失败: {str(e)}")

    async def download_file(self, object_key: str) -> bytes:
        """下载文件"""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"下载文件失败: {e}")
            raise StorageError(f"下载文件失败: {str(e)}")

    async def download_file_to_path(self, object_key: str, dest_path: str) -> None:
        """下载文件到指定路径"""
        try:
            Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
            self.client.download_file(self.bucket_name, object_key, dest_path)
            logger.info(f"文件下载成功: {object_key} -> {dest_path}")
        except ClientError as e:
            logger.error(f"下载文件失败: {e}")
            raise StorageError(f"下载文件失败: {str(e)}")

    async def delete_file(self, object_key: str) -> bool:
        """删除文件"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            logger.info(f"文件删除成功: {object_key}")
            return True
        except ClientError as e:
            logger.error(f"删除文件失败: {e}")
            return False

    async def copy_file(
        self,
        source_object_key: str,
        dest_object_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """复制文件"""
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_object_key}
            extra_args = {"MetadataDirective": "REPLACE", "Metadata": metadata} if metadata else {}
            self.client.copy_object(
                Bucket=self.bucket_name,
                Key=dest_object_key,
                CopySource=copy_source,
                **extra_args
            )
            logger.info(f"文件复制成功: {source_object_key} -> {dest_object_key}")
            return True
        except ClientError as e:
            logger.error(f"复制文件失败: {e}")
            return False

    async def list_files(
        self,
        prefix: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出文件"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )

            files = []
            for obj in response.get("Contents", []):
                if obj["Key"].endswith("/"):
                    continue
                files.append({
                    "object_key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat() if obj.get("LastModified") else None,
                    "etag": obj.get("ETag", "").strip('"'),
                    "url": self.get_presigned_url(obj["Key"]),
                })

            return files

        except ClientError as e:
            logger.error(f"列出文件失败: {e}")
            raise StorageError(f"列出文件失败: {str(e)}")

    async def get_file_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return {
                "object_key": object_key,
                "size": response["ContentLength"],
                "last_modified": response["LastModified"].isoformat() if response.get("LastModified") else None,
                "etag": response.get("ETag", "").strip('"'),
                "content_type": response.get("ContentType"),
                "metadata": response.get("Metadata", {}),
                "url": self.get_presigned_url(object_key),
            }
        except ClientError as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    async def file_exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """测试存储连接"""
        try:
            self.client.list_buckets()
            return {"success": True, "message": "连接成功"}
        except ClientError as e:
            return {"success": False, "message": str(e)}


# 全局存储客户端实例
storage_client = S3Storage()

# 兼容旧代码的别名
MinIOStorage = S3Storage


async def get_storage_client() -> S3Storage:
    """获取存储客户端实例"""
    await storage_client.ensure_bucket_exists()
    return storage_client


async def reload_storage_config_from_db(db_session) -> None:
    """从数据库重新加载存储配置（从StorageSource表）"""
    from sqlalchemy import select
    from src.models.storage_source import StorageSource

    result = await db_session.execute(
        select(StorageSource).where(StorageSource.is_active == True)
    )
    source = result.scalar_one_or_none()

    if source:
        config = StorageConfig(
            provider=source.provider,
            endpoint=source.endpoint,
            access_key=source.access_key,
            secret_key=source.secret_key,
            bucket=source.bucket,
            region=source.region,
            secure=source.secure,
        )
        storage_client.reload_config(config)
        logger.info(f"已加载存储源: {source.name}")


__all__ = [
    "S3Storage",
    "MinIOStorage",
    "StorageConfig",
    "StorageError",
    "storage_client",
    "get_storage_client",
    "reload_storage_config_from_db",
]
