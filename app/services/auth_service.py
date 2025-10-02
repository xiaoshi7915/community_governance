"""
用户认证服务
包含用户注册、登录、令牌管理等功能
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.security import password_manager, jwt_manager
from app.core.exceptions import (
    AuthenticationError, 
    ValidationError, 
    ConflictError,
    NotFoundError
)
from app.core.config import settings


class AuthService:
    """用户认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register(
        self, 
        phone: str, 
        password: str, 
        name: str,
        verification_code: Optional[str] = None
    ) -> Dict[str, str]:
        """
        用户注册
        
        Args:
            phone: 手机号
            password: 密码
            name: 用户姓名
            verification_code: 验证码（可选，实际项目中需要验证）
            
        Returns:
            Dict[str, str]: 包含访问令牌和刷新令牌
            
        Raises:
            ValidationError: 输入数据验证失败
            ConflictError: 用户已存在
        """
        # 验证输入数据
        self._validate_phone(phone)
        self._validate_password(password)
        self._validate_name(name)
        
        # TODO: 在实际项目中需要验证手机验证码
        # if verification_code:
        #     await self._verify_sms_code(phone, verification_code)
        
        # 检查用户是否已存在
        existing_user = await self._get_user_by_phone(phone)
        if existing_user:
            raise ConflictError("手机号已被注册")
        
        # 创建新用户
        password_hash = password_manager.hash_password(password)
        user = User(
            phone=phone,
            password_hash=password_hash,
            name=name,
            is_active=True
        )
        
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("手机号已被注册")
        
        # 生成令牌
        tokens = self._generate_tokens(user)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "user": user.to_dict()
        }
    
    async def login(self, phone: str, password: str) -> Dict[str, str]:
        """
        用户登录
        
        Args:
            phone: 手机号
            password: 密码
            
        Returns:
            Dict[str, str]: 包含访问令牌和刷新令牌
            
        Raises:
            AuthenticationError: 认证失败
        """
        # 验证输入数据
        self._validate_phone(phone)
        self._validate_password(password)
        
        # 获取用户
        user = await self._get_user_by_phone(phone)
        if not user:
            raise AuthenticationError("手机号或密码错误")
        
        # 检查用户状态
        if not user.is_active:
            raise AuthenticationError("用户账户已被禁用")
        
        # 验证密码
        if not password_manager.verify_password(password, user.password_hash):
            raise AuthenticationError("手机号或密码错误")
        
        # 生成令牌
        tokens = self._generate_tokens(user)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "user": user.to_dict()
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Dict[str, str]: 新的访问令牌和刷新令牌
            
        Raises:
            AuthenticationError: 令牌无效
        """
        try:
            # 验证刷新令牌
            payload = jwt_manager.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("令牌缺少用户信息")
            
            # 获取用户
            user = await self._get_user_by_id(uuid.UUID(user_id))
            if not user:
                raise AuthenticationError("用户不存在")
            
            if not user.is_active:
                raise AuthenticationError("用户账户已被禁用")
            
            # 生成新令牌
            tokens = self._generate_tokens(user)
            
            return {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer"
            }
            
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(f"令牌刷新失败: {str(e)}")
    
    async def verify_token(self, token: str) -> User:
        """
        验证访问令牌并返回用户信息
        
        Args:
            token: 访问令牌
            
        Returns:
            User: 用户对象
            
        Raises:
            AuthenticationError: 令牌无效
        """
        try:
            # 验证令牌
            payload = jwt_manager.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("令牌缺少用户信息")
            
            # 获取用户
            user = await self._get_user_by_id(uuid.UUID(user_id))
            if not user:
                raise AuthenticationError("用户不存在")
            
            if not user.is_active:
                raise AuthenticationError("用户账户已被禁用")
            
            return user
            
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(f"令牌验证失败: {str(e)}")
    
    async def update_user_profile(
        self, 
        user_id: uuid.UUID, 
        name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            name: 新的用户姓名
            avatar_url: 新的头像URL
            
        Returns:
            User: 更新后的用户对象
            
        Raises:
            NotFoundError: 用户不存在
            ValidationError: 输入数据验证失败
        """
        # 获取用户
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")
        
        # 更新字段
        if name is not None:
            self._validate_name(name)
            user.name = name
        
        if avatar_url is not None:
            user.avatar_url = avatar_url
        
        # 保存更改
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"更新用户资料失败: {str(e)}")
    
    async def reset_password(
        self, 
        phone: str, 
        new_password: str,
        verification_code: str
    ) -> bool:
        """
        重置密码
        
        Args:
            phone: 手机号
            new_password: 新密码
            verification_code: 验证码
            
        Returns:
            bool: 是否成功
            
        Raises:
            NotFoundError: 用户不存在
            ValidationError: 输入数据验证失败
            AuthenticationError: 验证码错误
        """
        # 验证输入数据
        self._validate_phone(phone)
        self._validate_password(new_password)
        
        # TODO: 在实际项目中需要验证手机验证码
        # await self._verify_sms_code(phone, verification_code)
        
        # 获取用户
        user = await self._get_user_by_phone(phone)
        if not user:
            raise NotFoundError("用户不存在")
        
        # 更新密码
        user.password_hash = password_manager.hash_password(new_password)
        
        try:
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"密码重置失败: {str(e)}")
    
    def _generate_tokens(self, user: User) -> Dict[str, str]:
        """
        生成访问令牌和刷新令牌
        
        Args:
            user: 用户对象
            
        Returns:
            Dict[str, str]: 包含访问令牌和刷新令牌
        """
        token_data = {"sub": str(user.id), "phone": user.phone}
        
        access_token = jwt_manager.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            data=token_data,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def _get_user_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """根据用户ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    def _validate_phone(self, phone: str) -> None:
        """验证手机号格式"""
        if not phone:
            raise ValidationError("手机号不能为空")
        
        if not phone.isdigit():
            raise ValidationError("手机号只能包含数字")
        
        if len(phone) != 11:
            raise ValidationError("手机号必须为11位数字")
        
        if not phone.startswith(('13', '14', '15', '16', '17', '18', '19')):
            raise ValidationError("手机号格式不正确")
    
    def _validate_password(self, password: str) -> None:
        """验证密码格式"""
        if not password:
            raise ValidationError("密码不能为空")
        
        if len(password) < 6:
            raise ValidationError("密码长度不能少于6位")
        
        if len(password) > 20:
            raise ValidationError("密码长度不能超过20位")
    
    def _validate_name(self, name: str) -> None:
        """验证用户姓名格式"""
        if not name:
            raise ValidationError("用户姓名不能为空")
        
        if len(name.strip()) < 2:
            raise ValidationError("用户姓名长度不能少于2位")
        
        if len(name) > 20:
            raise ValidationError("用户姓名长度不能超过20位")
    
    # TODO: 实际项目中需要实现短信验证码功能
    # async def _verify_sms_code(self, phone: str, code: str) -> None:
    #     """验证短信验证码"""
    #     # 这里应该调用短信服务提供商的API验证验证码
    #     pass