"""
日志中间件 - 记录HTTP请求和响应日志
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response

from src.core.logging import logger


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """日志记录中间件"""
    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    # 记录请求开始
    logger.info(f"HTTP请求开始 - {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(f"HTTP请求完成 - {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

    except Exception as exc:
        process_time = time.time() - start_time

        # 记录请求异常
        logger.error(f"HTTP请求异常 - {request.method} {request.url.path} - {type(exc).__name__}: {str(exc)} - {process_time:.3f}s")

        raise


async def request_details_middleware(request: Request, call_next: Callable) -> Response:
    """请求详情中间件 - 记录更详细的请求信息"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    start_time = time.time()

    # 记录详细的请求信息（仅在DEBUG模式）
    if logger.isEnabledFor(10):  # DEBUG level
        logger.debug(
            "HTTP请求详情",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
        )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录详细的响应信息（仅在DEBUG模式）
        if logger.isEnabledFor(10):
            logger.debug(
                "HTTP响应详情",
                request_id=request_id,
                status_code=response.status_code,
                headers=dict(response.headers),
                duration=f"{process_time:.3f}s",
            )

        return response

    except Exception as exc:
        process_time = time.time() - start_time

        logger.debug(
            "HTTP请求异常详情",
            request_id=request_id,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            duration=f"{process_time:.3f}s",
        )

        raise


async def performance_monitoring_middleware(request: Request, call_next: Callable) -> Response:
    """性能监控中间件 - 监控慢请求"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 监控慢请求（超过2秒）
        if process_time > 2.0:
            logger.warning(f"慢请求警告 - {request.method} {request.url.path} - {process_time:.3f}s")

        # 监控非常慢请求（超过5秒）
        if process_time > 5.0:
            logger.error(f"非常慢请求 - {request.method} {request.url.path} - {process_time:.3f}s")

        return response

    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(f"请求处理异常 - {request.method} {request.url.path} - {type(exc).__name__}: {str(exc)} - {process_time:.3f}s")
        raise


__all__ = [
    "logging_middleware",
    "request_details_middleware",
    "performance_monitoring_middleware",
]