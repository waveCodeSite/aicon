"""
FastAPI中间件
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.logging import logger
from src.core.exceptions import AICGException


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """错误处理中间件"""
    try:
        response = await call_next(request)
        return response
    except AICGException as exc:
        # 处理自定义异常
        logger.error(
            "AICG应用异常",
            exception_type=type(exc).__name__,
            message=exc.message,
            error_code=exc.error_code,
            status_code=exc.status_code,
            details=exc.details,
            path=request.url.path,
            method=request.method,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": time.time(),
            },
        )
    except Exception as exc:
        # 处理未知异常
        logger.error(
            "未处理的异常",
            exception_type=type(exc).__name__,
            message=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "内部服务器错误" if not settings.DEBUG else str(exc),
                "timestamp": time.time(),
            },
        )


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """日志记录中间件"""
    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    # 记录请求开始
    logger.info(
        "HTTP请求开始",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(
            "HTTP请求完成",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=f"{process_time:.3f}s",
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

    except Exception as exc:
        process_time = time.time() - start_time

        # 记录请求异常
        logger.error(
            "HTTP请求异常",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            duration=f"{process_time:.3f}s",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )

        # 添加响应头（即使异常也要添加）
        if hasattr(exc, 'response') and hasattr(exc.response, 'headers'):
            exc.response.headers["X-Request-ID"] = request_id
            exc.response.headers["X-Process-Time"] = f"{process_time:.3f}"

        raise


async def security_middleware(request: Request, call_next: Callable) -> Response:
    """安全中间件"""
    # 安全头
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
    }

    # 检查请求方法
    if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        logger.warning(
            "不允许的HTTP方法",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        return JSONResponse(
            status_code=405,
            content={
                "error": True,
                "code": "METHOD_NOT_ALLOWED",
                "message": "不允许的HTTP方法",
                "timestamp": time.time(),
            },
        )

    # 检查内容长度
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_FILE_SIZE:
        logger.warning(
            "请求内容过大",
            content_length=content_length,
            max_size=settings.MAX_FILE_SIZE,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=413,
            content={
                "error": True,
                "code": "PAYLOAD_TOO_LARGE",
                "message": "请求内容过大",
                "timestamp": time.time(),
            },
        )

    # 继续处理请求
    response = await call_next(request)

    # 添加安全头
    for header, value in security_headers.items():
        response.headers[header] = value

    return response


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """限流中间件"""
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)

    # 获取客户端IP
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else "unknown")
    )

    # 使用内存存储（生产环境应使用Redis）
    from src.core.security import check_api_rate_limit

    try:
        result = check_api_rate_limit(client_ip)

        if not result["allowed"]:
            logger.warning(
                "API限流触发",
                client_ip=client_ip,
                path=request.url.path,
                retry_after=result["retry_after"],
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": result["retry_after"],
                    "timestamp": time.time(),
                },
                headers={
                    "Retry-After": str(result["retry_after"]),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": str(result["remaining"]),
                    "X-RateLimit-Reset": str(int(result["reset_time"])),
                },
            )

        response = await call_next(request)

        # 添加限流响应头
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(result["reset_time"]))

        return response

    except Exception as exc:
        logger.error(
            "限流中间件异常",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            client_ip=client_ip,
        )
        # 限流中间件异常时，允许请求通过
        return await call_next(request)


async def cors_middleware(request: Request, call_next: Callable) -> Response:
    """CORS中间件（额外处理）"""
    response = await call_next(request)

    # 确保CORS头存在
    origin = request.headers.get("origin")
    if origin and (origin in settings.CORS_ORIGINS or "*" in settings.CORS_ORIGINS):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response