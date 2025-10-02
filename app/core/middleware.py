"""
中间件模块
包含异常处理、请求日志等中间件
"""
import time
import traceback
import uuid
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.exceptions import (
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
from app.core.response import ResponseFormatter
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(self.__class__.__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并捕获异常"""
        try:
            response = await call_next(request)
            return response
            
        except BaseCustomException as e:
            # 处理自定义异常
            self.logger.warning(
                "业务异常",
                error_code=e.code,
                error_message=e.message,
                error_details=e.details,
                path=request.url.path,
                method=request.method
            )
            
            return self._create_error_response(e)
            
        except Exception as e:
            # 处理未预期的异常
            self.logger.error(
                "系统异常",
                error_message=str(e),
                error_traceback=traceback.format_exc(),
                path=request.url.path,
                method=request.method
            )
            
            return ResponseFormatter.error(
                message="系统内部错误",
                error_code="INTERNAL_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_error_response(self, exception: BaseCustomException) -> JSONResponse:
        """根据异常类型创建相应的错误响应"""
        
        if isinstance(exception, ValidationError):
            return ResponseFormatter.validation_error(
                message=exception.message,
                details=exception.details
            )
        
        elif isinstance(exception, AuthenticationError):
            return ResponseFormatter.authentication_error(
                message=exception.message
            )
        
        elif isinstance(exception, AuthorizationError):
            return ResponseFormatter.authorization_error(
                message=exception.message
            )
        
        elif isinstance(exception, NotFoundError):
            return ResponseFormatter.not_found_error(
                message=exception.message
            )
        
        elif isinstance(exception, ConflictError):
            return ResponseFormatter.conflict_error(
                message=exception.message
            )
        
        elif isinstance(exception, ExternalServiceError):
            return ResponseFormatter.external_service_error(
                message=exception.message,
                service_name=exception.details.get("service", "unknown")
            )
        
        elif isinstance(exception, (DatabaseError, FileUploadError, AIServiceError)):
            return ResponseFormatter.error(
                message=exception.message,
                error_code=exception.code,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        else:
            # 其他自定义异常
            return ResponseFormatter.error(
                message=exception.message,
                error_code=exception.code,
                details=exception.details,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(self.__class__.__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """记录请求和响应信息"""
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 记录请求信息
        self.logger.info(
            "请求开始",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "")
        )
        
        # 将请求ID添加到请求状态中
        request.state.request_id = request_id
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            self.logger.info(
                "请求完成",
                request_id=request_id,
                status_code=response.status_code,
                process_time=f"{process_time:.4f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常信息
            self.logger.error(
                "请求异常",
                request_id=request_id,
                error_message=str(e),
                process_time=f"{process_time:.4f}s"
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件（如果需要自定义CORS处理）"""
    
    def __init__(
        self, 
        app: ASGIApp,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        allow_credentials: bool = True
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理CORS"""
        
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            return response
        
        # 处理正常请求
        response = await call_next(request)
        self._add_cors_headers(response, request)
        
        return response
    
    def _add_cors_headers(self, response: Response, request: Request):
        """添加CORS头"""
        origin = request.headers.get("origin")
        
        if origin and (origin in self.allow_origins or "*" in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"