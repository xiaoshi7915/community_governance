"""
数据模型包
"""
from sqlalchemy.ext.declarative import declarative_base

# 创建SQLAlchemy基类
Base = declarative_base()

# 导入所有模型以确保它们被注册
from .user import User
from .event import Event, EventTimeline, EventMedia, EventPriority, EventStatus, MediaType
from .community import Community
from .notification import (
    Notification, UserNotificationPreference, NotificationTemplate,
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)

# 导出所有模型和枚举
__all__ = [
    "Base",
    "User", 
    "Event", 
    "EventTimeline", 
    "EventMedia",
    "EventPriority",
    "EventStatus", 
    "MediaType",
    "Community",
    "Notification",
    "UserNotificationPreference", 
    "NotificationTemplate",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationPriority"
]