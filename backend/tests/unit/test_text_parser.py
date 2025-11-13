"""
文本解析服务单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.services.text_parser import (
    TextParserService,
    RegexChapterDetector,
    TextSplitter,
    ChapterDetection,
    ParsedContent
)
from src.utils.text_utils import (
    SentenceSplitter,
    TextAnalyzer,
    SentenceType,
    PunctuationMark
)


class TestTextSplitter:
    """文本分割器测试"""

    def test_split_into_paragraphs_basic(self):
        """测试基础段落分割"""
        text = "这是第一段。\n\n这是第二段。\n\n\n这是第三段。"
        splitter = TextSplitter()
        paragraphs = splitter.split_into_paragraphs(text)

        assert len(paragraphs) == 3
        assert "这是第一段。" in paragraphs[0]
        assert "这是第二段。" in paragraphs[1]
        assert "这是第三段。" in paragraphs[2]

    def test_split_into_paragraphs_empty(self):
        """测试空文本段落分割"""
        splitter = TextSplitter()
        paragraphs = splitter.split_into_paragraphs("")
        assert paragraphs == []

    def test_split_into_sentences_chinese(self):
        """测试中文句子分割"""
        text = "这是第一句话。这是第二句话？这是第三句话！"
        splitter = TextSplitter()
        sentences = splitter.split_into_sentences(text)

        assert len(sentences) == 3
        assert sentences[0] == "这是第一句话。"
        assert sentences[1] == "这是第二句话？"
        assert sentences[2] == "这是第三句话！"

    def test_split_into_sentences_mixed(self):
        """测试中英文混合句子分割"""
        text = "这是中文句子.This is English sentence!这是另一个中文句子？"
        splitter = TextSplitter()
        sentences = splitter.split_into_sentences(text)

        assert len(sentences) >= 2  # 至少分割出2个句子


class TestRegexChapterDetector:
    """正则章节检测器测试"""

    def test_detect_chapters_chinese_numbered(self):
        """检测中文数字章节"""
        text = """
第一章 引言

这是第一章的内容。

第二章 基础概念

这是第二章的内容。

第三章 高级应用

这是第三章的内容。
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        assert len(chapters) == 3
        assert "第一章" in chapters[0].title
        assert "第二章" in chapters[1].title
        assert "第三章" in chapters[2].title
        assert chapters[0].chapter_number == 1
        assert chapters[1].chapter_number == 2
        assert chapters[2].chapter_number == 3

    def test_detect_chapters_numbered(self):
        """检测数字章节"""
        text = """
1. 项目概述

这是项目概述内容。

2. 技术架构

这是技术架构内容。

3. 实现细节

这是实现细节内容。
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        assert len(chapters) == 3
        assert "1." in chapters[0].title or "1、" in chapters[0].title
        assert chapters[0].chapter_number == 1

    def test_detect_chapters_english(self):
        """检测英文章节"""
        text = """
Chapter 1: Introduction

This is chapter 1 content.

Chapter 2: Methodology

This is chapter 2 content.
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        assert len(chapters) == 2
        assert "Chapter 1" in chapters[0].title
        assert "Chapter 2" in chapters[1].title

    def test_detect_chapters_no_chapters(self):
        """检测无章节文本"""
        text = """
这是一段没有明确章节标记的文本。
它包含多个段落。
但没有章节标题。
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        # 应该创建单个章节
        assert len(chapters) == 1
        assert chapters[0].title == "完整文档"
        assert chapters[0].detection_method == "fallback"

    def test_detect_chapters_empty_text(self):
        """测试空文本"""
        detector = RegexChapterDetector()
        chapters = detector.detect_chapters("")

        assert len(chapters) == 1
        assert chapters[0].title == "完整文档"
        assert chapters[0].content == ""


class TestTextParserService:
    """文本解析服务测试"""

    @pytest.fixture
    def parser_service(self):
        """创建解析服务实例"""
        return TextParserService()

    @pytest.mark.asyncio
    async def test_parse_document_basic(self, parser_service):
        """测试基础文档解析"""
        text = """
第一章 项目介绍

这是项目的介绍内容。

1.1 项目背景
项目背景是...

1.2 项目目标
项目目标是...

第二章 技术实现

这是技术实现的内容。
        """.strip()

        result = await parser_service.parse_document(text)

        assert isinstance(result, ParsedContent)
        assert len(result.chapters) >= 1
        assert len(result.paragraphs) >= 1
        assert len(result.sentences) >= 1
        assert result.metadata['chapter_count'] == len(result.chapters)
        assert result.metadata['paragraph_count'] == len(result.paragraphs)
        assert result.metadata['sentence_count'] == len(result.sentences)
        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_parse_document_empty(self, parser_service):
        """测试空文档解析"""
        with pytest.raises(ValueError):
            await parser_service.parse_document("")

    @pytest.mark.asyncio
    async def test_parse_document_long_text(self, parser_service):
        """测试长文档解析"""
        # 创建一个较长的文档
        text = "这是第一段。" * 100 + "\n\n" + "这是第二段。" * 100

        result = await parser_service.parse_document(text)

        assert len(result.chapters) >= 1
        assert len(result.paragraphs) >= 2
        assert result.processing_time < 10.0  # 应该在10秒内完成

    @pytest.mark.asyncio
    async def test_parse_to_models(self, parser_service):
        """测试解析为模型格式"""
        project_id = "test-project-id"
        text = """
第一章 测试章节

这是第一段。这是第一句。这是第二句。

