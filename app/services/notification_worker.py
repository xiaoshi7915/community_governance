"""
通知后台处理服务
处理通知发送、重试和状态更新
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.notification import Notification, NotificationStatus
from app.services.notification_service import notification_service


logger = logging.getLogger(__name__)


class NotificationWorker:
    """通知后台处理器"""
    
    def __init__(self):
        self.notification_service = notification_service
        self.is_running = False
        self.worker_task = None
    
    async def start(self):
        """启动后台处理器"""
        if self.is_running:
            logger.warning("Notification worker is already running")
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Notification worker started")
    
    async def stop(self):
        """停止后台处理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Notification worker stopped")
    
    async def _worker_loop(self):
        """后台处理循环"""
        while self.is_running:
            try:
                # 处理待发送的通知
                await self._process_pending_notifications()
                
                # 重试失败的通知
                await self._retry_failed_notifications()
                
                # 清理过期的通知
                await self._cleanup_old_notifications()
                
                # 等待下一次处理
                await asyncio.sleep(30)  # 每30秒处理一次
            
            except Exception as e:
                logger.error(f"Error in notification worker loop: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间
    
    async def _process_pending_notifications(self):
        """处理待发送的通知"""
        try:
            async with AsyncSessionLocal() as db:
                # 查询待发送的通知
                result = await db.execute(
                    select(Notification)
                    .where(Notification.status == NotificationStatus.PENDING)
                    .limit(50)  # 每次处理50个
                )
                pending_notifications = result.scalars().all()
                
                if not pending_notifications:
                    return
                
                logger.info(f"Processing {len(pending_notifications)} pending notifications")
                
                # 并发发送通知
                send_tasks = []
                for notification in pending_notifications:
                    task = self._send_notification_safe(notification.id, db)
                    send_tasks.append(task)
                
                if send_tasks:
                    await asyncio.gather(*send_tasks, return_exceptions=True)
        
        except Exception as e:
            logger.error(f"Error processing pending notifications: {e}")
    
    async def _send_notification_safe(self, notification_id, db: AsyncSession):
        """安全发送通知（捕获异常）"""
        try:
            await self.notification_service.send_notification(notification_id, db)
        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {e}")
    
    async def _retry_failed_notifications(self):
        """重试失败的通知"""
        try:
            retry_count = await self.notification_service.retry_failed_notifications()
            if retry_count > 0:
                logger.info(f"Retried {retry_count} failed notifications")
        
        except Exception as e:
            logger.error(f"Error retrying failed notifications: {e}")
    
    async def _cleanup_old_notifications(self):
        """清理过期的通知"""
        try:
            async with AsyncSessionLocal() as db:
                # 删除30天前的已读通知
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                result = await db.execute(
                    select(Notification)
                    .where(
                        and_(
                            Notification.status == NotificationStatus.READ,
                            Notification.read_at < thirty_days_ago
                        )
                    )
                    .limit(100)  # 每次清理100个
                )
                old_notifications = result.scalars().all()
                
                if old_notifications:
                    for notification in old_notifications:
                        await db.delete(notification)
                    
                    await db.commit()
                    logger.info(f"Cleaned up {len(old_notifications)} old notifications")
        
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
    
    async def process_notification_batch(self, notification_ids: List[str]):
        """批量处理指定的通知"""
        try:
            async with AsyncSessionLocal() as db:
                send_tasks = []
                for notification_id in notification_ids:
                    task = self._send_notification_safe(notification_id, db)
                    send_tasks.append(task)
                
                if send_tasks:
                    await asyncio.gather(*send_tasks, return_exceptions=True)
                    logger.info(f"Processed batch of {len(notification_ids)} notifications")
        
        except Exception as e:
            logger.error(f"Error processing notification batch: {e}")


# 创建全局通知处理器实例
notification_worker = NotificationWorker()