"""
文本处理工具函数 - 包含句子分割算法和文本分析工具
严格按照data-model.md规范实现，为章节识别和解析提供支持
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from src.core.logging import get_logger
except ImportError:
    # 用于独立测试的情况
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class SentenceType(Enum):
    """句子类型枚举"""
    STATEMENT = "statement"      # 陈述句
    QUESTION = "question"        # 疑问句
    EXCLAMATION = "exclamation"  # 感叹句
    IMPERATIVE = "imperative"    # 祈使句
    UNKNOWN = "unknown"          # 未知类型


class PunctuationMark(Enum):
    """标点符号枚举"""
    PERIOD = "。"      # 中文句号
    QUESTION = "？"    # 中文问号
    EXCLAMATION = "！"  # 中文感叹号
    ELLIPSIS = "…"     # 省略号
    EN_PERIOD = "."    # 英文句号
    EN_QUESTION = "?"  # 英文问号
    EN_EXCLAMATION = "!"  # 英文感叹号


@dataclass
class SentenceInfo:
    """句子信息"""
    text: str
    start_pos: int
    end_pos: int
    length: int
    word_count: int
    character_count: int
    sentence_type: SentenceType
    punctuation_marks: List[PunctuationMark]
    has_chinese: bool
    has_english: bool
    has_numbers: bool
    confidence_score: float = 1.0


@dataclass
class TextAnalysis:
    """文本分析结果"""
    total_characters: int
    total_words: int
    total_sentences: int
    total_paragraphs: int
    character_distribution: Dict[str, int]
    sentence_types: Dict[SentenceType, int]
    punctuation_usage: Dict[PunctuationMark, int]
    language_mix: Dict[str, float]
    complexity_score: float
    readability_score: float


class SentenceSplitter:
    """句子分割器"""

    def __init__(self):
        # 中文句子结束标记
        self.chinese_endings = r'[。！？…]'

        # 英文句子结束标记
        self.english_endings = r'[.!?]'

        # 引号和括号
        self.quotes = r'["""''《》【】()（）\[\]{}]'

        # 数字和字母
        self.chinese_chars = r'[\u4e00-\u9fff]'
        self.english_chars = r'[a-zA-Z]'
        self.digits = r'\d'

        # 编译正则表达式
        self._compile_patterns()

    def _compile_patterns(self):
        """编译常用的正则表达式模式"""
        # 完整的句子结束模式
        self.sentence_end_pattern = re.compile(
            rf'({self.chinese_endings}|{self.english_endings})+'
        )

        # 引号内的句子结束
        self.quoted_sentence_pattern = re.compile(
            rf'{self.quotes}([^"]*?(?:{self.chinese_endings}|{self.english_endings})+[^"]*?){self.quotes}'
        )

        # 连续的标点符号
        self.consecutive_punctuation = re.compile(r'[。！？.!?]{2,}')

        # 数字.数字模式（避免误判）
        self.decimal_pattern = re.compile(r'\d+\.\d+')

        # 缩写模式（英文）
        self.abbreviation_pattern = re.compile(
            r'\b(?:Mr|Mrs|Dr|Prof|St|etc|vs|e\.g|i\.e)\.$',
            re.IGNORECASE
        )

    def split_sentences(self, text: str, options: Optional[Dict[str, any]] = None) -> List[SentenceInfo]:
        """
        分割文本为句子

        Args:
            text: 待分割文本
            options: 分割选项
                - min_sentence_length: 最小句子长度（默认5）
                - preserve_quotes: 保留引号（默认True）
                - handle_abbreviations: 处理缩写（默认True）
                - merge_short_sentences: 合并短句（默认False）

        Returns:
            List[SentenceInfo]: 句子信息列表
        """
        if not text or not text.strip():
            return []

        options = options or {}
        min_length = options.get('min_sentence_length', 5)
        preserve_quotes = options.get('preserve_quotes', True)
        handle_abbreviations = options.get('handle_abbreviations', True)
        merge_short = options.get('merge_short_sentences', False)

        try:
            # 预处理文本
            processed_text = self._preprocess_text(text, handle_abbreviations)

            # 基础句子分割
            sentences = self._basic_split(processed_text)

            # 后处理
            sentences = self._post_process_sentences(
                sentences,
                min_length,
                preserve_quotes,
                merge_short
            )

            # 生成句子信息
            sentence_infos = []
            current_pos = 0

            for sentence in sentences:
                # 找到句子在原文中的位置
                start_pos = text.find(sentence, current_pos)
                if start_pos == -1:
                    # 如果找不到，使用当前位置
                    start_pos = current_pos

                end_pos = start_pos + len(sentence)

                sentence_info = self._create_sentence_info(
                    sentence,
                    start_pos,
                    end_pos
                )

                if sentence_info:
                    sentence_infos.append(sentence_info)
                    current_pos = end_pos

            logger.debug(f"文本分割完成: {len(sentence_infos)} 个句子")
            return sentence_infos

        except Exception as e:
            logger.error(f"句子分割失败: {str(e)}")
            # 返回整个文本作为单个句子
            return [self._create_sentence_info(text, 0, len(text))]

    def _preprocess_text(self, text: str, handle_abbreviations: bool) -> str:
        """预处理文本"""
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)

        # 处理缩写
        if handle_abbreviations:
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

    def _post_process_sentences(
        self,
        sentences: List[str],
        min_length: int,
        preserve_quotes: bool,
        merge_short: bool
    ) -> List[str]:
        """后处理句子列表"""
        processed = []

        for sentence in sentences:
            # 恢复被替换的字符
            sentence = sentence.replace('<ABBREV_DOT>', '.')
            sentence = sentence.replace('<DECIMAL_DOT>', '.')

            # 移除多余的空白
            sentence = re.sub(r'\s+', ' ', sentence).strip()

            if len(sentence) >= min_length:
                processed.append(sentence)
            elif merge_short and processed:
                # 合并到前一个句子
                processed[-1] += ' ' + sentence
            elif len(sentence) > 0:
                # 短句也要保留，但标记低置信度
                processed.append(sentence)

        return processed

    def _create_sentence_info(self, text: str, start_pos: int, end_pos: int) -> Optional[SentenceInfo]:
        """创建句子信息对象"""
        if not text.strip():
            return None

        # 基础统计
        length = len(text)
        word_count = self._count_words(text)
        character_count = length

        # 检测句子类型
        sentence_type = self._detect_sentence_type(text)

        # 检测标点符号
        punctuation_marks = self._detect_punctuation_marks(text)

        # 语言检测
        has_chinese = bool(re.search(self.chinese_chars, text))
        has_english = bool(re.search(self.english_chars, text))
        has_numbers = bool(re.search(self.digits, text))

        # 计算置信度
        confidence_score = self._calculate_confidence_score(
            text, sentence_type, punctuation_marks
        )

        return SentenceInfo(
            text=text,
            start_pos=start_pos,
            end_pos=end_pos,
            length=length,
            word_count=word_count,
            character_count=character_count,
            sentence_type=sentence_type,
            punctuation_marks=punctuation_marks,
            has_chinese=has_chinese,
            has_english=has_english,
            has_numbers=has_numbers,
            confidence_score=confidence_score
        )

    def _count_words(self, text: str) -> int:
        """计算词数"""
        # 中文按字符计数
        chinese_words = len(re.findall(self.chinese_chars, text))

        # 英文按单词计数
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))

        # 数字按单独计数
        numbers = len(re.findall(r'\b\d+\b', text))

        return chinese_words + english_words + numbers

    def _detect_sentence_type(self, text: str) -> SentenceType:
        """检测句子类型"""
        if not text:
            return SentenceType.UNKNOWN

        # 检查最后一个标点符号
        for char in reversed(text):
            if char == '？' or char == '?':
                return SentenceType.QUESTION
            elif char == '！' or char == '!':
                return SentenceType.EXCLAMATION
            elif char == '。' or char == '.':
                # 检查是否是疑问句模式
                if any(word in text for word in ['吗', '呢', '吧', '什么', '谁', '哪里', 'why', 'what', 'who', 'where']):
                    return SentenceType.QUESTION
                # 检查是否是祈使句模式
                elif any(word in text for word in ['请', '让', '要', '必须', '应该', 'please', 'let', 'must', 'should']):
                    return SentenceType.IMPERATIVE
                else:
                    return SentenceType.STATEMENT

        return SentenceType.UNKNOWN

    def _detect_punctuation_marks(self, text: str) -> List[PunctuationMark]:
        """检测标点符号"""
        marks = []

        punctuation_map = {
            '。': PunctuationMark.PERIOD,
            '？': PunctuationMark.QUESTION,
            '！': PunctuationMark.EXCLAMATION,
            '…': PunctuationMark.ELLIPSIS,
            '.': PunctuationMark.EN_PERIOD,
            '?': PunctuationMark.EN_QUESTION,
            '!': PunctuationMark.EN_EXCLAMATION
        }

        for char in text:
            if char in punctuation_map:
                marks.append(punctuation_map[char])

        return marks

    def _calculate_confidence_score(
        self,
        text: str,
        sentence_type: SentenceType,
        punctuation_marks: List[PunctuationMark]
    ) -> float:
        """计算句子分割置信度"""
        score = 1.0

        # 根据句子类型调整
        if sentence_type == SentenceType.UNKNOWN:
            score -= 0.3

        # 根据标点符号调整
        if not punctuation_marks:
            score -= 0.4
        elif len(punctuation_marks) > 3:
            score -= 0.2  # 标点过多可能表示分割错误

        # 根据长度调整
        if len(text) < 5:
            score -= 0.3
        elif len(text) > 500:
            score -= 0.1

        # 根据内容质量调整
        if re.search(r'[^\w\s\u4e00-\u9fff，。！？、；：""''（）【】]', text):
            score -= 0.1  # 包含特殊字符

        return max(0.0, min(1.0, score))


