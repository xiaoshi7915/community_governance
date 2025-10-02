"""
通知相关API端点
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.core.response import create_response, response_formatter
from app.models.user import User
from app.models.notification import NotificationChannel, NotificationStatus
from app.services.notification_service import notification_service
from app.services.notification_preference_service import notification_preference_service
from app.schemas.notification import (
    NotificationResponse, NotificationListResponse,
    NotificationPreferenceResponse, NotificationPreferenceUpdate,
    NotificationPreferenceBatchUpdate
)


router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def get_user_notifications(
    channel: Optional[NotificationChannel] = Query(None, description="通知渠道过滤"),
    status: Optional[NotificationStatus] = Query(None, description="通知状态过滤"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户通知列表"""
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            channel=channel,
            status=status,
            limit=limit,
            offset=offset,
            db=db
        )
        
        return create_response(
            data={
                "notifications": [notification.to_dict() for notification in notifications],
                "total_count": len(notifications),
                "limit": limit,
                "offset": offset
            },
            message="获取通知列表成功"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"获取通知列表失败: {str(e)}")


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记通知为已读"""
    try:
        success = await notification_service.mark_notification_as_read(
            notification_id=notification_id,
            db=db
        )
        
        if success:
            return create_response(
                data={"notification_id": str(notification_id)},
                message="通知已标记为已读"
            )
        else:
            return response_formatter.error(message="通知不存在或已读")
    
    except Exception as e:
        return response_formatter.error(message=f"标记通知失败: {str(e)}")


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户通知偏好"""
    try:
        preferences = await notification_preference_service.get_user_preferences(
            user_id=current_user.id,
            db=db
        )
        
        return create_response(
            data=[preference.to_dict() for preference in preferences],
            message="获取通知偏好成功"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"获取通知偏好失败: {str(e)}")


@router.put("/preferences")
async def update_notification_preferences(
    preferences_update: NotificationPreferenceBatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新用户通知偏好"""
    try:
        preferences = await notification_preference_service.batch_set_preferences(
            user_id=current_user.id,
            preferences=[pref.dict() for pref in preferences_update.preferences],
            db=db
        )
        
        return create_response(
            data=[preference.to_dict() for preference in preferences],
            message="通知偏好更新成功"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"更新通知偏好失败: {str(e)}")


@router.get("/preferences/summary")
async def get_notification_preferences_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户通知偏好摘要"""
    try:
        summary = await notification_preference_service.get_preference_summary(
            user_id=current_user.id,
            db=db
        )
        
        return create_response(
            data=summary,
            message="获取通知偏好摘要成功"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"获取通知偏好摘要失败: {str(e)}")


@router.post("/preferences/initialize")
async def initialize_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """初始化用户默认通知偏好"""
    try:
        preferences = await notification_preference_service.initialize_default_preferences(
            user_id=current_user.id,
            db=db
        )
        
        return create_response(
            data=[preference.to_dict() for preference in preferences],
            message="通知偏好初始化成功"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"初始化通知偏好失败: {str(e)}")


@router.get("/unread-count")
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取未读通知数量"""
    try:
        unread_notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            status=NotificationStatus.SENT,  # 已发送但未读
            limit=1000,  # 获取足够多的数量来统计
            offset=0,
            db=db
        )
        
        # 按渠道统计未读数量
        unread_count_by_channel = {}
        total_unread = 0
        
        for notification in unread_notifications:
            channel = notification.channel.value
            unread_count_by_channel[channel] = unread_count_by_channel.get(channel, 0) + 1
            total_unread += 1
        
        return create_response(
            data={
                "total_unread": total_unread,
                "unread_by_channel": unread_count_by_channel
            },
            message="获取未读通知数量成功"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"获取未读通知数量失败: {str(e)}")


@router.post("/retry-failed")
async def retry_failed_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """重试失败的通知（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="需要管理员权限")
        
        retry_count = await notification_service.retry_failed_notifications(db=db)
        
        return create_response(
            data={"retry_count": retry_count},
            message=f"重试了 {retry_count} 个失败的通知"
        )
    
    except Exception as e:
        return response_formatter.error(message=f"重试失败通知失败: {str(e)}")