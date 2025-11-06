# Research Document: AICG内容分发平台技术决策

**Created**: 2025-11-06
**Purpose**: 技术选型决策和2025年最佳实践研究

## Python生态技术决策 (2025年更新)

### 包管理器选择：uv

**决策**: uv作为主要Python包管理器

**理由**:
- uv在2024-2025年成为Python生态的颠覆性工具，安装速度比pip快10-100倍
- 原生Rust实现，内存占用低，依赖解析算法优化
- 完全兼容pip和PyPI生态
- 支持虚拟环境管理，集成度高

**实施方案**:
```toml
# pyproject.toml
[project]
name = "aicg-platform"
version = "0.1.0"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "celery[redis]>=5.3.0",
    "redis[hiredis]>=5.0.0",
    "structlog>=23.2.0",
    "loguru>=0.7.0",
    "pydantic>=2.5.0",
    "httpx>=0.25.0",
    "python-multipart>=0.0.6",
    "ffmpeg-python>=0.2.0",
]
```

### 文本处理技术决策

#### 大文本处理策略 (2025年最佳实践)

**决策**: 流式处理 + 异步I/O + 智能分块

**核心组件选择**:
```python
# 文档解析库 (2025年推荐)
DOCUMENT_PARSERS = {
    'txt': 'chardet + aiofiles',  # 异步文件处理
    'md': 'markdown-it-py + meta-markdown',  # 高性能Markdown解析
    'docx': 'python-docx',  # 稳定可靠
    'epub': 'ebooklib',  # 功能完整
}

# 章节识别算法
import re
from typing import List, Optional
import jieba  # 中文分词，2025年仍是主流
```

**性能优化策略**:
```python
# 1. 异步流式读取
import aiofiles
async def read_large_file_async(file_path: str, chunk_size: int = 8192):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        async for chunk in f.read(chunk_size):
            yield chunk

# 2. 智能缓存策略
from functools import lru_cache
import cachetools  # 2025年流行的缓存库

# 3. 并行处理
import asyncio
from concurrent.futures import ThreadPoolExecutor
```

#### 章节识别算法优化

**决策**: 规则引擎 + 机器学习辅助

```python
class ChapterDetector:
    def __init__(self):
        # 预定义章节模式 (2025年增强版)
        self.patterns = [
            r'第[一二三四五六七八九十百千万零\d]+章[^\n]*\n',
            r'第[一二三四五六七八九十百千万零\d]+节[^\n]*\n',
            r'第[一二三四五六七八九十百千万零\d]+回[^\n]*\n',
            r'Chapter\s+[IVXLCDM\d]+[^\n]*\n',
            r'第\d+章[^\n]*\n',
            r'\d+\.[^\n]*\n',  # 数字编号
        ]

        # 使用spaCy进行语义分析 (2025年推荐)
        self.nlp = spacy.load('zh_core_web_sm')

    async def detect_chapters(self, text: str) -> List[dict]:
        """异步章节识别"""
        # 1. 快速规则匹配
        chapters = self._pattern_matching(text)

        # 2. 语义验证
        validated_chapters = await self._semantic_validation(chapters)

        return validated_chapters
```

### 异步任务架构决策

#### Celery 2025年配置最佳实践

**决策**: Celery 5.3+ + Redis 7.0 + 工人动态扩缩容

```python
# celery_config.py
from celery import Celery
from kombu import Queue

# 2025年推荐配置
app = Celery('aicg_platform')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,

    # 2025年性能优化配置
    worker_prefetch_multiplier=1,  # 防止内存爆炸
    task_acks_late=True,
    worker_disable_rate_limits=False,

    # 队列路由
    task_routes={
        'app.workers.text_processing.*': {'queue': 'text_processing'},
        'app.workers.image_generation.*': {'queue': 'ai_generation'},
        'app.workers.audio_generation.*': {'queue': 'ai_generation'},
        'app.workers.video_synthesis.*': {'queue': 'video_synthesis'},
    },

    # 队列定义
    task_default_queue='default',
    task_queues=(
        Queue('text_processing', routing_key='text_processing'),
        Queue('ai_generation', routing_key='ai_generation'),
        Queue('video_synthesis', routing_key='video_synthesis'),
    ),
)
```

#### 任务分解策略 (句子级细粒度)

**决策**: 最小化任务单元，支持精确的重试和恢复

```python
from celery import group, chain
from app.core.exceptions import RetryableError

@app.task(bind=True, max_retries=3)
def process_sentence_task(self, sentence_id: str, api_config: dict):
    """处理单个句子 - 最小任务单元"""
    try:
        # 生成图片
        image_result = generate_image_for_sentence(sentence_id, api_config)

        # 生成音频片段
        audio_result = generate_audio_for_sentence(sentence_id, api_config)

        # 更新句子状态
        await update_sentence_status(sentence_id, 'completed')

        return {'sentence_id': sentence_id, 'status': 'success'}

    except RetryableError as exc:
        # 可重试错误，自动重试
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task
def process_paragraph_task(paragraph_id: str, api_config: dict):
    """处理段落 - 包含多个句子任务"""
    # 获取段落中的所有句子
    sentences = await get_sentences_by_paragraph(paragraph_id)

    # 创建句子任务组
    sentence_tasks = group(
        process_sentence_task.s(sentence.id, api_config)
        for sentence in sentences
    )

    # 执行并行句子处理
    result = sentence_tasks.apply_async()

    return result.get()
```

