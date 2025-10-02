"""
认证相关API端点
包含用户注册、登录、令牌刷新等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import create_response
from app.core.auth_middleware import get_current_active_user
from app.services.auth_service import AuthService
from app.services.sms_service import sms_service
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    PasswordResetRequest,
    SendCodeRequest,
    TokenResponse,
    TokenRefreshResponse,
    MessageResponse,
    UserResponse
)
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    ConflictError,
    NotFoundError
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息
    """
    return create_response(
        data={
            "id": str(current_user.id),
            "phone": current_user.phone,
            "name": current_user.name,
            "avatar_url": current_user.avatar_url,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at
        }
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="用户通过手机号和密码注册新账户"
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册端点
    
    - **phone**: 手机号（11位数字）
    - **password**: 密码（6-20位字符）
    - **name**: 用户姓名（2-20位字符）
    - **verification_code**: 验证码（可选）
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.register(
            phone=request.phone,
            password=request.password,
            name=request.name,
            verification_code=request.verification_code
        )
        
        return create_response(
            data=result,
            message="注册成功"
        )
        
    except (ValidationError, ConflictError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="用户通过手机号和密码登录"
)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录端点
    
    - **phone**: 手机号
    - **password**: 密码
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.login(
            phone=request.phone,
            password=request.password
        )
        
        # 直接返回TokenResponse格式
        return TokenResponse(**result)
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"登录异常: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌"
)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新令牌端点
    
    - **refresh_token**: 刷新令牌
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(request.refresh_token)
        
        return create_response(
            data=result,
            message="令牌刷新成功"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败，请稍后重试"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="用户登出",
    description="用户登出（客户端需要清除本地令牌）"
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    用户登出端点
    
    注意：由于使用JWT令牌，服务端无法主动使令牌失效，
    客户端需要清除本地存储的令牌。
    在实际项目中，可以考虑使用Redis黑名单来管理已登出的令牌。
    """
    # TODO: 在实际项目中可以将令牌加入Redis黑名单
    return create_response(
        data={"message": "登出成功"},
        message="登出成功"
    )


@router.post(
    "/send-code",
    response_model=MessageResponse,
    summary="发送验证码",
    description="向指定手机号发送验证码"
)
async def send_verification_code(
    request: SendCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送验证码端点
    
    - **phone**: 手机号（11位数字）
    - **type**: 验证码类型（register, reset_password, bind_phone）
    """
    try:
        # 发送验证码
        result = await sms_service.send_verification_code(
            phone_number=request.phone,
            code_type=request.type
        )
        
        if result["success"]:
            return create_response(
                data={
                    "message": "验证码发送成功",
                    "code": result.get("code") if result.get("code") else None  # 开发环境返回验证码
                },
                message="验证码发送成功"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试"
        )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="重置密码",
    description="通过手机验证码重置密码"
)
async def reset_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    重置密码端点
    
    - **phone**: 手机号
    - **new_password**: 新密码（6-20位字符）
    - **verification_code**: 验证码
    """
    try:
        auth_service = AuthService(db)
        await auth_service.reset_password(
            phone=request.phone,
            new_password=request.new_password,
            verification_code=request.verification_code
        )
        
        return create_response(
            data={"message": "密码重置成功"},
            message="密码重置成功"
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (ValidationError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败，请稍后重试"
        )