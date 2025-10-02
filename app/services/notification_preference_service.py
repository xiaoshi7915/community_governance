"""
用户通知偏好管理服务
"""
import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.notification import (
    UserNotificationPreference, NotificationType, NotificationChannel
)


logger = logging.getLogger(__name__)


class NotificationPreferenceService:
    """通知偏好服务"""
    
    async def get_user_preferences(
        self,
        user_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> List[UserNotificationPreference]:
        """获取用户通知偏好"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._get_user_preferences_impl(db, user_id)
        else:
            return await self._get_user_preferences_impl(db, user_id)
    
    async def _get_user_preferences_impl(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[UserNotificationPreference]:
        """获取用户通知偏好的实现"""
        result = await db.execute(
            select(UserNotificationPreference)
            .where(UserNotificationPreference.user_id == user_id)
            .order_by(
                UserNotificationPreference.notification_type,
                UserNotificationPreference.channel
            )
        )
        return result.scalars().all()
    
    async def set_user_preference(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        enabled: bool,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        frequency_limit: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> UserNotificationPreference:
        """设置用户通知偏好"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._set_user_preference_impl(
                    db, user_id, notification_type, channel, enabled,
                    quiet_hours_start, quiet_hours_end, frequency_limit
                )
        else:
            return await self._set_user_preference_impl(
                db, user_id, notification_type, channel, enabled,
                quiet_hours_start, quiet_hours_end, frequency_limit
            )
    
    async def _set_user_preference_impl(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: NotificationType,
        channel: NotificationChannel,
        enabled: bool,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        frequency_limit: Optional[int] = None
    ) -> UserNotificationPreference:
        """设置用户通知偏好的实现"""
        # 查找现有偏好
        result = await db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.notification_type == notification_type,
                    UserNotificationPreference.channel == channel
                )
            )
        )
        preference = result.scalar_one_or_none()
        
        if preference:
            # 更新现有偏好
            preference.enabled = enabled
            preference.quiet_hours_start = quiet_hours_start
            preference.quiet_hours_end = quiet_hours_end
            preference.frequency_limit = frequency_limit
        else:
            # 创建新偏好
            preference = UserNotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                enabled=enabled,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
                frequency_limit=frequency_limit
            )
            db.add(preference)
        
        await db.commit()
        await db.refresh(preference)
        
        logger.info(f"Set notification preference for user {user_id}: {notification_type.value}/{channel.value} = {enabled}")
        return preference
    
    async def batch_set_preferences(
        self,
        user_id: UUID,
        preferences: List[Dict],
        db: Optional[AsyncSession] = None
    ) -> List[UserNotificationPreference]:
        """批量设置用户通知偏好"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._batch_set_preferences_impl(db, user_id, preferences)
        else:
            return await self._batch_set_preferences_impl(db, user_id, preferences)
    
    async def _batch_set_preferences_impl(
        self,
        db: AsyncSession,
        user_id: UUID,
        preferences: List[Dict]
    ) -> List[UserNotificationPreference]:
        """批量设置用户通知偏好的实现"""
        results = []
        
        for pref_data in preferences:
            preference = await self._set_user_preference_impl(
                db=db,
                user_id=user_id,
                notification_type=NotificationType(pref_data["notification_type"]),
                channel=NotificationChannel(pref_data["channel"]),
                enabled=pref_data["enabled"],
                quiet_hours_start=pref_data.get("quiet_hours_start"),
                quiet_hours_end=pref_data.get("quiet_hours_end"),
                frequency_limit=pref_data.get("frequency_limit")
            )
            results.append(preference)
        
        return results
    
    async def initialize_default_preferences(
        self,
        user_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> List[UserNotificationPreference]:
        """为新用户初始化默认通知偏好"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._initialize_default_preferences_impl(db, user_id)
        else:
            return await self._initialize_default_preferences_impl(db, user_id)
    
    async def _initialize_default_preferences_impl(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[UserNotificationPreference]:
        """为新用户初始化默认通知偏好的实现"""
        # 检查是否已有偏好设置
        result = await db.execute(
            select(UserNotificationPreference).where(
                UserNotificationPreference.user_id == user_id
            ).limit(1)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"User {user_id} already has notification preferences")
            return await self._get_user_preferences_impl(db, user_id)
        
        # 默认偏好配置
        default_preferences = [
            # 事件状态变更通知 - 默认启用推送和应用内通知
            {
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.PUSH,
                "enabled": True,
                "frequency_limit": 10  # 每小时最多10条
            },
            {
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.IN_APP,
                "enabled": True,
                "frequency_limit": None
            },
            {
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.SMS,
                "enabled": False,  # 短信默认关闭
                "frequency_limit": 3  # 每小时最多3条
            },
            {
                "notification_type": NotificationType.EVENT_STATUS_CHANGE,
                "channel": NotificationChannel.EMAIL,
                "enabled": False,  # 邮件默认关闭
                "frequency_limit": 5  # 每小时最多5条
            },
            
            # 事件分配通知
            {
                "notification_type": NotificationType.EVENT_ASSIGNED,
                "channel": NotificationChannel.PUSH,
                "enabled": True,
                "frequency_limit": 5
            },
            {
                "notification_type": NotificationType.EVENT_ASSIGNED,
                "channel": NotificationChannel.IN_APP,
                "enabled": True,
                "frequency_limit": None
            },
            {
                "notification_type": NotificationType.EVENT_ASSIGNED,
                "channel": NotificationChannel.SMS,
                "enabled": False,
                "frequency_limit": 2
            },
            {
                "notification_type": NotificationType.EVENT_ASSIGNED,
                "channel": NotificationChannel.EMAIL,
                "enabled": False,
                "frequency_limit": 3
            },
            
            # 事件提醒
            {
                "notification_type": NotificationType.EVENT_REMINDER,
                "channel": NotificationChannel.PUSH,
                "enabled": True,
                "frequency_limit": 5
            },
            {
                "notification_type": NotificationType.EVENT_REMINDER,
                "channel": NotificationChannel.IN_APP,
                "enabled": True,
                "frequency_limit": None
            },
            {
                "notification_type": NotificationType.EVENT_REMINDER,
                "channel": NotificationChannel.SMS,
                "enabled": False,
                "frequency_limit": 2
            },
            {
                "notification_type": NotificationType.EVENT_REMINDER,
                "channel": NotificationChannel.EMAIL,
                "enabled": False,
                "frequency_limit": 3
            },
            
            # 系统公告 - 重要通知，默认启用所有渠道
            {
                "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT,
                "channel": NotificationChannel.PUSH,
                "enabled": True,
                "frequency_limit": 3
            },
            {
                "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT,
                "channel": NotificationChannel.IN_APP,
                "enabled": True,
                "frequency_limit": None
            },
            {
                "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT,
                "channel": NotificationChannel.SMS,
                "enabled": True,
                "frequency_limit": 1
            },
            {
                "notification_type": NotificationType.SYSTEM_ANNOUNCEMENT,
                "channel": NotificationChannel.EMAIL,
                "enabled": True,
                "frequency_limit": 2
            },
            
            # 维护通知
            {
                "notification_type": NotificationType.MAINTENANCE_NOTICE,
                "channel": NotificationChannel.PUSH,
                "enabled": True,
                "frequency_limit": 2
            },
            {
                "notification_type": NotificationType.MAINTENANCE_NOTICE,
                "channel": NotificationChannel.IN_APP,
                "enabled": True,
                "frequency_limit": None
            },
            {
                "notification_type": NotificationType.MAINTENANCE_NOTICE,
                "channel": NotificationChannel.SMS,
                "enabled": False,
                "frequency_limit": 1
            },
            {
                "notification_type": NotificationType.MAINTENANCE_NOTICE,
                "channel": NotificationChannel.EMAIL,
                "enabled": True,
                "frequency_limit": 2
            },
        ]
        
        preferences = []
        for pref_data in default_preferences:
            preference = UserNotificationPreference(
                user_id=user_id,
                notification_type=pref_data["notification_type"],
                channel=pref_data["channel"],
                enabled=pref_data["enabled"],
                quiet_hours_start=pref_data.get("quiet_hours_start"),
                quiet_hours_end=pref_data.get("quiet_hours_end"),
                frequency_limit=pref_data.get("frequency_limit")
            )
            db.add(preference)
            preferences.append(preference)
        
        await db.commit()
        
        logger.info(f"Initialized default notification preferences for user {user_id}")
        return preferences
    
    async def delete_user_preferences(
        self,
        user_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> int:
        """删除用户所有通知偏好"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._delete_user_preferences_impl(db, user_id)
        else:
            return await self._delete_user_preferences_impl(db, user_id)
    
    async def _delete_user_preferences_impl(self, db: AsyncSession, user_id: UUID) -> int:
        """删除用户所有通知偏好的实现"""
        result = await db.execute(
            delete(UserNotificationPreference).where(
                UserNotificationPreference.user_id == user_id
            )
        )
        
        await db.commit()
        deleted_count = result.rowcount
        
        logger.info(f"Deleted {deleted_count} notification preferences for user {user_id}")
        return deleted_count
    
    async def get_preference_summary(
        self,
        user_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Dict[str, bool]]:
        """获取用户通知偏好摘要"""
        if db is None:
            async with AsyncSessionLocal() as db:
                return await self._get_preference_summary_impl(db, user_id)
        else:
            return await self._get_preference_summary_impl(db, user_id)
    
    async def _get_preference_summary_impl(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, Dict[str, bool]]:
        """获取用户通知偏好摘要的实现"""
        preferences = await self._get_user_preferences_impl(db, user_id)
        
        summary = {}
        for pref in preferences:
            if pref.notification_type.value not in summary:
                summary[pref.notification_type.value] = {}
            
            summary[pref.notification_type.value][pref.channel.value] = pref.enabled
        
        return summary


# 创建全局通知偏好服务实例
notification_preference_service = NotificationPreferenceService()