"""
管理员API端点
处理用户管理、系统管理等管理员功能
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user_required
from src.core.database import get_db
from src.models.user import User
from src.models.system_setting import SystemSetting
from src.api.schemas.base import MessageResponse

from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# Schemas
# ============================================

class AdminUserResponse(BaseModel):
    """管理员查看的用户信息"""
    id: UUID
    username: str
    email: str
    display_name: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[AdminUserResponse]
    total: int
    page: int
    page_size: int


class UserUpdateByAdminRequest(BaseModel):
    """管理员更新用户请求"""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None


class CreateUserRequest(BaseModel):
    """管理员创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = Field(None, max_length=100)
    is_admin: bool = False


class SystemSettingsResponse(BaseModel):
    """系统设置响应"""
    allow_registration: bool = True


class SystemSettingsUpdateRequest(BaseModel):
    """系统设置更新请求"""
    allow_registration: Optional[bool] = None


# ============================================
# Dependencies
# ============================================

async def get_admin_user(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """验证当前用户是否为管理员"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# ============================================
# Routes
# ============================================

router = APIRouter()


@router.get("/users", response_model=UserListResponse, summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="筛选激活状态"),
    is_admin: Optional[bool] = Query(None, description="筛选管理员"),
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（管理员）

    - **认证**: 需要管理员权限
    - **分页**: 支持分页查询
    - **筛选**: 支持按状态、角色筛选
    """
    query = select(User)
    count_query = select(func.count(User.id))

    # 搜索条件
    if search:
        search_filter = User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # 筛选条件
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    if is_admin is not None:
        query = query.where(User.is_admin == is_admin)
        count_query = count_query.where(User.is_admin == is_admin)

    # 总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[AdminUserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse, summary="获取用户详情")
async def get_user(
    user_id: UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定用户详情（管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return AdminUserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=AdminUserResponse, summary="更新用户")
async def update_user(
    user_id: UUID,
    update_data: UserUpdateByAdminRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息（管理员）

    - **认证**: 需要管理员权限
    - **可更新**: is_active, is_verified, is_admin
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 防止管理员取消自己的管理员权限
    if user.id == admin_user.id and update_data.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能取消自己的管理员权限"
        )

    # 更新字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return AdminUserResponse.model_validate(user)


@router.post("/users", response_model=AdminUserResponse, summary="创建用户")
async def create_user(
    user_data: CreateUserRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新用户（管理员）"""
    # 检查用户名是否存在
    existing = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )

    # 创建用户
    user = await User.create_user(
        db_session=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        display_name=user_data.display_name
    )

    # 设置管理员权限
    if user_data.is_admin:
        user.is_admin = True
        await db.commit()
        await db.refresh(user)

    return AdminUserResponse.model_validate(user)


@router.delete("/users/{user_id}", response_model=MessageResponse, summary="删除用户")
async def delete_user(
    user_id: UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户（管理员）"""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    await db.delete(user)
    await db.commit()

    return MessageResponse(message="用户已删除")


@router.post("/users/{user_id}/toggle-active", response_model=AdminUserResponse, summary="切换用户激活状态")
async def toggle_user_active(
    user_id: UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """切换用户激活状态（管理员）"""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)

    return AdminUserResponse.model_validate(user)


@router.get("/settings", response_model=SystemSettingsResponse, summary="获取系统设置")
async def get_system_settings(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统设置（管理员）"""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == 'allow_registration')
    )
    setting = result.scalar_one_or_none()

    allow_registration = True
    if setting and setting.value:
        allow_registration = setting.value.lower() == 'true'

    return SystemSettingsResponse(allow_registration=allow_registration)


@router.put("/settings", response_model=SystemSettingsResponse, summary="更新系统设置")
async def update_system_settings(
    settings: SystemSettingsUpdateRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新系统设置（管理员）"""
    if settings.allow_registration is not None:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == 'allow_registration')
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = str(settings.allow_registration).lower()
        else:
            setting = SystemSetting(
                key='allow_registration',
                value=str(settings.allow_registration).lower(),
                description='是否允许用户注册'
            )
            db.add(setting)

        await db.commit()

    return await get_system_settings(admin_user, db)


__all__ = ["router"]
