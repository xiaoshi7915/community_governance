"""
日志配置模块
提供结构化日志记录和配置管理
"""
import logging
import logging.handlers
import sys
import os
from typing import Any, Dict, Optional
from datetime import datetime
import structlog
from structlog.types import FilteringBoundLogger
from app.core.config import settings


def add_request_context(logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """添加请求上下文信息到日志"""
    # 尝试从当前上下文获取请求信息
    try:
        from contextvars import copy_context
        context = copy_context()
        request_id = context.get("request_id", None)
        if request_id:
            event_dict["request_id"] = request_id
    except:
        pass
    
    return event_dict


def configure_logging() -> None:
    """配置结构化日志"""
    
    # 确保日志目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 根据环境选择处理器
    if settings.ENVIRONMENT == "production":
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            add_request_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            add_request_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # 配置structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # 创建文件处理器（生产环境）
    if settings.ENVIRONMENT == "production":
        # 应用日志文件
        app_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        app_handler.setLevel(log_level)
        
        # 错误日志文件
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "error.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        
        # 配置根日志记录器
        logging.basicConfig(
            level=log_level,
            format=settings.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(sys.stdout),
                app_handler,
                error_handler
            ]
        )
    else:
        # 开发环境只输出到控制台
        logging.basicConfig(
            format=settings.LOG_FORMAT,
            stream=sys.stdout,
            level=log_level,
        )
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """获取当前类的日志记录器"""
        return get_logger(self.__class__.__name__)


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.logger = get_logger("request")
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, request_id=self.request_id, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, request_id=self.request_id, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, request_id=self.request_id, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, request_id=self.request_id, **kwargs)


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("performance")
    
    def log_api_performance(
        self, 
        method: str, 
        path: str, 
        status_code: int, 
        process_time: float,
        request_id: Optional[str] = None
    ):
        """记录API性能日志"""
        self.logger.info(
            "API性能统计",
            method=method,
            path=path,
            status_code=status_code,
            process_time=process_time,
            request_id=request_id
        )
    
    def log_database_performance(
        self, 
        operation: str, 
        table: str, 
        execution_time: float,
        request_id: Optional[str] = None
    ):
        """记录数据库性能日志"""
        self.logger.info(
            "数据库性能统计",
            operation=operation,
            table=table,
            execution_time=execution_time,
            request_id=request_id
        )
    
    def log_external_service_performance(
        self, 
        service: str, 
        operation: str, 
        response_time: float,
        success: bool,
        request_id: Optional[str] = None
    ):
        """记录外部服务性能日志"""
        self.logger.info(
            "外部服务性能统计",
            service=service,
            operation=operation,
            response_time=response_time,
            success=success,
            request_id=request_id
        )


# 创建全局性能日志记录器实例
performance_logger = PerformanceLogger()