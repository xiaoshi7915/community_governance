"""
通知系统初始化
在应用启动时初始化通知模板和启动后台处理器
"""
import asyncio
import logging

from app.services.notification_template_service import notification_template_service
from app.services.notification_worker import notification_worker


logger = logging.getLogger(__name__)


async def initialize_notification_system():
    """初始化通知系统"""
    try:
        logger.info("Initializing notification system...")
        
        # 初始化默认通知模板
        await notification_template_service.initialize_default_templates()
        logger.info("Notification templates initialized")
        
        # 启动通知后台处理器
        await notification_worker.start()
        logger.info("Notification worker started")
        
        logger.info("Notification system initialized successfully")
    
    except Exception as e:
        logger.error(f"Failed to initialize notification system: {e}")
        raise


async def shutdown_notification_system():
    """关闭通知系统"""
    try:
        logger.info("Shutting down notification system...")
        
        # 停止通知后台处理器
        await notification_worker.stop()
        logger.info("Notification worker stopped")
        
        logger.info("Notification system shutdown completed")
    
    except Exception as e:
        logger.error(f"Error shutting down notification system: {e}")


def setup_notification_system_events(app):
    """设置通知系统的启动和关闭事件"""
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        await initialize_notification_system()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        await shutdown_notification_system()