这是第二段。这是第三句。
        """.strip()

        chapters_data, paragraphs_data, sentences_data = await parser_service.parse_to_models(
            project_id, text
        )

        # 验证章节数据
        assert len(chapters_data) == 1
        assert chapters_data[0]['project_id'] == project_id
        assert chapters_data[0]['title'] == "第一章 测试章节"
        assert chapters_data[0]['chapter_number'] == 1
        assert chapters_data[0]['paragraph_count'] == 2
        assert chapters_data[0]['sentence_count'] == 3

        # 验证段落数据
        assert len(paragraphs_data) == 2
        assert all(p['order_index'] in [1, 2] for p in paragraphs_data)
        assert all(p['action'] == 'keep' for p in paragraphs_data)

        # 验证句子的数据
        assert len(sentences_data) == 3
        assert all(s['order_index'] in [1, 2, 3] for s in sentences_data)
        assert all(s['status'] == 'pending' for s in sentences_data)

    @pytest.mark.asyncio
    async def test_validate_chapter_detection(self, parser_service):
        """测试章节检测验证"""
        text = """
第一章 测试

这是测试内容。

第二章 验证

这是验证内容。
        """.strip()

        result = await parser_service.validate_chapter_detection(text, expected_chapters=2)

        assert result['is_valid'] == True
        assert result['detected_chapters'] == 2
        assert result['expected_chapters'] == 2
        assert len(result['chapter_titles']) == 2
        assert result['average_confidence'] > 0

    @pytest.mark.asyncio
    async def test_validate_chapter_detection_mismatch(self, parser_service):
        """测试章节数量不匹配验证"""
        text = "这是一段没有章节的文本。"

        result = await parser_service.validate_chapter_detection(text, expected_chapters=3)

        assert result['is_valid'] == True  # 仍然有效，但有警告
        assert len(result['warnings']) > 0
        assert "检测章节数" in result['warnings'][0]

    def test_get_detection_stats(self, parser_service):
        """测试获取检测统计"""
        stats = parser_service.get_detection_stats()

        assert 'total_documents_processed' in stats
        assert 'total_chapters_detected' in stats
        assert 'average_chapters_per_document' in stats
        assert isinstance(stats['total_documents_processed'], int)


class TestSentenceSplitterUtils:
    """句子分割工具测试"""

    def test_sentence_info_creation(self):
        """测试句子信息创建"""
        splitter = SentenceSplitter()
        text = "这是一个测试句子。"

        sentence_info = splitter._create_sentence_info(text, 0, len(text))

        assert sentence_info.text == text
        assert sentence_info.start_pos == 0
        assert sentence_info.end_pos == len(text)
        assert sentence_info.word_count > 0
        assert sentence_info.character_count == len(text)
        assert sentence_info.has_chinese == True
        assert sentence_info.sentence_type == SentenceType.STATEMENT
        assert 0 <= sentence_info.confidence_score <= 1

    def test_sentence_type_detection(self):
        """测试句子类型检测"""
        splitter = SentenceSplitter()

        # 测试疑问句
        question_sentence = splitter._detect_sentence_type("这是一个问题吗？")
        assert question_sentence == SentenceType.QUESTION

        # 测试感叹句
        exclamation_sentence = splitter._detect_sentence_type("这是一个感叹句！")
        assert exclamation_sentence == SentenceType.EXCLAMATION

        # 测试陈述句
        statement_sentence = splitter._detect_sentence_type("这是一个陈述句。")
        assert statement_sentence == SentenceType.STATEMENT

    def test_punctuation_detection(self):
        """测试标点符号检测"""
        splitter = SentenceSplitter()
        text = "这是中文句子。This is English sentence!"

        marks = splitter._detect_punctuation_marks(text)

        assert PunctuationMark.PERIOD in marks
        assert PunctuationMark.EN_PERIOD in marks
        assert PunctuationMark.EN_EXCLAMATION in marks


class TestTextAnalyzer:
    """文本分析器测试"""

    def test_analyze_text_basic(self):
        """测试基础文本分析"""
        analyzer = TextAnalyzer()
        text = "这是测试文本。包含中文和English单词123。"

        result = analyzer.analyze_text(text)

        assert result.total_characters == len(text)
        assert result.total_words > 0
        assert result.total_sentences >= 1
        assert result.character_distribution['chinese'] > 0
        assert result.character_distribution['english'] > 0
        assert result.character_distribution['numbers'] > 0
        assert 0 <= result.complexity_score <= 1
        assert 0 <= result.readability_score <= 1

    def test_analyze_empty_text(self):
        """测试空文本分析"""
        analyzer = TextAnalyzer()

        result = analyzer.analyze_text("")

        assert result.total_characters == 0
        assert result.total_words == 0
        assert result.total_sentences == 0
        assert result.total_paragraphs == 0

    def test_language_mix_analysis(self):
        """测试语言混合分析"""
        analyzer = TextAnalyzer()

        # 纯中文
        chinese_text = "这是纯中文文本。"
        chinese_result = analyzer._analyze_language_mix(chinese_text)
        assert chinese_result['chinese'] > 0.9
        assert chinese_result['mixed'] == 0.0

        # 纯英文
        english_text = "This is pure English text."
        english_result = analyzer._analyze_language_mix(english_text)
        assert english_result['english'] > 0.9
        assert english_result['mixed'] == 0.0

        # 混合文本
        mixed_text = "这是中文文本and English text."
        mixed_result = analyzer._analyze_language_mix(mixed_text)
        assert mixed_result['mixed'] > 0.0


if __name__ == "__main__":
    pytest.main([__file__])