"""
认证相关的Pydantic模式
用于请求和响应数据验证
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class UserRegisterRequest(BaseModel):
    """用户注册请求模式"""
    phone: str = Field(..., description="手机号", example="13800138000")
    password: str = Field(..., description="密码", min_length=6, max_length=20, example="password123")
    name: str = Field(..., description="用户姓名", min_length=2, max_length=20, example="张三")
    verification_code: Optional[str] = Field(None, description="验证码", example="123456")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('用户姓名不能为空')
        return v.strip()


class UserLoginRequest(BaseModel):
    """用户登录请求模式"""
    phone: str = Field(..., description="手机号", example="13800138000")
    password: str = Field(..., description="密码", example="password123")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v


class TokenRefreshRequest(BaseModel):
    """令牌刷新请求模式"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求模式"""
    phone: str = Field(..., description="手机号", example="13800138000")
    new_password: str = Field(..., description="新密码", min_length=6, max_length=20, example="newpassword123")
    verification_code: str = Field(..., description="验证码", example="123456")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v


class UserProfileUpdateRequest(BaseModel):
    """用户资料更新请求模式"""
    name: Optional[str] = Field(None, description="用户姓名", min_length=2, max_length=20, example="李四")
    avatar_url: Optional[str] = Field(None, description="头像URL", example="https://example.com/avatar.jpg")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('用户姓名不能为空')
        return v.strip() if v else v


class UserResponse(BaseModel):
    """用户信息响应模式"""
    id: str = Field(..., description="用户ID")
    phone: str = Field(..., description="手机号")
    name: str = Field(..., description="用户姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(..., description="是否激活")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: Optional[UserResponse] = Field(None, description="用户信息")


class TokenRefreshResponse(BaseModel):
    """令牌刷新响应模式"""
    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class SendCodeRequest(BaseModel):
    """发送验证码请求模式"""
    phone: str = Field(..., description="手机号", example="13800138000")
    type: str = Field(default="register", description="验证码类型", example="register")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式不正确')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ['register', 'reset_password', 'bind_phone']:
            raise ValueError('验证码类型不正确')
        return v


class MessageResponse(BaseModel):
    """消息响应模式"""
    message: str = Field(..., description="响应消息")
    success: bool = Field(default=True, description="是否成功")