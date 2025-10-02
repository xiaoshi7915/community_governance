"""
通知推送服务
支持多种通知渠道：推送、短信、邮件、应用内通知
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

import aiohttp
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.notification import (
    Notification, UserNotificationPreference, NotificationTemplate,
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)
from app.models.user import User
from app.models.event import Event, EventStatus


logger = logging.getLogger(__name__)


class NotificationChannelHandler:
    """通知渠道处理器基类"""
    
    def __init__(self, channel: NotificationChannel):
        self.channel = channel
    
    async def send(self, notification: Notification) -> Dict[str, Any]:
        """发送通知"""
        raise NotImplementedError
    
    async def check_delivery_status(self, notification: Notification) -> Optional[NotificationStatus]:
        """检查送达状态"""
        return None


class PushNotificationHandler(NotificationChannelHandler):
    """推送通知处理器"""
    
    def __init__(self):
        super().__init__(NotificationChannel.PUSH)
        self.push_service_url = getattr(settings, 'PUSH_SERVICE_URL', '')
        self.push_service_key = getattr(settings, 'PUSH_SERVICE_KEY', '')
    
    async def send(self, notification: Notification) -> Dict[str, Any]:
        """发送推送通知"""
        try:
            if not self.push_service_url:
                logger.warning("Push service URL not configured")
                return {"success": False, "error": "Push service not configured"}
            
            payload = {
                "to": notification.recipient,
                "title": notification.title,
                "body": notification.content,
                "data": notification.data or {},
                "priority": notification.priority.value
            }
            
            headers = {
                "Authorization": f"Bearer {self.push_service_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.push_service_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "external_id": result.get("message_id"),
                            "response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("error", "Unknown error"),
                            "response": result
                        }
        
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return {"success": False, "error": str(e)}


class SMSNotificationHandler(NotificationChannelHandler):
    """短信通知处理器"""
    
    def __init__(self):
        super().__init__(NotificationChannel.SMS)
        self.sms_service_url = getattr(settings, 'SMS_SERVICE_URL', '')
        self.sms_service_key = getattr(settings, 'SMS_SERVICE_KEY', '')
    
    async def send(self, notification: Notification) -> Dict[str, Any]:
        """发送短信通知"""
        try:
            if not self.sms_service_url:
                logger.warning("SMS service URL not configured")
                return {"success": False, "error": "SMS service not configured"}
            
            payload = {
                "phone": notification.recipient,
                "message": f"{notification.title}\n{notification.content}",
                "template_id": notification.data.get("template_id") if notification.data else None
            }
            
            headers = {
                "Authorization": f"Bearer {self.sms_service_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.sms_service_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "external_id": result.get("message_id"),
                            "response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("error", "Unknown error"),
                            "response": result
                        }
        
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return {"success": False, "error": str(e)}


class EmailNotificationHandler(NotificationChannelHandler):
    """邮件通知处理器"""
    
    def __init__(self):
        super().__init__(NotificationChannel.EMAIL)
        self.email_service_url = getattr(settings, 'EMAIL_SERVICE_URL', '')
        self.email_service_key = getattr(settings, 'EMAIL_SERVICE_KEY', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@governance.com')
    
    async def send(self, notification: Notification) -> Dict[str, Any]:
        """发送邮件通知"""
        try:
            if not self.email_service_url:
                logger.warning("Email service URL not configured")
                return {"success": False, "error": "Email service not configured"}
            
            payload = {
                "to": notification.recipient,
                "from": self.from_email,
                "subject": notification.title,
                "html": notification.content,
                "text": notification.content
            }
            
            headers = {
                "Authorization": f"Bearer {self.email_service_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.email_service_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "external_id": result.get("message_id"),
                            "response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("error", "Unknown error"),
                            "response": result
                        }
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return {"success": False, "error": str(e)}


class InAppNotificationHandler(NotificationChannelHandler):
    """应用内通知处理器"""
    
    def __init__(self):
        super().__init__(NotificationChannel.IN_APP)
    
    async def send(self, notification: Notification) -> Dict[str, Any]:
        """应用内通知直接存储到数据库，无需外部发送"""
        return {
            "success": True,
            "external_id": str(notification.id),
            "response": {"message": "In-app notification stored"}
        }


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.handlers = {
            NotificationChannel.PUSH: PushNotificationHandler(),
            NotificationChannel.SMS: SMSNotificationHandler(),
            NotificationChannel.EMAIL: EmailNotificationHandler(),
            NotificationChannel.IN_APP: InAppNotificationHandler(),
        }
    
    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title: str,
        content: str,
        recipient: str,
        event_id: Optional[UUID] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> Notification:
        """创建通知记录"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._create_notification_impl(
                    db, user_id, notification_type, channel, title, content,
                    recipient, event_id, priority, data
                )
        else:
            return await self._create_notification_impl(
                db, user_id, notification_type, channel, title, content,
                recipient, event_id, priority, data
            )
    
    async def _create_notification_impl(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title: str,
        content: str,
        recipient: str,
        event_id: Optional[UUID] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """创建通知记录的实现"""
        notification = Notification(
            user_id=user_id,
            event_id=event_id,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            title=title,
            content=content,
            recipient=recipient,
            data=data,
            status=NotificationStatus.PENDING
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        logger.info(f"Created notification {notification.id} for user {user_id}")
        return notification
    
    async def send_notification(self, notification_id: UUID, db: Optional[AsyncSession] = None) -> bool:
        """发送通知"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._send_notification_impl(db, notification_id)
        else:
            return await self._send_notification_impl(db, notification_id)
    
    async def _send_notification_impl(self, db: AsyncSession, notification_id: UUID) -> bool:
        """发送通知的实现"""
        # 获取通知记录
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return False
        
        if notification.status != NotificationStatus.PENDING:
            logger.warning(f"Notification {notification_id} is not pending")
            return False
        
        # 检查用户通知偏好
        if not await self._check_user_preference(db, notification):
            logger.info(f"Notification {notification_id} blocked by user preference")
            notification.status = NotificationStatus.FAILED
            notification.error_message = "Blocked by user preference"
            await db.commit()
            return False
        
        # 获取对应的处理器
        handler = self.handlers.get(notification.channel)
        if not handler:
            logger.error(f"No handler for channel {notification.channel}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = f"No handler for channel {notification.channel}"
            await db.commit()
            return False
        
        # 发送通知
        try:
            result = await handler.send(notification)
            
            if result["success"]:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                notification.external_id = result.get("external_id")
                notification.external_response = result.get("response")
                logger.info(f"Successfully sent notification {notification_id}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = result.get("error", "Unknown error")
                notification.external_response = result.get("response")
                logger.error(f"Failed to send notification {notification_id}: {notification.error_message}")
            
            await db.commit()
            return result["success"]
        
        except Exception as e:
            logger.error(f"Error sending notification {notification_id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            await db.commit()
            return False
    
    async def _check_user_preference(self, db: AsyncSession, notification: Notification) -> bool:
        """检查用户通知偏好"""
        # 查询用户偏好
        result = await db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == notification.user_id,
                    UserNotificationPreference.notification_type == notification.notification_type,
                    UserNotificationPreference.channel == notification.channel
                )
            )
        )
        preference = result.scalar_one_or_none()
        
        if preference and not preference.enabled:
            return False
        
        # 检查免打扰时间
        if preference and preference.quiet_hours_start and preference.quiet_hours_end:
            current_time = datetime.now().strftime("%H:%M")
            if preference.quiet_hours_start <= current_time <= preference.quiet_hours_end:
                return False
        
        # 检查频率限制
        if preference and preference.frequency_limit:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.user_id == notification.user_id,
                        Notification.notification_type == notification.notification_type,
                        Notification.channel == notification.channel,
                        Notification.created_at >= one_hour_ago,
                        Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED])
                    )
                )
            )
            recent_notifications = result.scalars().all()
            
            if len(recent_notifications) >= preference.frequency_limit:
                return False
        
        return True
    
    async def retry_failed_notifications(self, db: Optional[AsyncSession] = None) -> int:
        """重试失败的通知"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._retry_failed_notifications_impl(db)
        else:
            return await self._retry_failed_notifications_impl(db)
    
    async def _retry_failed_notifications_impl(self, db: AsyncSession) -> int:
        """重试失败通知的实现"""
        # 查询需要重试的通知
        now = datetime.utcnow()
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.status == NotificationStatus.FAILED,
                    Notification.retry_count < Notification.max_retries,
                    or_(
                        Notification.next_retry_at.is_(None),
                        Notification.next_retry_at <= now
                    )
                )
            ).limit(100)  # 限制批量处理数量
        )
        notifications = result.scalars().all()
        
        retry_count = 0
        for notification in notifications:
            # 更新重试信息
            notification.retry_count += 1
            notification.status = NotificationStatus.PENDING
            notification.next_retry_at = now + timedelta(minutes=5 * notification.retry_count)  # 指数退避
            
            await db.commit()
            
            # 重新发送
            if await self._send_notification_impl(db, notification.id):
                retry_count += 1
        
        logger.info(f"Retried {retry_count} failed notifications")
        return retry_count
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        channel: Optional[NotificationChannel] = None,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> List[Notification]:
        """获取用户通知列表"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._get_user_notifications_impl(
                    db, user_id, channel, status, limit, offset
                )
        else:
            return await self._get_user_notifications_impl(
                db, user_id, channel, status, limit, offset
            )
    
    async def _get_user_notifications_impl(
        self,
        db: AsyncSession,
        user_id: UUID,
        channel: Optional[NotificationChannel] = None,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """获取用户通知列表的实现"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if channel:
            query = query.where(Notification.channel == channel)
        
        if status:
            query = query.where(Notification.status == status)
        
        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def mark_notification_as_read(
        self,
        notification_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """标记通知为已读"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._mark_notification_as_read_impl(db, notification_id)
        else:
            return await self._mark_notification_as_read_impl(db, notification_id)
    
    async def _mark_notification_as_read_impl(self, db: AsyncSession, notification_id: UUID) -> bool:
        """标记通知为已读的实现"""
        result = await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(
                status=NotificationStatus.READ,
                read_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        return result.rowcount > 0
    
    async def create_event_status_notification(
        self,
        event_id: UUID,
        old_status: EventStatus,
        new_status: EventStatus,
        db: Optional[AsyncSession] = None
    ) -> List[Notification]:
        """创建事件状态变更通知"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._create_event_status_notification_impl(
                    db, event_id, old_status, new_status
                )
        else:
            return await self._create_event_status_notification_impl(
                db, event_id, old_status, new_status
            )
    
    async def _create_event_status_notification_impl(
        self,
        db: AsyncSession,
        event_id: UUID,
        old_status: EventStatus,
        new_status: EventStatus
    ) -> List[Notification]:
        """创建事件状态变更通知的实现"""
        # 获取事件信息
        result = await db.execute(
            select(Event).options(selectinload(Event.user)).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
        
        if not event:
            logger.error(f"Event {event_id} not found")
            return []
        
        # 获取通知模板
        template_key = f"event_status_change_{new_status.value}"
        result = await db.execute(
            select(NotificationTemplate).where(
                and_(
                    NotificationTemplate.template_key == template_key,
                    NotificationTemplate.is_active == True
                )
            )
        )
        templates = result.scalars().all()
        
        notifications = []
        
        # 为每个渠道创建通知
        for template in templates:
            # 渲染模板
            title = self._render_template(template.title_template, {
                "event_title": event.title,
                "event_type": event.event_type,
                "old_status": old_status.value,
                "new_status": new_status.value
            })
            
            content = self._render_template(template.content_template, {
                "event_title": event.title,
                "event_type": event.event_type,
                "event_description": event.description,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "location_address": event.location_address
            })
            
            # 确定接收者
            recipient = self._get_recipient_for_channel(event.user, template.channel)
            if not recipient:
                continue
            
            # 创建通知
            notification = await self._create_notification_impl(
                db=db,
                user_id=event.user_id,
                notification_type=NotificationType.EVENT_STATUS_CHANGE,
                channel=template.channel,
                title=title,
                content=content,
                recipient=recipient,
                event_id=event_id,
                priority=NotificationPriority.NORMAL,
                data={
                    "event_id": str(event_id),
                    "old_status": old_status.value,
                    "new_status": new_status.value
                }
            )
            
            notifications.append(notification)
        
        return notifications
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """渲染通知模板"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
    
    def _get_recipient_for_channel(self, user: User, channel: NotificationChannel) -> Optional[str]:
        """根据渠道获取接收者信息"""
        if channel == NotificationChannel.PUSH:
            return user.phone  # 使用手机号作为推送标识
        elif channel == NotificationChannel.SMS:
            return user.phone
        elif channel == NotificationChannel.EMAIL:
            # 假设用户模型中有email字段，如果没有则返回None
            return getattr(user, 'email', None)
        elif channel == NotificationChannel.IN_APP:
            return str(user.id)
        
        return None


# 创建全局通知服务实例
notification_service = NotificationService()