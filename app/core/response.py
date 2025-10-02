"""
统一API响应格式处理器
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union, TypeVar, Generic
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """API响应模型"""
    success: bool
    data: Optional[T] = None
    message: str
    code: int
    timestamp: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: ErrorDetail
    timestamp: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResponseFormatter:
    """响应格式化工具类"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """
        创建成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            status_code: HTTP状态码
            
        Returns:
            JSONResponse: 格式化的成功响应
        """
        response_data = APIResponse(
            success=True,
            data=data,
            message=message,
            code=status_code,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response_data.dict()
        )
    
    @staticmethod
    def error(
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> JSONResponse:
        """
        创建错误响应
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
            status_code: HTTP状态码
            
        Returns:
            JSONResponse: 格式化的错误响应
        """
        response_data = ErrorResponse(
            error=ErrorDetail(
                code=error_code,
                message=message,
                details=details
            ),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response_data.dict()
        )
    
    @staticmethod
    def validation_error(
        message: str = "输入数据验证失败",
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        创建验证错误响应
        
        Args:
            message: 错误消息
            details: 验证错误详情
            
        Returns:
            JSONResponse: 验证错误响应
        """
        return ResponseFormatter.error(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def authentication_error(
        message: str = "认证失败"
    ) -> JSONResponse:
        """
        创建认证错误响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse: 认证错误响应
        """
        return ResponseFormatter.error(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def authorization_error(
        message: str = "权限不足"
    ) -> JSONResponse:
        """
        创建授权错误响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse: 授权错误响应
        """
        return ResponseFormatter.error(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def not_found_error(
        message: str = "资源不存在"
    ) -> JSONResponse:
        """
        创建资源不存在错误响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse: 资源不存在错误响应
        """
        return ResponseFormatter.error(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def conflict_error(
        message: str = "资源冲突"
    ) -> JSONResponse:
        """
        创建资源冲突错误响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse: 资源冲突错误响应
        """
        return ResponseFormatter.error(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT
        )
    
    @staticmethod
    def external_service_error(
        message: str = "外部服务不可用",
        service_name: str = "unknown"
    ) -> JSONResponse:
        """
        创建外部服务错误响应
        
        Args:
            message: 错误消息
            service_name: 服务名称
            
        Returns:
            JSONResponse: 外部服务错误响应
        """
        return ResponseFormatter.error(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name},
            status_code=status.HTTP_502_BAD_GATEWAY
        )


# 创建全局响应格式化器实例
response_formatter = ResponseFormatter()


def create_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    """
    创建响应数据字典（用于FastAPI路由返回）
    
    Args:
        data: 响应数据
        message: 响应消息
        status_code: HTTP状态码
        
    Returns:
        Dict[str, Any]: 响应数据字典
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }