"""
API v1 模块
"""

from fastapi import APIRouter

# 创建主路由器
api_router = APIRouter()

@api_router.get("/")
async def api_v1_info():
    """API v1 信息"""
    return {
        "name": "AICG内容分发平台 API v1",
        "version": "1.0.0",
        "status": "under_development",
        "message": "API v1 正在开发中",
    }

# 暂时禁用其他路由，避免导入错误
# TODO: 在完成相应模块后启用这些路由
# from .auth import router as auth_router
# api_router.include_router(auth_router, prefix="/auth", tags=["认证"])

__all__ = ["api_router"]