"""
通知相关模型
包含通知记录、用户通知偏好和通知模板
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, 
    String, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base


class NotificationType(str, Enum):
    """通知类型枚举"""
    EVENT_STATUS_CHANGE = "event_status_change"    # 事件状态变更
    EVENT_ASSIGNED = "event_assigned"              # 事件分配
    EVENT_REMINDER = "event_reminder"              # 事件提醒
    SYSTEM_ANNOUNCEMENT = "system_announcement"    # 系统公告
    MAINTENANCE_NOTICE = "maintenance_notice"      # 维护通知


class NotificationChannel(str, Enum):
    """通知渠道枚举"""
    PUSH = "push"          # 推送通知
    SMS = "sms"            # 短信
    EMAIL = "email"        # 邮件
    IN_APP = "in_app"      # 应用内通知


class NotificationStatus(str, Enum):
    """通知状态枚举"""
    PENDING = "pending"      # 待发送
    SENT = "sent"           # 已发送
    DELIVERED = "delivered"  # 已送达
    READ = "read"           # 已读
    FAILED = "failed"       # 发送失败


class NotificationPriority(str, Enum):
    """通知优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """通知记录模型"""
    
    __tablename__ = "notifications"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外键
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True, index=True)
    
    # 通知基本信息
    notification_type = Column(
        SQLEnum(NotificationType), 
        nullable=False,
        index=True,
        comment="通知类型"
    )
    channel = Column(
        SQLEnum(NotificationChannel), 
        nullable=False,
        comment="通知渠道"
    )
    priority = Column(
        SQLEnum(NotificationPriority), 
        default=NotificationPriority.NORMAL,
        nullable=False,
        comment="优先级"
    )
    
    # 通知内容
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    data = Column(JSON, nullable=True, comment="附加数据")
    
    # 发送信息
    recipient = Column(String(200), nullable=False, comment="接收者(手机号/邮箱等)")
    status = Column(
        SQLEnum(NotificationStatus), 
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
        comment="发送状态"
    )
    
    # 发送结果
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="发送时间")
    delivered_at = Column(DateTime(timezone=True), nullable=True, comment="送达时间")
    read_at = Column(DateTime(timezone=True), nullable=True, comment="阅读时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 重试信息
    retry_count = Column(Integer, default=0, nullable=False, comment="重试次数")
    max_retries = Column(Integer, default=3, nullable=False, comment="最大重试次数")
    next_retry_at = Column(DateTime(timezone=True), nullable=True, comment="下次重试时间")
    
    # 外部服务信息
    external_id = Column(String(200), nullable=True, comment="外部服务消息ID")
    external_response = Column(JSON, nullable=True, comment="外部服务响应")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    # 关系
    user = relationship("User", back_populates="notifications")
    event = relationship("Event", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_id": str(self.event_id) if self.event_id else None,
            "notification_type": self.notification_type.value if self.notification_type else None,
            "channel": self.channel.value if self.channel else None,
            "priority": self.priority.value if self.priority else None,
            "title": self.title,
            "content": self.content,
            "data": self.data,
            "recipient": self.recipient,
            "status": self.status.value if self.status else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "external_id": self.external_id,
            "external_response": self.external_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserNotificationPreference(Base):
    """用户通知偏好模型"""
    
    __tablename__ = "user_notification_preferences"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外键
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 通知偏好设置
    notification_type = Column(
        SQLEnum(NotificationType), 
        nullable=False,
        comment="通知类型"
    )
    channel = Column(
        SQLEnum(NotificationChannel), 
        nullable=False,
        comment="通知渠道"
    )
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    
    # 时间限制
    quiet_hours_start = Column(String(5), nullable=True, comment="免打扰开始时间(HH:MM)")
    quiet_hours_end = Column(String(5), nullable=True, comment="免打扰结束时间(HH:MM)")
    
    # 频率限制
    frequency_limit = Column(Integer, nullable=True, comment="频率限制(每小时最大通知数)")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    # 关系
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self):
        return f"<UserNotificationPreference(user_id={self.user_id}, type={self.notification_type}, channel={self.channel})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "notification_type": self.notification_type.value if self.notification_type else None,
            "channel": self.channel.value if self.channel else None,
            "enabled": self.enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "frequency_limit": self.frequency_limit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationTemplate(Base):
    """通知模板模型"""
    
    __tablename__ = "notification_templates"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 模板信息
    template_key = Column(String(100), unique=True, nullable=False, index=True, comment="模板键")
    notification_type = Column(
        SQLEnum(NotificationType), 
        nullable=False,
        index=True,
        comment="通知类型"
    )
    channel = Column(
        SQLEnum(NotificationChannel), 
        nullable=False,
        comment="通知渠道"
    )
    
    # 模板内容
    title_template = Column(String(200), nullable=False, comment="标题模板")
    content_template = Column(Text, nullable=False, comment="内容模板")
    
    # 模板变量说明
    variables = Column(JSON, nullable=True, comment="模板变量说明")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<NotificationTemplate(key={self.template_key}, type={self.notification_type})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "template_key": self.template_key,
            "notification_type": self.notification_type.value if self.notification_type else None,
            "channel": self.channel.value if self.channel else None,
            "title_template": self.title_template,
            "content_template": self.content_template,
            "variables": self.variables,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }