"""
通知相关的Pydantic模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.notification import (
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)


class NotificationBase(BaseModel):
    """通知基础模型"""
    notification_type: NotificationType
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., max_length=200)
    content: str
    data: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """创建通知请求模型"""
    user_id: UUID
    event_id: Optional[UUID] = None
    recipient: str


class NotificationResponse(NotificationBase):
    """通知响应模型"""
    id: UUID
    user_id: UUID
    event_id: Optional[UUID] = None
    recipient: str
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应模型"""
    notifications: List[NotificationResponse]
    total_count: int
    limit: int
    offset: int


class NotificationPreferenceBase(BaseModel):
    """通知偏好基础模型"""
    notification_type: NotificationType
    channel: NotificationChannel
    enabled: bool = True
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    frequency_limit: Optional[int] = Field(None, ge=1, le=100)


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """更新通知偏好请求模型"""
    pass


class NotificationPreferenceBatchUpdate(BaseModel):
    """批量更新通知偏好请求模型"""
    preferences: List[NotificationPreferenceUpdate]


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """通知偏好响应模型"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationTemplateBase(BaseModel):
    """通知模板基础模型"""
    template_key: str = Field(..., max_length=100)
    notification_type: NotificationType
    channel: NotificationChannel
    title_template: str = Field(..., max_length=200)
    content_template: str
    variables: Optional[Dict[str, Any]] = None
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    """创建通知模板请求模型"""
    pass


class NotificationTemplateUpdate(BaseModel):
    """更新通知模板请求模型"""
    title_template: Optional[str] = Field(None, max_length=200)
    content_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    """通知模板响应模型"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """通知统计响应模型"""
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    read_notifications: int
    failed_notifications: int
    pending_notifications: int
    stats_by_channel: Dict[str, Dict[str, int]]
    stats_by_type: Dict[str, Dict[str, int]]


class EventStatusChangeNotificationRequest(BaseModel):
    """事件状态变更通知请求模型"""
    event_id: UUID
    old_status: str
    new_status: str


class SystemAnnouncementRequest(BaseModel):
    """系统公告请求模型"""
    title: str = Field(..., max_length=200)
    content: str
    target_users: Optional[List[UUID]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = [NotificationChannel.PUSH, NotificationChannel.IN_APP]


class MaintenanceNoticeRequest(BaseModel):
    """维护通知请求模型"""
    maintenance_time: str
    duration: str
    maintenance_content: str
    advance_hours: int = Field(24, ge=1, le=168)  # 1小时到7天
    channels: List[NotificationChannel] = [NotificationChannel.PUSH, NotificationChannel.IN_APP]