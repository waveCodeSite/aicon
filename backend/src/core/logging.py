"""
统一日志系统 - 支持彩色输出和结构化日志
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from loguru import logger as loguru_logger

from src.core.config import settings


# 颜色定义
class LogColors:
    """日志颜色定义"""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # 日志级别颜色
    DEBUG = "\033[36m"  # 青色
    INFO = "\033[32m"  # 绿色
    WARNING = "\033[33m"  # 黄色
    ERROR = "\033[31m"  # 红色
    CRITICAL = "\033[35m"  # 紫色

    # 组件颜色
    TIMESTAMP = "\033[90m"  # 灰色
    LOGGER_NAME = "\033[94m"  # 蓝色
    MODULE = "\033[93m"  # 亮黄色
    FUNCTION = "\033[92m"  # 亮绿色


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器 - 开发环境使用"""

    # 颜色映射
    LEVEL_COLORS = {
        'DEBUG': LogColors.DEBUG,
        'INFO': LogColors.INFO,
        'WARNING': LogColors.WARNING,
        'ERROR': LogColors.ERROR,
        'CRITICAL': LogColors.CRITICAL,
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and self._supports_color()

    def _supports_color(self) -> bool:
        """检测终端是否支持颜色"""
        if not settings.COLORED_LOGS:
            return False

        # 检查是否在TTY中
        if not hasattr(sys.stderr, "isatty") or not sys.stderr.isatty():
            return False

        # 检查环境变量
        if os.getenv("NO_COLOR"):
            return False

        # 检查TERM环境变量
        term = os.getenv("TERM", "")
        if "color" in term or term in ("xterm", "xterm-256color", "screen", "tmux"):
            return True

        # 检查COLORTERM环境变量
        if os.getenv("COLORTERM"):
            return True

        return False

    def _colorize(self, text: str, color: str) -> str:
        """给文本添加颜色"""
        if not self.use_colors:
            return text
        return f"{color}{text}{LogColors.RESET}"

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取颜色
        level_color = self.LEVEL_COLORS.get(record.levelname, "")

        # 时间戳
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        colored_timestamp = self._colorize(timestamp, LogColors.TIMESTAMP)

        # 日志级别
        level_name = f"{record.levelname:8}"
        colored_level = self._colorize(level_name, level_color)

        # 日志器名称
        logger_name = record.name.split('.')[-1]  # 只显示最后一部分
        colored_logger = self._colorize(f"[{logger_name}]", LogColors.LOGGER_NAME)

        # 模块和函数信息
        if hasattr(record, 'funcName') and hasattr(record, 'lineno'):
            location = f"{record.funcName}:{record.lineno}"
            colored_location = self._colorize(location, LogColors.MODULE)
        else:
            colored_location = ""

        # 构建基础消息
        message = record.getMessage()

        # 组合格式
        parts = [
            colored_timestamp,
            colored_level,
            colored_logger,
        ]

        if colored_location:
            parts.append(colored_location)

        parts.append(message)

        formatted = " ".join(parts)

        # 添加异常信息
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器 - 生产环境使用"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id

        return json.dumps(log_entry, ensure_ascii=False)


class StructuredHandler(logging.Handler):
    """结构化日志处理器"""

    def __init__(self, level: int = logging.INFO):
        super().__init__(level)
        self.formatter = StructuredFormatter()

    def emit(self, record: logging.LogRecord) -> None:
        """发出日志记录"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # 添加异常信息
            if record.exc_info:
                log_entry["exception"] = self.formatter.formatException(record.exc_info)

            # 添加额外字段
            if hasattr(record, "user_id"):
                log_entry["user_id"] = record.user_id
            if hasattr(record, "request_id"):
                log_entry["request_id"] = record.request_id
            if hasattr(record, "task_id"):
                log_entry["task_id"] = record.task_id

            print(json.dumps(log_entry, ensure_ascii=False), file=sys.stderr)
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """设置日志系统"""
    # 配置标准库日志
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 根据环境选择格式化器
    if settings.is_development and settings.COLORED_LOGS:
        # 开发环境：彩色控制台输出
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        console_handler.setFormatter(ColoredFormatter(use_colors=True))
        root_logger.addHandler(console_handler)
    else:
        # 生产环境或其他环境：简洁格式
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)

    # 如果启用结构化日志，添加文件处理器
    if settings.STRUCTURED_LOGGING and settings.LOG_FILE:
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)

    # 配置structlog（用于结构化日志记录器）
    if settings.STRUCTURED_LOGGING:
        structlog.configure(
            processors=[
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # 设置第三方库日志级别
    _configure_third_party_loggers()

    # 禁用loguru避免冲突
    loguru_logger.remove()


def _configure_third_party_loggers() -> None:
    """配置第三方库日志级别"""
    # Web框架
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # 数据库
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

    # 任务队列
    logging.getLogger("celery").setLevel(logging.INFO)

    # 缓存和存储
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("minio").setLevel(logging.WARNING)

    # HTTP客户端
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("multipart.multipart").setLevel(logging.WARNING)

    # 其他
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取标准库日志器"""
    return logging.getLogger(name)


def get_structured_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志器"""
    return structlog.get_logger(name)


# 创建应用根日志器
logger = get_logger(__name__)
structured_logger = get_structured_logger(__name__)


class LoggerMixin:
    """日志混入类"""

    @property
    def logger(self) -> logging.Logger:
        """获取当前类的标准库日志器"""
        return get_logger(self.__class__.__name__)

    @property
    def structured_logger(self) -> structlog.stdlib.BoundLogger:
        """获取当前类的结构化日志器"""
        return get_structured_logger(self.__class__.__name__)


def log_with_context(
        level: str,
        message: str,
        **context: Any,
) -> None:
    """带上下文的日志记录"""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra=context)


# 性能日志装饰器
def log_performance(func_name: Optional[str] = None):
    """性能日志装饰器"""

    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Function executed successfully",
                    extra={
                        "function": name,
                        "duration": f"{duration:.3f}s",
                        "success": True
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Function execution failed",
                    extra={
                        "function": name,
                        "duration": f"{duration:.3f}s",
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Function executed successfully",
                    extra={
                        "function": name,
                        "duration": f"{duration:.3f}s",
                        "success": True
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Function execution failed",
                    extra={
                        "function": name,
                        "duration": f"{duration:.3f}s",
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# 请求日志辅助函数
def log_request(
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
) -> None:
    """记录请求日志"""
    logger.info(
        f"HTTP {method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": f"{duration:.3f}s",
            "user_id": user_id,
            "request_id": request_id,
        }
    )


# 错误日志记录
def log_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
) -> None:
    """记录错误日志"""
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "user_id": user_id,
            "request_id": request_id,
        },
        exc_info=True
    )


# 业务日志记录
def log_business_event(
        event_name: str,
        **kwargs: Any,
) -> None:
    """记录业务事件日志"""
    logger.info(
        f"Business event: {event_name}",
        extra={
            "event": event_name,
            **kwargs
        }
    )


# 安全日志记录
def log_security_event(
        event_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs: Any,
) -> None:
    """记录安全事件日志"""
    logger.warning(
        f"Security event: {event_name}",
        extra={
            "security_event": event_name,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            **kwargs
        }
    )


# 任务日志记录
def log_task_event(
        task_id: str,
        event: str,
        status: str,
        **kwargs: Any,
) -> None:
    """记录任务事件日志"""
    logger.info(
        f"Task {task_id}: {event} ({status})",
        extra={
            "task_id": task_id,
            "task_event": event,
            "task_status": status,
            **kwargs
        }
    )


# 初始化日志系统
setup_logging()

__all__ = [
    "get_logger",
    "get_structured_logger",
    "LoggerMixin",
    "log_with_context",
    "log_performance",
    "log_request",
    "log_error",
    "log_business_event",
    "log_security_event",
    "log_task_event",
    "logger",
    "structured_logger",
]
