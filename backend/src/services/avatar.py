"""
头像上传服务模块

提供服务：
- 头像文件验证和格式检查
- 图片压缩和尺寸调整
- S3兼容对象存储管理
- 头像URL生成和管理

支持格式：JPG, PNG, WebP
最大尺寸：5MB
输出尺寸：200x200像素（居中裁剪）
"""

import hashlib
import io
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image

from src.core.config import settings
from src.core.exceptions import ValidationError


class AvatarService:
    """头像上传服务类"""

    def __init__(self):
        """初始化头像服务"""
        protocol = "https" if settings.MINIO_SECURE else "http"
        endpoint_url = f"{protocol}://{settings.MINIO_ENDPOINT}"

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = settings.AVATAR_BUCKET_NAME

    async def _ensure_bucket_exists(self):
        """确保头像存储桶存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.client.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={"LocationConstraint": settings.MINIO_REGION}
                if settings.MINIO_REGION != "us-east-1" else {}
            )

    async def _validate_image(self, file_data: bytes, filename: str) -> str:
        """验证图片文件"""
        if len(file_data) > settings.MAX_AVATAR_SIZE:
            raise ValidationError(f"图片文件大小不能超过 {settings.MAX_AVATAR_SIZE // (1024 * 1024)}MB")

        file_ext = filename.lower().split('.')[-1]
        if file_ext not in settings.ALLOWED_AVATAR_TYPES:
            raise ValidationError(f"不支持的图片格式，支持的格式: {', '.join(settings.ALLOWED_AVATAR_TYPES)}")

        try:
            img = Image.open(io.BytesIO(file_data))
            img.verify()
            img = Image.open(io.BytesIO(file_data))
            width, height = img.size
            if width > 2000 or height > 2000:
                raise ValidationError("图片尺寸过大，最大允许 2000x2000")
            return img.format.lower()
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("无效的图片文件")

    async def _resize_image(self, file_data: bytes, format_type: str = "JPEG") -> bytes:
        """调整图片尺寸"""
        img = Image.open(io.BytesIO(file_data))

        if format_type.lower() == 'png' and img.mode != 'RGBA':
            img = img.convert('RGBA')
        elif img.mode not in ['RGB', 'RGBA']:
            img = img.convert('RGB')

        width, height = img.size
        target_width, target_height = settings.AVATAR_DEFAULT_SIZE

        scale = min(target_width / width, target_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        if new_width != width or new_height != height:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        background = Image.new('RGB', (target_width, target_height), (255, 255, 255))
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2

        if img.mode == 'RGBA':
            background.paste(img, (x_offset, y_offset), img)
        else:
            background.paste(img, (x_offset, y_offset))

        output = io.BytesIO()
        background.save(output, format=format_type, quality=85, optimize=True)
        output.seek(0)
        return output.getvalue()

    def _generate_object_name(self, user_id: str, original_filename: str, format_type: str) -> str:
        """生成对象存储名称"""
        file_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        timestamp = int(__import__('time').time())
        ext = format_type.lower()
        return f"avatars/{user_id}/{file_hash}_{timestamp}.{ext}"

    async def upload_avatar(self, user_id: str, file_data: bytes, filename: str) -> str:
        """上传头像"""
        await self._ensure_bucket_exists()
        format_type = await self._validate_image(file_data, filename)
        processed_data = await self._resize_image(file_data, format_type)
        object_name = self._generate_object_name(user_id, filename, format_type)

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=object_name,
            Body=processed_data,
            ContentType=f"image/{format_type.lower()}"
        )

        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"

    async def delete_avatar(self, avatar_url: str) -> bool:
        """删除头像"""
        if not avatar_url or f"/{self.bucket_name}/" not in avatar_url:
            return False

        object_name = avatar_url.split(f"/{self.bucket_name}/", 1)[1]

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_name)
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError:
            return False

    async def get_avatar_info(self, avatar_url: str) -> Optional[dict]:
        """获取头像信息"""
        if not avatar_url or f"/{self.bucket_name}/" not in avatar_url:
            return None

        object_name = avatar_url.split(f"/{self.bucket_name}/", 1)[1]

        try:
            stat = self.client.head_object(Bucket=self.bucket_name, Key=object_name)
            return {
                "object_name": object_name,
                "size": stat["ContentLength"],
                "last_modified": stat["LastModified"],
                "content_type": stat["ContentType"],
                "etag": stat.get("ETag", "").strip('"')
            }
        except ClientError:
            return None


avatar_service = AvatarService()
