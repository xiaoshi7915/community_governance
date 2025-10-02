"""
核心配置和工具包
提供应用程序的核心功能模块
"""

# 配置
from .config import settings

# 安全工具
from .security import PasswordManager, JWTManager, password_manager, jwt_manager

# 响应格式化
from .response import ResponseFormatter, APIResponse, ErrorResponse, response_formatter

# 异常处理
from .exceptions import (
    BaseCustomException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    DatabaseError,
    FileUploadError,
    AIServiceError
)

# 中间件
from .middleware import (
    ExceptionHandlerMiddleware,
    RequestLoggingMiddleware,
    CORSMiddleware
)

# 日志记录
from .logging import (
    configure_logging,
    get_logger,
    LoggerMixin,
    RequestLogger,
    PerformanceLogger,
    performance_logger
)

# 工具函数
from .utils import (
    ValidationUtils,
    DateTimeUtils,
    StringUtils,
    DictUtils,
    ListUtils,
    validation_utils,
    datetime_utils,
    string_utils,
    dict_utils,
    list_utils
)

__all__ = [
    # 配置
    "settings",
    
    # 安全工具
    "PasswordManager",
    "JWTManager", 
    "password_manager",
    "jwt_manager",
    
    # 响应格式化
    "ResponseFormatter",
    "APIResponse",
    "ErrorResponse",
    "response_formatter",
    
    # 异常处理
    "BaseCustomException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "ExternalServiceError",
    "DatabaseError",
    "FileUploadError",
    "AIServiceError",
    
    # 中间件
    "ExceptionHandlerMiddleware",
    "RequestLoggingMiddleware",
    "CORSMiddleware",
    
    # 日志记录
    "configure_logging",
    "get_logger",
    "LoggerMixin",
    "RequestLogger",
    "PerformanceLogger",
    "performance_logger",
    
    # 工具函数
    "ValidationUtils",
    "DateTimeUtils",
    "StringUtils",
    "DictUtils",
    "ListUtils",
    "validation_utils",
    "datetime_utils",
    "string_utils",
    "dict_utils",
    "list_utils",
]