class TextAnalyzer:
    """文本分析器"""

    def __init__(self):
        self.sentence_splitter = SentenceSplitter()

    def analyze_text(self, text: str) -> TextAnalysis:
        """全面分析文本"""
        try:
            # 基础统计
            total_characters = len(text)
            total_words = self._count_total_words(text)

            # 分段和分句
            paragraphs = self._split_paragraphs(text)
            sentences = self.sentence_splitter.split_sentences(text)

            total_paragraphs = len(paragraphs)
            total_sentences = len(sentences)

            # 字符分布
            character_distribution = self._analyze_character_distribution(text)

            # 句子类型分布
            sentence_types = self._analyze_sentence_types(sentences)

            # 标点符号使用
            punctuation_usage = self._analyze_punctuation_usage(text)

            # 语言混合
            language_mix = self._analyze_language_mix(text)

            # 复杂度和可读性
            complexity_score = self._calculate_complexity_score(
                text, sentences, paragraphs
            )
            readability_score = self._calculate_readability_score(
                text, sentences, paragraphs
            )

            return TextAnalysis(
                total_characters=total_characters,
                total_words=total_words,
                total_sentences=total_sentences,
                total_paragraphs=total_paragraphs,
                character_distribution=character_distribution,
                sentence_types=sentence_types,
                punctuation_usage=punctuation_usage,
                language_mix=language_mix,
                complexity_score=complexity_score,
                readability_score=readability_score
            )

        except Exception as e:
            logger.error(f"文本分析失败: {str(e)}")
            # 返回默认值
            return TextAnalysis(
                total_characters=len(text),
                total_words=0,
                total_sentences=0,
                total_paragraphs=0,
                character_distribution={},
                sentence_types={},
                punctuation_usage={},
                language_mix={},
                complexity_score=0.0,
                readability_score=0.0
            )

    def _count_total_words(self, text: str) -> int:
        """计算总词数"""
        splitter = SentenceSplitter()
        return splitter._count_words(text)

    def _split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    def _analyze_character_distribution(self, text: str) -> Dict[str, int]:
        """分析字符分布"""
        distribution = {
            'chinese': len(re.findall(r'[\u4e00-\u9fff]', text)),
            'english': len(re.findall(r'[a-zA-Z]', text)),
            'numbers': len(re.findall(r'\d', text)),
            'punctuation': len(re.findall(r'[，。！？、；：""''（）【】\.,!?;:()"\'\[\]{}]', text)),
            'spaces': len(re.findall(r'\s', text)),
            'others': 0
        }

        # 计算其他字符
        total = sum(distribution.values())
        distribution['others'] = len(text) - total

        return distribution

    def _analyze_sentence_types(self, sentences: List[SentenceInfo]) -> Dict[SentenceType, int]:
        """分析句子类型分布"""
        types_count = {}
        for sentence in sentences:
            types_count[sentence.sentence_type] = types_count.get(sentence.sentence_type, 0) + 1
        return types_count

    def _analyze_punctuation_usage(self, text: str) -> Dict[PunctuationMark, int]:
        """分析标点符号使用"""
        usage = {}
        punctuation_map = {
            '。': PunctuationMark.PERIOD,
            '？': PunctuationMark.QUESTION,
            '！': PunctuationMark.EXCLAMATION,
            '…': PunctuationMark.ELLIPSIS,
            '.': PunctuationMark.EN_PERIOD,
            '?': PunctuationMark.EN_QUESTION,
            '!': PunctuationMark.EN_EXCLAMATION
        }

        for char, mark in punctuation_map.items():
            count = text.count(char)
            if count > 0:
                usage[mark] = count

        return usage

    def _analyze_language_mix(self, text: str) -> Dict[str, float]:
        """分析语言混合情况"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_meaningful = chinese_chars + english_chars

        if total_meaningful == 0:
            return {'chinese': 0.0, 'english': 0.0, 'mixed': 1.0}

        chinese_ratio = chinese_chars / total_meaningful
        english_ratio = english_chars / total_meaningful

        # 判断是否为混合文本
        if chinese_ratio > 0.1 and english_ratio > 0.1:
            return {'chinese': chinese_ratio, 'english': english_ratio, 'mixed': 1.0}
        elif chinese_ratio > 0.9:
            return {'chinese': 1.0, 'english': 0.0, 'mixed': 0.0}
        elif english_ratio > 0.9:
            return {'chinese': 0.0, 'english': 1.0, 'mixed': 0.0}
        else:
            return {'chinese': chinese_ratio, 'english': english_ratio, 'mixed': 0.5}

    def _calculate_complexity_score(self, text: str, sentences: List[SentenceInfo], paragraphs: List[str]) -> float:
        """计算文本复杂度分数 (0-1)"""
        if not text:
            return 0.0

        factors = []

        # 句子长度变化
        if sentences:
            sentence_lengths = [s.length for s in sentences]
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            length_variance = sum((l - avg_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
            factors.append(min(1.0, length_variance / 1000))  # 归一化

        # 段落数量
        paragraph_factor = min(1.0, len(paragraphs) / 20)  # 20段以上认为是复杂的
        factors.append(paragraph_factor)

        # 标点符号多样性
        unique_punctuation = len(set(re.findall(r'[，。！？、；：""''（）【】\.,!?;:()"\'\[\]{}]', text)))
        punctuation_factor = min(1.0, unique_punctuation / 10)
        factors.append(punctuation_factor)

        # 语言混合
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        has_english = bool(re.search(r'[a-zA-Z]', text))
        if has_chinese and has_english:
            factors.append(0.3)  # 语言混合增加复杂度

        return min(1.0, sum(factors) / len(factors))

    def _calculate_readability_score(self, text: str, sentences: List[SentenceInfo], paragraphs: List[str]) -> float:
        """计算可读性分数 (0-1, 1表示最易读)"""
        if not text or not sentences:
            return 0.0

        # 基础分数
        base_score = 0.7

        # 句子长度适中性
        avg_sentence_length = sum(s.length for s in sentences) / len(sentences)
        if 10 <= avg_sentence_length <= 50:
            length_score = 0.2
        elif 5 <= avg_sentence_length <= 100:
            length_score = 0.1
        else:
            length_score = -0.1

        # 段落长度适中性
        if paragraphs:
            avg_paragraph_length = sum(len(p) for p in paragraphs) / len(paragraphs)
            if 50 <= avg_paragraph_length <= 300:
                paragraph_score = 0.1
            else:
                paragraph_score = -0.05
        else:
            paragraph_score = 0.0

        # 标点符号使用合理性
        punctuation_ratio = len(re.findall(r'[，。！？、；：""''（）【】\.,!?;:()"\'\[\]{}]', text)) / len(text)
        if 0.05 <= punctuation_ratio <= 0.15:
            punctuation_score = 0.1
        else:
            punctuation_score = -0.05

        total_score = base_score + length_score + paragraph_score + punctuation_score
        return max(0.0, min(1.0, total_score))


# 全局实例
sentence_splitter = SentenceSplitter()
text_analyzer = TextAnalyzer()

__all__ = [
    'SentenceSplitter',
    'TextAnalyzer',
    'SentenceInfo',
    'TextAnalysis',
    'SentenceType',
    'PunctuationMark',
    'sentence_splitter',
    'text_analyzer'
]