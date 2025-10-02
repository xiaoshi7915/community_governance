"""
性能监控中间件
记录API请求的响应时间和性能指标
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.logging import performance_logger, get_logger
from app.core.metrics import performance_monitor


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(self.__class__.__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """监控请求性能"""
        start_time = time.time()
        error_message = None
        response = None
        
        try:
            # 处理请求
            response = await call_next(request)
            return response
        except Exception as e:
            # 记录异常信息
            error_message = str(e)
            raise
        finally:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 获取响应状态码
            status_code = getattr(response, 'status_code', 500) if response else 500
            
            # 获取用户ID（如果有）
            user_id = None
            if hasattr(request.state, 'current_user') and request.state.current_user:
                user_id = str(request.state.current_user.id)
            
            # 获取请求ID
            request_id = getattr(request.state, 'request_id', None)
            
            # 记录到性能监控系统
            await performance_monitor.record_request(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                response_time=process_time,
                user_id=user_id,
                error=error_message
            )
            
            # 记录性能日志
            performance_logger.log_api_performance(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                process_time=process_time,
                request_id=request_id
            )
            
            # 添加性能头
            if response:
                response.headers["X-Process-Time"] = str(process_time)


class DatabasePerformanceMonitor:
    """数据库性能监控器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    async def monitor_query(self, operation: str, table: str, query_func):
        """监控数据库查询性能"""
        start_time = time.time()
        
        try:
            result = await query_func()
            execution_time = time.time() - start_time
            
            # 记录性能日志
            performance_logger.log_database_performance(
                operation=operation,
                table=table,
                execution_time=execution_time
            )
            
            # 如果查询时间过长，记录警告
            if execution_time > 1.0:  # 超过1秒
                self.logger.warning(
                    "数据库查询耗时过长",
                    operation=operation,
                    table=table,
                    execution_time=execution_time
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.error(
                "数据库查询失败",
                operation=operation,
                table=table,
                execution_time=execution_time,
                error=str(e)
            )
            
            raise


class ExternalServiceMonitor:
    """外部服务性能监控器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    async def monitor_service_call(self, service: str, operation: str, call_func):
        """监控外部服务调用性能"""
        start_time = time.time()
        success = False
        
        try:
            result = await call_func()
            success = True
            response_time = time.time() - start_time
            
            # 记录性能日志
            performance_logger.log_external_service_performance(
                service=service,
                operation=operation,
                response_time=response_time,
                success=success
            )
            
            # 如果响应时间过长，记录警告
            if response_time > 5.0:  # 超过5秒
                self.logger.warning(
                    "外部服务响应时间过长",
                    service=service,
                    operation=operation,
                    response_time=response_time
                )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # 记录性能日志
            performance_logger.log_external_service_performance(
                service=service,
                operation=operation,
                response_time=response_time,
                success=success
            )
            
            self.logger.error(
                "外部服务调用失败",
                service=service,
                operation=operation,
                response_time=response_time,
                error=str(e)
            )
            
            raise


# 创建全局监控器实例
db_monitor = DatabasePerformanceMonitor()
external_service_monitor = ExternalServiceMonitor()