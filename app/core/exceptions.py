"""
自定义异常类
"""
from typing import Any, Dict, Optional


class BaseCustomException(Exception):
    """基础自定义异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseCustomException):
    """数据验证错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(BaseCustomException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(BaseCustomException):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class NotFoundError(BaseCustomException):
    """资源不存在错误"""
    
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, "NOT_FOUND")


class ConflictError(BaseCustomException):
    """资源冲突错误"""
    
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, "CONFLICT")


class ExternalServiceError(BaseCustomException):
    """外部服务错误"""
    
    def __init__(self, message: str, service_name: str = "external_service"):
        super().__init__(
            message, 
            "EXTERNAL_SERVICE_ERROR",
            {"service": service_name}
        )


class DatabaseError(BaseCustomException):
    """数据库操作错误"""
    
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message, "DATABASE_ERROR")


class FileUploadError(BaseCustomException):
    """文件上传错误"""
    
    def __init__(self, message: str = "文件上传失败"):
        super().__init__(message, "FILE_UPLOAD_ERROR")


class AIServiceError(BaseCustomException):
    """AI服务错误"""
    
    def __init__(self, message: str = "AI服务调用失败"):
        super().__init__(message, "AI_SERVICE_ERROR")