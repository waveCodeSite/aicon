"""
文本处理工具函数 - 统一的文本处理模块
提供段落分割、句子分割、文本分析等功能，避免重复实现
严格按照data-model.md规范实现，为章节识别和解析提供支持
"""

import re
from dataclasses import dataclass
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter

try:
    from src.core.logging import get_logger
except ImportError:
    # 用于独立测试的情况
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


@dataclass
class SentenceInfo:
    """句子信息"""
    text: str
    start_pos: int
    end_pos: int
    length: int
    word_count: int
    character_count: int


class ParagraphSplitter:
    """段落分割器 - 委托给file_handlers.py以避免重复代码"""

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)

    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        将文本分割为段落 - 委托给FileHandler
        保持接口兼容性，避免重复实现
        """
        if not text:
            return []

        return self.splitter.split_text(text)


class LongSentenceSplitter(TextSplitter):
    """
    LangChain 兼容的长句切分器。

    功能：
        1. 按中英文标点符号进行基础分句
        2. 自动合并短句，生成较长句子
        3. 控制每句长度在 target_min_chars ~ target_max_chars 之间
        4. 支持 strict_mode，严格保证每句最小长度

    Attributes:
        target_min_chars (int): 每句最小字符数
        target_max_chars (int): 每句最大字符数
        strict_mode (bool): 是否严格保证句子长度 >= target_min_chars
    """

    def __init__(
            self,
            target_min_chars: int = 100,
            target_max_chars: int = 300,
            strict_mode: bool = True,
    ):
        """
        初始化 LongSentenceSplitter。

        Args:
            target_min_chars (int): 每句最小字符数，默认 80
            target_max_chars (int): 每句最大字符数，默认 200
            strict_mode (bool): 是否严格保证最小长度，默认 False
        """
        super().__init__()
        self.target_min_chars = target_min_chars
        self.target_max_chars = target_max_chars
        self.strict_mode = strict_mode

        # 定义中英文分句正则
        self._split_pattern = re.compile(
            r"(?<=[。！？!?])\s*|(?<=[\.\?\!])\s+"
        )

    def base_split(self, text: str) -> List[str]:
        """
        将文本按中英文标点进行基础分句。

        Args:
            text (str): 待切分文本

        Returns:
            List[str]: 基础句子列表，可能包含较短句子
        """
        parts = re.split(self._split_pattern, text)
        return [p.strip() for p in parts if p.strip()]

    def merge_sentences(self, sentences: List[str]) -> List[str]:
        """
        将基础句子合并成更长的句子，保证长度在 target_min_chars ~ target_max_chars 之间。

        Args:
            sentences (List[str]): 基础句子列表

        Returns:
            List[str]: 合并后的长句列表
        """
        merged = []
        current = ""

        for s in sentences:
            new_len = len(current) + len(s)

            if new_len < self.target_min_chars:
                # 句子太短，继续合并
                current += s
                continue

            if new_len > self.target_max_chars:
                # 句子太长，先保存已有句子，重新开始新句
                if current:
                    merged.append(current)
                current = s
                continue

            # 句子长度在合理范围内，直接加入
            current += s
            merged.append(current)
            current = ""

        # 循环结束后，若还有剩余句子，加入结果
        if current:
            merged.append(current)

        if not self.strict_mode:
            return merged

        # strict_mode=True：保证所有句子长度 >= target_min_chars
        final = []
        temp = ""
        for m in merged:
            if len(m) < self.target_min_chars:
                temp += m
            else:
                if temp:
                    final.append(temp)
                    temp = ""
                final.append(m)
        if temp:
            final.append(temp)

        print(final)
        exit()
        return final

    def split_text(self, text: str) -> List[str]:
        """
        LangChain 主接口：将文本切分为长句列表。

        Args:
            text (str): 待切分文本

        Returns:
            List[str]: 切分后的长句列表，可直接用于 LangChain Document chunks
        """
        sentences = self.base_split(text)
        return self.merge_sentences(sentences)


class SentenceSplitter:
    """句子分割器 - 专注于基础的句子分割功能"""

    def __init__(self):
        # 中文句子结束标记
        self.chinese_endings = r'[。！？…]'

        # 英文句子结束标记
        self.english_endings = r'[.!?]'

        # 编译正则表达式
        self.sentence_end_pattern = re.compile(
            rf'({self.chinese_endings}|{self.english_endings})+'
        )

        # 数字.数字模式（避免误判）
        self.decimal_pattern = re.compile(r'\d+\.\d+')

        # 缩写模式（英文）
        self.abbreviation_pattern = re.compile(
            r'\b(?:Mr|Mrs|Dr|Prof|St|etc|vs|e\.g|i\.e)\.$',
            re.IGNORECASE
        )

    def split_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        if not text:
            return []

        # 预处理文本
        processed_text = self._preprocess_text(text)

        # 基础句子分割
        sentences = self._basic_split(processed_text)

        # 后处理
        sentences = self._post_process_sentences(sentences)

        return sentences

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)

        # 处理缩写
        text = self.abbreviation_pattern.sub(
            lambda m: m.group().replace('.', '<ABBREV_DOT>'),
            text
        )

        # 处理数字中的点
        text = self.decimal_pattern.sub(
            lambda m: m.group().replace('.', '<DECIMAL_DOT>'),
            text
        )

        return text

    def _basic_split(self, text: str) -> List[str]:
        """基础句子分割"""
        sentences = []

        # 使用正则表达式分割
        parts = self.sentence_end_pattern.split(text)

        # 重建句子
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                sentence = parts[i] + parts[i + 1]
            else:
                sentence = parts[i]

            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def _post_process_sentences(self, sentences: List[str]) -> List[str]:
        """后处理句子列表"""
        processed = []

        for sentence in sentences:
            # 恢复被替换的字符
            sentence = sentence.replace('<ABBREV_DOT>', '.')
            sentence = sentence.replace('<DECIMAL_DOT>', '.')

            # 移除多余的空白
            sentence = re.sub(r'\s+', ' ', sentence).strip()

            if len(sentence) >= 5:  # 过滤过短的句子
                processed.append(sentence)

        return processed


# 全局实例
paragraph_splitter = ParagraphSplitter()
sentence_splitter = SentenceSplitter()
long_sentence_splitter = LongSentenceSplitter()

__all__ = [
    'ParagraphSplitter',
    'SentenceSplitter',
    'SentenceInfo',
    'paragraph_splitter',
    'sentence_splitter'
]
