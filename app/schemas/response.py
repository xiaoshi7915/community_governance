"""
API响应数据模型
"""
from datetime import datetime
from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """统一API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field(..., description="响应消息")
    code: int = Field(200, description="状态码")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[dict] = Field(None, description="错误详情")


class ErrorResponseModel(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作是否成功")
    error: ErrorDetail = Field(..., description="错误信息")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationModel(BaseModel):
    """分页信息模型"""
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedResponseModel(BaseModel, Generic[T]):
    """分页响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: list[T] = Field(..., description="数据列表")
    pagination: PaginationModel = Field(..., description="分页信息")
    message: str = Field(..., description="响应消息")
    code: int = Field(200, description="状态码")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }