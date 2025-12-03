"""
素材服务 - 处理素材下载和管理

负责:
- 从MinIO下载素材（图片、音频）
- 解析预签名URL和对象键
- 批量下载优化
"""

from pathlib import Path
from urllib.parse import urlparse, unquote

from src.core.logging import get_logger
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class MaterialService:
    """素材服务 - 处理素材下载和管理"""

    def __init__(self):
        """初始化素材服务"""
        self.storage_client = None

    async def _get_storage_client(self):
        """获取存储客户端"""
        if self.storage_client is None:
            self.storage_client = await get_storage_client()
        return self.storage_client

    async def fetch_material_from_minio(self, object_key_or_url: str, dest_path: Path) -> None:
        """
        从MinIO下载素材（支持对象键或预签名URL）

        Args:
            object_key_or_url: MinIO对象键或预签名URL
            dest_path: 目标路径
        """
        try:
            # 判断是URL还是对象键
            if object_key_or_url.startswith('http://') or object_key_or_url.startswith('https://'):
                # 是预签名URL，提取对象键
                # URL格式: http://localhost:9000/bucket/path/to/file.jpg?X-Amz-...
                parsed = urlparse(object_key_or_url)
                # 路径格式: /bucket/path/to/file.jpg
                path_parts = parsed.path.split('/', 2)  # ['', 'bucket', 'path/to/file.jpg']

                if len(path_parts) >= 3:
                    object_key = unquote(path_parts[2])  # 'path/to/file.jpg'
                    logger.debug(f"从URL提取对象键: {object_key}")
                else:
                    raise ValueError(f"无法从URL提取对象键: {object_key_or_url}")

                # 使用对象键从MinIO下载
                storage = await self._get_storage_client()
                await storage.download_file_to_path(object_key, str(dest_path))
                logger.debug(f"下载素材成功: {object_key} -> {dest_path}")
            else:
                # 是对象键，直接从MinIO下载
                logger.debug(f"从MinIO下载素材: {object_key_or_url}")
                storage = await self._get_storage_client()
                await storage.download_file_to_path(object_key_or_url, str(dest_path))
                logger.debug(f"下载素材成功: {object_key_or_url} -> {dest_path}")

        except Exception as e:
            logger.error(
                f"下载素材失败: {object_key_or_url[:100] if len(object_key_or_url) > 100 else object_key_or_url}, 错误: {e}")
            raise


# 创建全局实例
material_service = MaterialService()

__all__ = [
    "MaterialService",
    "material_service",
]
