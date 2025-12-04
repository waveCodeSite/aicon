"""
BGM管理API
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.api.schemas.bgm import (
    BGMDeleteResponse,
    BGMListResponse,
    BGMResponse,
    BGMStatsResponse,
    BGMUploadResponse,
)
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.services.bgm_service import BGMService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/upload", response_model=BGMUploadResponse)
async def upload_bgm(
    *,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(..., description="BGM文件"),
    name: str = Form(..., description="BGM名称")
):
    """上传BGM文件"""
    bgm_service = BGMService(db)
    
    try:
        bgm = await bgm_service.upload_bgm(
            user_id=str(current_user.id),
            file=file,
            name=name
        )
        
        response_data = bgm.to_dict()
        return BGMUploadResponse.from_dict(response_data)
        
    except Exception as e:
        logger.error(f"BGM上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=BGMListResponse)
async def get_bgms(
    *,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序顺序")
):
    """获取用户的BGM列表"""
    bgm_service = BGMService(db)
    
    bgms, total = await bgm_service.list_user_bgms(
        user_id=str(current_user.id),
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # 转换为响应模型
    bgm_responses = [BGMResponse.from_dict(bgm.to_dict()) for bgm in bgms]
    total_pages = (total + size - 1) // size
    
    return BGMListResponse(
        bgms=bgm_responses,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get("/stats", response_model=BGMStatsResponse)
async def get_bgm_stats(
    *,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的BGM统计信息"""
    bgm_service = BGMService(db)
    stats = await bgm_service.get_bgm_stats(str(current_user.id))
    return BGMStatsResponse(**stats)


@router.get("/{bgm_id}", response_model=BGMResponse)
async def get_bgm(
    *,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    bgm_id: str
):
    """获取BGM详情"""
    bgm_service = BGMService(db)
    bgm = await bgm_service.get_bgm_by_id(bgm_id, str(current_user.id))
    
    response_data = bgm.to_dict()
    return BGMResponse.from_dict(response_data)


@router.delete("/{bgm_id}", response_model=BGMDeleteResponse)
async def delete_bgm(
    *,
    current_user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    bgm_id: str
):
    """删除BGM"""
    bgm_service = BGMService(db)
    await bgm_service.delete_bgm(bgm_id, str(current_user.id))
    
    return BGMDeleteResponse(
        success=True,
        message="删除成功",
        bgm_id=bgm_id
    )


__all__ = ["router"]
