"""
性能监控中间件
记录API性能指标、资源使用情况和响应时间
"""
import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger, performance_logger
from app.core.monitoring import metrics_collector, alert_manager

logger = get_logger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(self.__class__.__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """监控请求性能"""
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录性能指标
            metrics_collector.record_api_metrics(
                endpoint=path,
                method=method,
                response_time=process_time,
                status_code=response.status_code,
                request_id=request_id
            )
            
            # 记录性能日志
            performance_logger.log_api_performance(
                method=method,
                path=path,
                status_code=response.status_code,
                process_time=process_time,
                request_id=request_id
            )
            
            # 检查性能告警
            from app.core.monitoring import APIMetrics
            from datetime import datetime
            
            api_metrics = APIMetrics(
                endpoint=path,
                method=method,
                response_time=process_time,
                status_code=response.status_code,
                timestamp=datetime.now(),
                request_id=request_id
            )
            
            # 异步检查告警（不阻塞响应）
            asyncio.create_task(alert_manager.check_api_alerts(api_metrics))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误指标
            metrics_collector.record_api_metrics(
                endpoint=path,
                method=method,
                response_time=process_time,
                status_code=500,
                request_id=request_id
            )
            
            # 记录错误日志
            self.logger.error(
                "请求处理异常",
                method=method,
                path=path,
                process_time=process_time,
                request_id=request_id,
                error=str(e)
            )
            
            raise


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