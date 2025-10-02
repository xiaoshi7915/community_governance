"""
认证中间件
用于保护需要登录的API端点
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.exceptions import AuthenticationError


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前认证用户的依赖注入函数
    
    Args:
        credentials: HTTP Bearer 认证凭据
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        auth_service = AuthService(db)
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户的依赖注入函数
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前活跃用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出403错误
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    return current_user


class AuthMiddleware:
    """认证中间件类"""
    
    @staticmethod
    def require_auth():
        """
        需要认证的装饰器
        返回一个依赖注入函数，用于保护需要登录的端点
        """
        return Depends(get_current_active_user)
    
    @staticmethod
    def optional_auth():
        """
        可选认证的装饰器
        返回一个依赖注入函数，用于可选登录的端点
        """
        async def _optional_auth(
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
            db: AsyncSession = Depends(get_db)
        ) -> Optional[User]:
            if not credentials:
                return None
            
            try:
                auth_service = AuthService(db)
                user = await auth_service.verify_token(credentials.credentials)
                return user if user.is_active else None
            except:
                return None
        
        return Depends(_optional_auth)


# 创建全局中间件实例
auth_middleware = AuthMiddleware()