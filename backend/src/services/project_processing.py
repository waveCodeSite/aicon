"""
项目文件处理服务 - 协调文本解析和数据保存

提供服务：
- 文件内容解析处理流程
- 章节段落句子数据保存
- 项目状态和进度跟踪
- 数据清理和统计更新

设计原则：
- 使用SessionManagedService独立管理会话
- 协调多个服务完成复杂业务流程
- 提供完整的处理状态跟踪
- 异常处理和回滚机制
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.core.exceptions import NotFoundError
from src.core.logging import get_logger
from src.models.chapter import Chapter
from src.models.paragraph import Paragraph
from src.models.project import Project, ProjectStatus
from src.models.sentence import Sentence
from src.services.base import SessionManagedService

logger = get_logger(__name__)


class ProjectProcessingService(SessionManagedService):
    """
    项目文件处理服务

    负责协调文本解析和数据保存的完整流程，包括：
    1. 获取项目信息
    2. 清理已有数据
    3. 更新处理状态
    4. 解析文本内容
    5. 保存解析结果
    6. 更新统计信息

    该服务独立管理数据库会话，适用于后台任务和批处理场景。
    """

    def __init__(self):
        super().__init__()  # 调用父类初始化方法
        self.text_parser_service = None
        # 延迟导入text_parser_service避免循环依赖

    async def _get_text_parser_service(self):
        """延迟导入text_parser_service"""
        if self.text_parser_service is None:
            from src.services.text_parser import text_parser_service
            self.text_parser_service = text_parser_service
        return self.text_parser_service

    async def process_uploaded_file(self, project_id: str, file_content: str) -> Dict:
        """
        处理上传的文件 - 完整的文本解析和数据保存流程

        这是一个完整的文件处理工作流，包含数据清理、文本解析、
        数据保存和状态更新等步骤。整个操作在事务中执行，失败时自动回滚。

        Args:
            project_id: 项目ID，必须是有效的UUID
            file_content: 文件的文本内容，编码应为UTF-8

        Returns:
            Dict[str, Any]: 处理结果，包含：
                - success: 处理是否成功
                - project_id: 项目ID
                - chapters_count: 章节数量
                - paragraphs_count: 段落数量
                - sentences_count: 句子数量
                - message: 处理结果消息

        Raises:
            NotFoundError: 当项目不存在时
            ValidationError: 当文件内容无效时
            BusinessLogicError: 当项目状态不允许处理时
            DatabaseError: 当数据库操作失败时
        """
        try:
            # 1. 获取项目信息
            project = await self._get_project(project_id)

            # 2. 清理已有的数据（避免重复处理）
            await self._clean_existing_data(project_id)

            # 3. 更新项目状态为处理中（10%进度）
            await self._update_project_status(project, ProjectStatus.PARSING, 10)

            # 4. 解析文本内容
            logger.info(f"开始解析项目 {project_id} 的文本内容，长度: {len(file_content)} 字符")
            chapters_data, paragraphs_data, sentences_data = await self._parse_text_content(
                project_id, file_content
            )

            # 5. 更新进度到30%（解析完成）
            await self._update_project_status(project, ProjectStatus.PARSING, 30)

            # 6. 批量保存到数据库
            await self._save_parsed_content(
                project_id, chapters_data, paragraphs_data, sentences_data
            )

            # 7. 更新项目统计信息
            await self._update_project_statistics(project)

            # 8. 标记项目为已解析（100%完成）
            await self._update_project_status(project, ProjectStatus.PARSED, 100)

            # 提交所有更改
            await self.commit()

            logger.info(f"项目 {project_id} 文件处理完成")

            return {
                'success': True,
                'project_id': project_id,
                'chapters_count': len(chapters_data),
                'paragraphs_count': len(paragraphs_data),
                'sentences_count': len(sentences_data),
                'message': '文件处理完成'
            }

        except Exception as e:
            # 发生错误时回滚事务
            await self.rollback()
            logger.error(f"处理项目 {project_id} 文件失败: {e}")
            raise  # 重新抛出异常，由上层处理

    async def _get_project(self, project_id: str) -> Project:
        """
        获取项目信息

        Args:
            project_id: 项目ID

        Returns:
            Project: 项目对象

        Raises:
            NotFoundError: 当项目不存在时
        """
        project = await self.get(Project, project_id)
        if not project:
            raise NotFoundError("项目不存在", resource_type="project", resource_id=project_id)
        return project

    async def _clean_existing_data(self, project_id: str) -> None:
        """
        清理项目已有的数据，避免重复处理

        删除项目相关的所有章节、段落、句子数据，并重置项目统计信息。
        这个操作通常在重新解析文件之前执行。

        Args:
            project_id: 项目ID
        """
        logger.info(f"开始清理项目 {project_id} 的已有数据")

        # 1. 删除句子数据
        deleted_sentences = await Sentence.delete_by_project_id(self.db_session, project_id)
        logger.info(f"删除了 {deleted_sentences} 个句子")

        # 2. 删除段落数据
        deleted_paragraphs = await Paragraph.delete_by_project_id(self.db_session, project_id)
        logger.info(f"删除了 {deleted_paragraphs} 个段落")

        # 3. 删除章节数据
        deleted_chapters = await Chapter.delete_by_project_id(self.db_session, project_id)
        logger.info(f"删除了 {deleted_chapters} 个章节")

        # 4. 重置项目统计信息
        project = await self.get(Project, project_id)
        if project:
            project.chapter_count = 0
            project.paragraph_count = 0
            project.sentence_count = 0
            project.word_count = 0
            project.processing_progress = 0
            project.error_message = None
            project.completed_at = None
            await self.flush()

        logger.info(f"项目 {project_id} 数据清理完成")

    async def _update_project_status(self, project: Project, status: ProjectStatus,
                                     progress: int, error_message: Optional[str] = None) -> None:
        """
        更新项目状态和进度

        更新项目的处理状态、进度百分比，可选择设置错误信息。
        完成时自动设置完成时间。

        Args:
            project: 项目对象
            status: 新的项目状态
            progress: 进度百分比（0-100）
            error_message: 可选的错误信息
        """
        project.status = status.value
        project.processing_progress = progress
        if error_message:
            project.error_message = error_message
        elif status == ProjectStatus.PARSED:
            project.error_message = None
            project.completed_at = datetime.utcnow()

        await self.flush()
        logger.debug(f"更新项目状态: ID={project.id}, 状态={status.value}, 进度={progress}%")

    async def _parse_text_content(self, project_id: str, file_content: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        解析文本内容

        Args:
            project_id: 项目ID
            file_content: 文件内容

        Returns:
            (chapters_data, paragraphs_data, sentences_data)
        """
        text_parser_service = await self._get_text_parser_service()

        # 根据项目设置解析选项
        parse_options = {
            'min_chapter_length': 1000,  # 最小章节长度
        }

        return await text_parser_service.parse_to_models(project_id, file_content, parse_options)

    async def _save_parsed_content(self, project_id: str, chapters_data: List[Dict],
                                   paragraphs_data: List[Dict], sentences_data: List[Dict]) -> None:
        """
        保存解析的内容到数据库

        将文本解析的结果保存到数据库，包含章节、段落、句子三层结构。
        使用批量操作提高性能，并维护数据间的关联关系。

        Args:
            project_id: 项目ID
            chapters_data: 章节数据列表
            paragraphs_data: 段落数据列表
            sentences_data: 句子数据列表
        """
        logger.info(f"开始保存解析内容: {len(chapters_data)} 章节, {len(paragraphs_data)} 段落, {len(sentences_data)} 句子")

        # 1. 批量保存章节
        chapter_ids = await Chapter.batch_create(self.db_session, chapters_data)
        logger.info(f"成功保存 {len(chapter_ids)} 个章节")

        # 2. 更新段落数据中的chapter_id，并批量保存段落
        current_para_index = 0
        para_chapter_mapping = []

        for chapter_idx, chapter_data in enumerate(chapters_data):
            # 计算当前章节的段落数量
            chapter_paragraph_count = chapter_data['paragraph_count']
            if current_para_index + chapter_paragraph_count > len(paragraphs_data):
                # 数据不一致，使用实际可用的数量
                chapter_paragraph_count = len(paragraphs_data) - current_para_index

            # 更新段落的chapter_id
            for i in range(chapter_paragraph_count):
                para_index = current_para_index + i
                if para_index < len(paragraphs_data):
                    paragraphs_data[para_index]['chapter_id'] = chapter_ids[chapter_idx]
                    para_chapter_mapping.append(chapter_ids[chapter_idx])

            current_para_index += chapter_paragraph_count

        # 批量保存段落
        paragraph_ids = await Paragraph.batch_create(self.db_session, paragraphs_data[:current_para_index], para_chapter_mapping)
        logger.info(f"成功保存 {len(paragraph_ids)} 个段落")

        # 3. 更新句子数据中的paragraph_id，并批量保存句子
        current_sent_index = 0
        sent_para_mapping = []

        for para_idx, paragraph_data in enumerate(paragraphs_data[:current_para_index]):
            # 计算当前段落的句子数量
            para_sentence_count = paragraph_data.get('sentence_count', 0)
            if current_sent_index + para_sentence_count > len(sentences_data):
                # 数据不一致，使用实际可用的数量
                para_sentence_count = len(sentences_data) - current_sent_index

            # 更新句子的paragraph_id
            for i in range(para_sentence_count):
                sent_index = current_sent_index + i
                if sent_index < len(sentences_data):
                    sentences_data[sent_index]['paragraph_id'] = paragraph_ids[para_idx]
                    sent_para_mapping.append(paragraph_ids[para_idx])

            current_sent_index += para_sentence_count

        # 批量保存句子
        sentence_ids = await Sentence.batch_create(self.db_session, sentences_data[:current_sent_index], sent_para_mapping)
        logger.info(f"成功保存 {len(sentence_ids)} 个句子")

    async def _update_project_statistics(self, project: Project) -> None:
        """
        更新项目统计信息

        重新计算并更新项目的各项统计数据，包括章节数、段落数、
        句子数和总字数。这些数据用于显示和统计分析。

        Args:
            project: 项目对象
        """
        # 统计章节数量
        chapter_count = await Chapter.count_by_project_id(self.db_session, project.id)
        project.chapter_count = chapter_count

        # 统计段落数量
        paragraphs = await Paragraph.get_by_project_id(self.db_session, project.id)
        project.paragraph_count = len(paragraphs)

        # 统计句子数量
        sentences = await Sentence.get_by_project_id(self.db_session, project.id)
        project.sentence_count = len(sentences)

        # 统计总字数
        total_word_count = 0
        for paragraph in paragraphs:
            total_word_count += paragraph.word_count or 0
        project.word_count = total_word_count

        await self.flush()
        logger.info(f"项目 {project.id} 统计信息更新完成: {chapter_count}章节, {len(paragraphs)}段落, {len(sentences)}句子, {total_word_count}字")

    async def get_processing_status(self, project_id: str) -> Dict:
        """
        获取项目处理状态

        返回项目的详细状态信息，包括处理进度、统计数据和错误信息。
        用于监控处理进度和状态查询。

        Args:
            project_id: 项目ID

        Returns:
            Dict[str, Any]: 状态信息，包含：
                - success: 查询是否成功
                - project_id: 项目ID
                - status: 当前状态
                - processing_progress: 处理进度百分比
                - chapters_count: 章节数量
                - paragraphs_count: 段落数量
                - sentences_count: 句子数量
                - word_count: 总字数
                - error_message: 错误信息（如果有）
                - created_at: 创建时间
                - updated_at: 更新时间
                - completed_at: 完成时间

        Raises:
            NotFoundError: 当项目不存在时
        """
        project = await self._get_project(project_id)

        # 获取各层级的统计
        chapter_count = await Chapter.count_by_project_id(self.db_session, project_id)
        paragraphs = await Paragraph.get_by_project_id(self.db_session, project_id)
        sentence_count = len(await Sentence.get_by_project_id(self.db_session, project_id))

        return {
            'success': True,
            'project_id': project_id,
            'status': project.status,
            'processing_progress': project.processing_progress,
            'chapters_count': chapter_count,
            'paragraphs_count': len(paragraphs),
            'sentences_count': sentence_count,
            'word_count': project.word_count or 0,
            'error_message': project.error_message,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None,
            'completed_at': project.completed_at.isoformat() if project.completed_at else None,
        }


# 全局实例
project_processing_service = ProjectProcessingService()

__all__ = [
    'ProjectProcessingService',
    'project_processing_service',
]
