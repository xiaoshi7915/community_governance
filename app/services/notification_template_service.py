"""
通知模板管理服务
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import and_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.notification import (
    NotificationTemplate, NotificationType, NotificationChannel
)


logger = logging.getLogger(__name__)


class NotificationTemplateService:
    """通知模板服务"""
    
    async def create_template(
        self,
        template_key: str,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title_template: str,
        content_template: str,
        variables: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        db: Optional[AsyncSession] = None
    ) -> NotificationTemplate:
        """创建通知模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._create_template_impl(
                    db, template_key, notification_type, channel,
                    title_template, content_template, variables, is_active
                )
        else:
            return await self._create_template_impl(
                db, template_key, notification_type, channel,
                title_template, content_template, variables, is_active
            )
    
    async def _create_template_impl(
        self,
        db: AsyncSession,
        template_key: str,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title_template: str,
        content_template: str,
        variables: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> NotificationTemplate:
        """创建通知模板的实现"""
        template = NotificationTemplate(
            template_key=template_key,
            notification_type=notification_type,
            channel=channel,
            title_template=title_template,
            content_template=content_template,
            variables=variables,
            is_active=is_active
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Created notification template: {template_key}")
        return template
    
    async def get_template(
        self,
        template_key: str,
        db: Optional[AsyncSession] = None
    ) -> Optional[NotificationTemplate]:
        """获取通知模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._get_template_impl(db, template_key)
        else:
            return await self._get_template_impl(db, template_key)
    
    async def _get_template_impl(
        self,
        db: AsyncSession,
        template_key: str
    ) -> Optional[NotificationTemplate]:
        """获取通知模板的实现"""
        result = await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.template_key == template_key
            )
        )
        return result.scalar_one_or_none()
    
    async def get_templates_by_type_and_channel(
        self,
        notification_type: NotificationType,
        channel: Optional[NotificationChannel] = None,
        active_only: bool = True,
        db: Optional[AsyncSession] = None
    ) -> List[NotificationTemplate]:
        """根据类型和渠道获取模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._get_templates_by_type_and_channel_impl(
                    db, notification_type, channel, active_only
                )
        else:
            return await self._get_templates_by_type_and_channel_impl(
                db, notification_type, channel, active_only
            )
    
    async def _get_templates_by_type_and_channel_impl(
        self,
        db: AsyncSession,
        notification_type: NotificationType,
        channel: Optional[NotificationChannel] = None,
        active_only: bool = True
    ) -> List[NotificationTemplate]:
        """根据类型和渠道获取模板的实现"""
        query = select(NotificationTemplate).where(
            NotificationTemplate.notification_type == notification_type
        )
        
        if channel:
            query = query.where(NotificationTemplate.channel == channel)
        
        if active_only:
            query = query.where(NotificationTemplate.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_template(
        self,
        template_key: str,
        title_template: Optional[str] = None,
        content_template: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        db: Optional[AsyncSession] = None
    ) -> Optional[NotificationTemplate]:
        """更新通知模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._update_template_impl(
                    db, template_key, title_template, content_template, variables, is_active
                )
        else:
            return await self._update_template_impl(
                db, template_key, title_template, content_template, variables, is_active
            )
    
    async def _update_template_impl(
        self,
        db: AsyncSession,
        template_key: str,
        title_template: Optional[str] = None,
        content_template: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[NotificationTemplate]:
        """更新通知模板的实现"""
        result = await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.template_key == template_key
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        if title_template is not None:
            template.title_template = title_template
        
        if content_template is not None:
            template.content_template = content_template
        
        if variables is not None:
            template.variables = variables
        
        if is_active is not None:
            template.is_active = is_active
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Updated notification template: {template_key}")
        return template
    
    async def delete_template(
        self,
        template_key: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """删除通知模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._delete_template_impl(db, template_key)
        else:
            return await self._delete_template_impl(db, template_key)
    
    async def _delete_template_impl(self, db: AsyncSession, template_key: str) -> bool:
        """删除通知模板的实现"""
        result = await db.execute(
            delete(NotificationTemplate).where(
                NotificationTemplate.template_key == template_key
            )
        )
        
        await db.commit()
        deleted = result.rowcount > 0
        
        if deleted:
            logger.info(f"Deleted notification template: {template_key}")
        
        return deleted
    
    async def initialize_default_templates(self, db: Optional[AsyncSession] = None) -> List[NotificationTemplate]:
        """初始化默认通知模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._initialize_default_templates_impl(db)
        else:
            return await self._initialize_default_templates_impl(db)
    
    async def _initialize_default_templates_impl(self, db: AsyncSession) -> List[NotificationTemplate]:
        """初始化默认通知模板的实现"""
        # 检查是否已有模板
        result = await db.execute(select(NotificationTemplate).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Default notification templates already exist")
            return []
        
        # 默认模板配置
        default_templates = [
            # 事件状态变更 - 推送通知
            {
                "template_key": "event_status_change_processing_push",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.PUSH,
                "title_template": "事件处理中",
                "content_template": "您上报的事件「{event_title}」正在处理中，请耐心等待。",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型",
                    "old_status": "原状态",
                    "new_status": "新状态"
                }
            },
            {
                "template_key": "event_status_change_completed_push",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.PUSH,
                "title_template": "事件已完成",
                "content_template": "您上报的事件「{event_title}」已处理完成，感谢您的参与！",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型",
                    "old_status": "原状态",
                    "new_status": "新状态"
                }
            },
            {
                "template_key": "event_status_change_rejected_push",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.PUSH,
                "title_template": "事件已拒绝",
                "content_template": "很抱歉，您上报的事件「{event_title}」未能通过审核。",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型",
                    "old_status": "原状态",
                    "new_status": "新状态"
                }
            },
            
            # 事件状态变更 - 应用内通知
            {
                "template_key": "event_status_change_processing_in_app",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.IN_APP,
                "title_template": "事件状态更新",
                "content_template": "您上报的{event_type}事件「{event_title}」状态已从「{old_status}」更新为「{new_status}」。地址：{location_address}",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型",
                    "event_description": "事件描述",
                    "old_status": "原状态",
                    "new_status": "新状态",
                    "location_address": "事件地址"
                }
            },
            {
                "template_key": "event_status_change_completed_in_app",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.IN_APP,
                "title_template": "事件处理完成",
                "content_template": "您上报的{event_type}事件「{event_title}」已处理完成。感谢您对城市治理的贡献！地址：{location_address}",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型",
                    "event_description": "事件描述",
                    "old_status": "原状态",
                    "new_status": "新状态",
                    "location_address": "事件地址"
                }
            },
            {
                "template_key": "event_status_change_rejected_in_app",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.IN_APP,
                "title_template": "事件审核未通过",
                "content_template": "很抱歉，您上报的{event_type}事件「{event_title}」未能通过审核。如有疑问，请联系客服。地址：{location_address}",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型",
                    "event_description": "事件描述",
                    "old_status": "原状态",
                    "new_status": "新状态",
                    "location_address": "事件地址"
                }
            },
            
            # 事件状态变更 - 短信通知
            {
                "template_key": "event_status_change_completed_sms",
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.SMS,
                "title_template": "事件处理完成通知",
                "content_template": "【城市治理】您上报的事件「{event_title}」已处理完成，感谢您的参与！",
                "variables": {
                    "event_title": "事件标题",
                    "event_type": "事件类型"
                }
            },
            
            # 系统公告 - 推送通知
            {
                "template_key": "system_announcement_push",
                "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT,
                "channel": NotificationChannel.PUSH,
                "title_template": "系统公告",
                "content_template": "{announcement_content}",
                "variables": {
                    "announcement_title": "公告标题",
                    "announcement_content": "公告内容"
                }
            },
            
            # 系统公告 - 应用内通知
            {
                "template_key": "system_announcement_in_app",
                "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT,
                "channel": NotificationChannel.IN_APP,
                "title_template": "{announcement_title}",
                "content_template": "{announcement_content}",
                "variables": {
                    "announcement_title": "公告标题",
                    "announcement_content": "公告内容"
                }
            },
            
            # 维护通知 - 推送通知
            {
                "template_key": "maintenance_notice_push",
                "notification_type": NotificationType.MAINTENANCE_NOTICE,
                "channel": NotificationChannel.PUSH,
                "title_template": "系统维护通知",
                "content_template": "系统将于{maintenance_time}进行维护，预计耗时{duration}，请合理安排使用时间。",
                "variables": {
                    "maintenance_time": "维护时间",
                    "duration": "维护时长",
                    "maintenance_content": "维护内容"
                }
            },
            
            # 维护通知 - 应用内通知
            {
                "template_key": "maintenance_notice_in_app",
                "notification_type": NotificationType.MAINTENANCE_NOTICE,
                "channel": NotificationChannel.IN_APP,
                "title_template": "系统维护通知",
                "content_template": "系统将于{maintenance_time}进行维护，维护内容：{maintenance_content}，预计耗时{duration}。维护期间可能影响部分功能使用，请您谅解。",
                "variables": {
                    "maintenance_time": "维护时间",
                    "duration": "维护时长",
                    "maintenance_content": "维护内容"
                }
            }
        ]
        
        templates = []
        for template_data in default_templates:
            template = NotificationTemplate(
                template_key=template_data["template_key"],
                notification_type=template_data["notification_type"],
                channel=template_data["channel"],
                title_template=template_data["title_template"],
                content_template=template_data["content_template"],
                variables=template_data["variables"],
                is_active=True
            )
            db.add(template)
            templates.append(template)
        
        await db.commit()
        
        logger.info(f"Initialized {len(templates)} default notification templates")
        return templates
    
    async def get_all_templates(
        self,
        active_only: bool = True,
        db: Optional[AsyncSession] = None
    ) -> List[NotificationTemplate]:
        """获取所有通知模板"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._get_all_templates_impl(db, active_only)
        else:
            return await self._get_all_templates_impl(db, active_only)
    
    async def _get_all_templates_impl(
        self,
        db: AsyncSession,
        active_only: bool = True
    ) -> List[NotificationTemplate]:
        """获取所有通知模板的实现"""
        query = select(NotificationTemplate)
        
        if active_only:
            query = query.where(NotificationTemplate.is_active == True)
        
        query = query.order_by(
            NotificationTemplate.notification_type,
            NotificationTemplate.channel,
            NotificationTemplate.template_key
        )
        
        result = await db.execute(query)
        return result.scalars().all()


# 创建全局通知模板服务实例
notification_template_service = NotificationTemplateService()