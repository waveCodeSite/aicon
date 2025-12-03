"""
视频合成服务 - 视频生成的核心服务（重构版）
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from src.core.exceptions import BusinessLogicError
from src.core.logging import get_logger
from src.models import Chapter, ChapterStatus, Sentence, VideoTask, VideoTaskStatus
from src.services.api_key import APIKeyService
from src.services.base import SessionManagedService
from src.services.chapter import ChapterService
from src.services.video_composition_service import video_composition_service
from src.services.video_task import VideoTaskService
from src.utils.ffmpeg_utils import (
    check_ffmpeg_installed,
    concatenate_videos,
    get_audio_duration,
)
from src.utils.storage import get_storage_client

logger = get_logger(__name__)


class VideoSynthesisService(SessionManagedService):
    """
    视频合成服务（重构版）

    负责视频生成的完整流程编排，将具体操作委托给专门的服务：
    - SubtitleService: 字幕生成和LLM纠错
    - MaterialService: 素材下载
    - VideoCompositionService: 视频合成
    """

    def __init__(self):
        """初始化视频合成服务"""
        super().__init__()
        self.storage_client = None
        logger.debug("VideoSynthesisService 初始化完成")

    async def _get_storage_client(self):
        """获取存储客户端"""
        if self.storage_client is None:
            self.storage_client = await get_storage_client()
        return self.storage_client

    async def _validate_chapter_materials(self, chapter: Chapter) -> None:
        """
        验证章节素材是否准备好

        Args:
            chapter: 章节对象

        Raises:
            BusinessLogicError: 如果章节状态不正确或素材不完整
        """
        # 检查章节状态
        if chapter.status != ChapterStatus.MATERIALS_PREPARED.value:
            raise BusinessLogicError(
                f"章节状态不正确，当前状态: {chapter.status}，需要: {ChapterStatus.MATERIALS_PREPARED.value}"
            )

        # 获取章节的所有句子
        chapter_service = ChapterService(self.db_session)
        sentences = await chapter_service.get_sentences(chapter.id)

        if not sentences:
            raise BusinessLogicError("章节没有句子")

        # 检查每个句子是否有必要的素材
        missing_materials = []
        for sentence in sentences:
            if not sentence.image_url:
                missing_materials.append(f"句子 {sentence.id} 缺少图片")
            if not sentence.audio_url:
                missing_materials.append(f"句子 {sentence.id} 缺少音频")

        if missing_materials:
            raise BusinessLogicError(
                f"章节素材不完整:\n" + "\n".join(missing_materials[:5])  # 只显示前5个
            )

        logger.info(f"章节素材验证通过: {chapter.id}, 共 {len(sentences)} 个句子")

    async def _process_sentence_async(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict,
            semaphore: asyncio.Semaphore,
            api_key=None,
            model: Optional[str] = None
    ) -> Tuple[bool, Optional[Path], Optional[Exception]]:
        """
        异步处理单个句子（带并发控制）

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置
            semaphore: 并发控制信号量
            api_key: API密钥（可选，用于LLM纠错）
            model: 模型名称（可选）

        Returns:
            (是否成功, 视频路径, 异常对象)
        """
        async with semaphore:
            try:
                video_path = await video_composition_service.synthesize_sentence_video(
                    sentence=sentence,
                    temp_dir=temp_dir,
                    index=index,
                    gen_setting=gen_setting,
                    api_key=api_key,
                    model=model
                )
                return True, video_path, None
            except Exception as e:
                logger.error(f"处理句子失败: {sentence.id}, 错误: {e}")
                return False, None, e

    # 保留原有的方法签名以兼容测试代码
    async def _synthesize_sentence_video(
            self,
            sentence: Sentence,
            temp_dir: Path,
            index: int,
            gen_setting: dict
    ) -> Path:
        """
        合成单个句子的视频（兼容方法）

        这个方法保留是为了兼容现有的测试代码。
        实际实现已经移到 VideoCompositionService。

        Args:
            sentence: 句子对象
            temp_dir: 临时目录
            index: 句子索引
            gen_setting: 生成设置

        Returns:
            生成的视频文件路径
        """
        return await video_composition_service.synthesize_sentence_video(
            sentence=sentence,
            temp_dir=temp_dir,
            index=index,
            gen_setting=gen_setting,
            api_key=None,  # 测试时不使用LLM纠错
            model=None
        )

    async def synthesize_video(self, video_task_id: str) -> dict:
        """
        合成视频（主流程）

        Args:
            video_task_id: 视频任务ID

        Returns:
            统计信息字典
        """
        async with self:
            temp_dir = None
            try:
                # 检查FFmpeg
                if not check_ffmpeg_installed():
                    raise BusinessLogicError("FFmpeg未安装或不可用")

                # 1. 加载视频任务
                task_service = VideoTaskService(self.db_session)
                task = await task_service.get_video_task_by_id(video_task_id)

                # 2. 验证任务状态
                if task.status not in [VideoTaskStatus.PENDING.value, VideoTaskStatus.FAILED.value]:
                    raise BusinessLogicError(
                        f"任务状态不正确: {task.status}"
                    )

                # 3. 更新状态为验证中
                await task_service.update_task_status(task.id, VideoTaskStatus.VALIDATING)

                # 4. 加载章节并验证素材
                chapter_service = ChapterService(self.db_session)
                chapter = await chapter_service.get_chapter_by_id(task.chapter_id)
                await self._validate_chapter_materials(chapter)

                # 5. 解析生成设置
                gen_setting = task.get_gen_setting()

                # 6. 如果任务包含api_key_id，加载API密钥用于LLM纠错
                api_key = None
                model = None
                if task.api_key_id:
                    try:
                        api_key_service = APIKeyService(self.db_session)
                        api_key = await api_key_service.get_api_key_by_id(
                            str(task.api_key_id),
                            str(task.user_id)
                        )
                        logger.info(f"[LLM纠错] 已加载API密钥，将使用LLM纠正字幕")
                        
                        # 可以从gen_setting中获取模型配置
                        model = gen_setting.get("llm_model")
                    except Exception as e:
                        logger.warning(f"加载API密钥失败，将不使用LLM纠错: {e}")
                        api_key = None

                # 7. 更新状态为下载素材
                await task_service.update_task_status(task.id, VideoTaskStatus.DOWNLOADING_MATERIALS)

                # 8. 获取所有句子
                sentences = await chapter_service.get_sentences(task.chapter_id)
                task.total_sentences = len(sentences)
                await self.db_session.flush()

                # 9. 创建临时目录
                temp_dir = Path(tempfile.mkdtemp(prefix="video_synthesis_"))
                logger.info(f"创建临时目录: {temp_dir}")

                # 10. 更新状态为合成视频
                await task_service.update_task_status(
                    task.id,
                    VideoTaskStatus.SYNTHESIZING_VIDEOS
                )

                # 11. 并发处理所有句子
                semaphore = asyncio.Semaphore(3)  # 限制并发数为3
                tasks_list = [
                    self._process_sentence_async(
                        sentence, temp_dir, idx, gen_setting, semaphore, api_key, model
                    )
                    for idx, sentence in enumerate(sentences)
                ]

                results = await asyncio.gather(*tasks_list, return_exceptions=True)

                # 12. 统计结果
                success_count = 0
                failed_count = 0
                video_paths = []

                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"句子 {idx} 处理异常: {result}")
                    else:
                        success, video_path, error = result
                        if success and video_path:
                            success_count += 1
                            video_paths.append(video_path)
                            # 更新进度
                            progress = int((idx + 1) / len(sentences) * 80)  # 0-80%
                            task.update_progress(progress)
                            task.current_sentence_index = idx
                            await self.db_session.flush()
                        else:
                            failed_count += 1

                if failed_count > 0:
                    raise BusinessLogicError(
                        f"部分句子处理失败: 成功={success_count}, 失败={failed_count}"
                    )

                # 13. 更新API密钥使用统计（如果使用了LLM纠错）
                if api_key:
                    try:
                        api_key_service = APIKeyService(self.db_session)
                        # 每个句子调用一次LLM，所以使用次数为句子数量
                        for _ in range(len(sentences)):
                            await api_key_service.update_usage(api_key.id, str(task.user_id))
                        logger.info(f"[LLM纠错] 已更新API密钥使用统计，共 {len(sentences)} 次")
                    except Exception as e:
                        logger.warning(f"更新API密钥使用统计失败: {e}")

                # 14. 更新状态为拼接中
                await task_service.update_task_status(task.id, VideoTaskStatus.CONCATENATING)
                task.update_progress(85)
                await self.db_session.flush()

                # 15. 拼接视频
                final_video_path = temp_dir / "final_video.mp4"
                concat_file_path = temp_dir / "concat.txt"

                success = concatenate_videos(video_paths, final_video_path, concat_file_path)
                if not success:
                    raise BusinessLogicError("视频拼接失败")

                # 16. 更新状态为上传中
                await task_service.update_task_status(task.id, VideoTaskStatus.UPLOADING)
                task.update_progress(90)
                await self.db_session.flush()

                # 17. 上传到MinIO
                storage = await self._get_storage_client()
                video_key = storage.generate_object_key(
                    str(task.user_id),
                    f"chapter_{task.chapter_id}_video.mp4",
                    prefix="videos"
                )

                # 读取文件并上传
                from fastapi import UploadFile
                with open(final_video_path, 'rb') as f:
                    upload_file = UploadFile(
                        filename=f"chapter_{task.chapter_id}_video.mp4",
                        file=f
                    )
                    result = await storage.upload_file(
                        str(task.user_id),
                        upload_file,
                        object_key=video_key
                    )

                video_key = result["object_key"]

                # 18. 获取视频时长
                duration = int(get_audio_duration(str(final_video_path)) or 0)

                # 19. 标记任务完成
                await task_service.mark_task_completed(task.id, video_key, duration)
                task.update_progress(100)
                await self.db_session.flush()

                logger.info(f"视频合成完成: task_id={task.id}, video_key={video_key}")

                return {
                    "total": len(sentences),
                    "success": success_count,
                    "failed": failed_count,
                    "video_key": video_key,
                    "duration": duration
                }

            except Exception as e:
                logger.error(f"视频合成失败: {e}", exc_info=True)

                # 标记任务失败
                try:
                    task_service = VideoTaskService(self.db_session)
                    await task_service.mark_task_failed(
                        video_task_id,
                        str(e)
                    )
                except Exception as mark_error:
                    logger.error(f"标记任务失败时出错: {mark_error}")

                raise

            finally:
                # 清理临时目录
                if temp_dir and temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                        logger.info(f"清理临时目录: {temp_dir}")
                    except Exception as e:
                        logger.error(f"清理临时目录失败: {e}")


# 创建全局实例
video_synthesis_service = VideoSynthesisService()

__all__ = [
    "VideoSynthesisService",
    "video_synthesis_service",
]
