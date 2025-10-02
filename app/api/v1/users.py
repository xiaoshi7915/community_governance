"""
用户管理相关API端点
包含用户资料查询和更新功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import create_response
from app.core.auth_middleware import get_current_active_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserProfileUpdateRequest,
    UserResponse,
    MessageResponse
)
from app.core.exceptions import (
    ValidationError,
    NotFoundError
)
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="获取用户资料",
    description="获取当前登录用户的个人资料信息"
)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户资料端点
    
    需要认证：是
    返回当前登录用户的详细信息
    """
    return create_response(
        data=current_user.to_dict(),
        message="获取用户资料成功"
    )


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="更新用户资料",
    description="更新当前登录用户的个人资料信息"
)
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户资料端点
    
    需要认证：是
    
    - **name**: 用户姓名（可选，2-20位字符）
    - **avatar_url**: 头像URL（可选）
    """
    try:
        auth_service = AuthService(db)
        updated_user = await auth_service.update_user_profile(
            user_id=current_user.id,
            name=request.name,
            avatar_url=request.avatar_url
        )
        
        return create_response(
            data=updated_user.to_dict(),
            message="用户资料更新成功"
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户资料更新失败，请稍后重试"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的基本信息（与/profile相同）"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息端点
    
    需要认证：是
    这是/profile端点的别名，提供相同的功能
    """
    return create_response(
        data=current_user.to_dict(),
        message="获取用户信息成功"
    )