### 数据库架构决策

#### SQLAlchemy 2.0 + AsyncPG 2025年优化

**决策**: 全异步数据库访问 + 连接池优化

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# 2025年推荐的异步引擎配置
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/aicg_db",
    echo=True,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    async_native=True,
)

# 异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 异步上下文管理器
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### 数据分片策略

**决策**: 按项目和章节水平分片

```python
# 分片路由器
class DatabaseRouter:
    def __init__(self):
        self.shard_mapping = {}

    def get_shard_engine(self, project_id: int):
        """根据项目ID获取对应的数据库引擎"""
        shard_key = f"shard_{project_id % 4}"  # 4个分片
        if shard_key not in self.shard_mapping:
            self.shard_mapping[shard_key] = create_async_engine(
                f"postgresql+asyncpg://user:password@localhost/{shard_key}"
            )
        return self.shard_mapping[shard_key]

# 模型定义示例
class Sentence(Base):
    __tablename__ = 'sentences'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paragraph_id = Column(String, ForeignKey('paragraphs.id'))
    content = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    start_time = Column(Float, nullable=True)  # 音频开始时间
    end_time = Column(Float, nullable=True)    # 音频结束时间
    status = Column(Enum('pending', 'processing', 'completed', 'failed'), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    paragraph = relationship("Paragraph", back_populates="sentences")
```

### 存储架构决策

#### MinIO 2025年企业级配置

**决策**: MinIO集群 + 分布式存储 + 生命周期管理

```python
# storage_manager.py
from minio import Minio
from minio.error import S3Error
import asyncio
from aiofiles import os

class StorageManager:
    def __init__(self):
        # MinIO客户端配置 (2025年推荐)
        self.client = Minio(
            "minio-server:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )

        # 存储桶配置
        self.buckets = {
            'original-docs': '原始文档 (30天TTL)',
            'generated-images': '生成的图片 (30天TTL)',
            'generated-audio': '生成的音频 (30天TTL)',
            'final-videos': '最终视频 (永久存储)',
            'temp-files': '临时文件 (24小时TTL)'
        }

    async def setup_buckets(self):
        """初始化存储桶和生命周期规则"""
        for bucket_name, description in self.buckets.items():
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                await self._set_lifecycle_policy(bucket_name)

    async def store_with_metadata(self,
                                 bucket: str,
                                 object_name: str,
                                 data: bytes,
                                 metadata: dict = None):
        """存储文件并附加元数据"""
        try:
            from io import BytesIO
            self.client.put_object(
                bucket,
                object_name,
                BytesIO(data),
                len(data),
                metadata=metadata or {}
            )
            return f"{bucket}/{object_name}"
        except S3Error as e:
            raise StorageError(f"MinIO存储失败: {e}")
```

### 日志和监控决策 (2025年标准)

#### 结构化日志 + OpenTelemetry

**决策**: structlog + OpenTelemetry + Prometheus

```python
# logging_config.py
import structlog
import logging
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

# OpenTelemetry配置
def setup_telemetry():
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(JaegerExporter(agent_host_name="jaeger"))
    )

    reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))

# 结构化日志配置
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 带追踪的日志记录器
logger = structlog.get_logger()
```

### 异常处理和错误恢复

#### 分层异常处理 + Circuit Breaker

```python
# exceptions.py
from typing import Optional
from circuit_breaker import CircuitBreaker
import backoff

class AICGException(Exception):
    """基础异常类"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class RetryableError(AICGException):
    """可重试错误"""
    pass

class NonRetryableError(AICGException):
    """不可重试错误"""
    pass

# Circuit Breaker配置
ai_service_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=RetryableError
)

# 带退避策略的重试装饰器
@backoff.on_exception(
    backoff.expo,
    RetryableError,
    max_tries=3,
    base=1,
    max_value=60
)
@ai_service_breaker
async def call_ai_service(api_call_func, *args, **kwargs):
    """AI服务调用 - 带熔断和退避"""
    return await api_call_func(*args, **kwargs)
```

## 技术决策总结 (2025年标准)

| 技术领域 | 选择方案 | 2025年优势 |
|---------|---------|-----------|
| **包管理** | uv | 10-100倍速度提升，现代化依赖管理 |
| **Web框架** | FastAPI 0.104+ | 原生异步支持，OpenAPI自动生成 |
| **数据库** | SQLAlchemy 2.0 + AsyncPG | 全异步ORM，性能优异 |
| **任务队列** | Celery 5.3+ + Redis 7.0 | 成熟稳定，支持动态扩缩容 |
| **存储** | MinIO集群 | 开源，S3兼容，高性能 |
| **前端** | Vue.js 3 + Vite | 现代化，开发体验优秀 |
| **日志** | structlog + OpenTelemetry | 结构化，分布式追踪 |
| **监控** | Prometheus + Grafana | 云原生标准，生态丰富 |
| **缓存** | Redis + cachetools | 多级缓存，性能优化 |

这些技术选择都基于2025年的最新发展，确保系统的现代化、高性能和可维护性。