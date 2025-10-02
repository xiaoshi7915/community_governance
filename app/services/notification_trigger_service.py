"""
通知触发器服务
处理事件状态变化时的自动通知触发
"""
import asyncio
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import EventStatus
from app.services.notification_service import notification_service


logger = logging.getLogger(__name__)


class NotificationTriggerService:
    """通知触发器服务"""
    
    def __init__(self):
        self.notification_service = notification_service
    
    async def trigger_event_status_change_notifications(
        self,
        event_id: UUID,
        old_status: EventStatus,
        new_status: EventStatus,
        db: Optional[AsyncSession] = None
    ) -> List[str]:
        """
        触发事件状态变更通知
        
        Args:
            event_id: 事件ID
            old_status: 原状态
            new_status: 新状态
            db: 数据库会话
            
        Returns:
            List[str]: 创建的通知ID列表
        """
        try:
            # 创建状态变更通知
            notifications = await self.notification_service.create_event_status_notification(
                event_id=event_id,
                old_status=old_status,
                new_status=new_status,
                db=db
            )
            
            notification_ids = []
            
            # 异步发送所有通知
            send_tasks = []
            for notification in notifications:
                notification_ids.append(str(notification.id))
                # 创建发送任务
                task = self._send_notification_async(notification.id, db)
                send_tasks.append(task)
            
            # 并发发送通知
            if send_tasks:
                await asyncio.gather(*send_tasks, return_exceptions=True)
            
            logger.info(f"Triggered {len(notifications)} notifications for event {event_id} status change: {old_status.value} -> {new_status.value}")
            
            return notification_ids
        
        except Exception as e:
            logger.error(f"Failed to trigger event status change notifications: {e}")
            return []
    
    async def _send_notification_async(self, notification_id: UUID, db: Optional[AsyncSession] = None):
        """异步发送通知"""
        try:
            await self.notification_service.send_notification(notification_id, db)
        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {e}")
    
    async def trigger_event_assigned_notification(
        self,
        event_id: UUID,
        assigned_user_id: UUID,
        assigner_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> List[str]:
        """
        触发事件分配通知
        
        Args:
            event_id: 事件ID
            assigned_user_id: 被分配用户ID
            assigner_id: 分配者ID
            db: 数据库会话
            
        Returns:
            List[str]: 创建的通知ID列表
        """
        # TODO: 实现事件分配通知逻辑
        # 这里可以根据业务需求实现事件分配给特定用户的通知
        logger.info(f"Event {event_id} assigned to user {assigned_user_id} by {assigner_id}")
        return []
    
    async def trigger_event_reminder_notification(
        self,
        event_id: UUID,
        reminder_type: str = "processing_timeout",
        db: Optional[AsyncSession] = None
    ) -> List[str]:
        """
        触发事件提醒通知
        
        Args:
            event_id: 事件ID
            reminder_type: 提醒类型
            db: 数据库会话
            
        Returns:
            List[str]: 创建的通知ID列表
        """
        # TODO: 实现事件提醒通知逻辑
        # 例如：处理超时提醒、定期状态检查提醒等
        logger.info(f"Event {event_id} reminder triggered: {reminder_type}")
        return []
    
    async def trigger_system_announcement(
        self,
        title: str,
        content: str,
        target_users: Optional[List[UUID]] = None,
        priority: str = "normal",
        db: Optional[AsyncSession] = None
    ) -> List[str]:
        """
        触发系统公告通知
        
        Args:
            title: 公告标题
            content: 公告内容
            target_users: 目标用户列表（None表示所有用户）
            priority: 优先级
            db: 数据库会话
            
        Returns:
            List[str]: 创建的通知ID列表
        """
        # TODO: 实现系统公告通知逻辑
        # 需要查询目标用户，为每个用户创建通知
        logger.info(f"System announcement triggered: {title}")
        return []
    
    async def trigger_maintenance_notice(
        self,
        maintenance_time: str,
        duration: str,
        maintenance_content: str,
        advance_hours: int = 24,
        db: Optional[AsyncSession] = None
    ) -> List[str]:
        """
        触发维护通知
        
        Args:
            maintenance_time: 维护时间
            duration: 维护时长
            maintenance_content: 维护内容
            advance_hours: 提前通知小时数
            db: 数据库会话
            
        Returns:
            List[str]: 创建的通知ID列表
        """
        # TODO: 实现维护通知逻辑
        # 需要查询所有活跃用户，创建维护通知
        logger.info(f"Maintenance notice triggered: {maintenance_time}")
        return []


# 创建全局通知触发器服务实例
notification_trigger_service = NotificationTriggerService()