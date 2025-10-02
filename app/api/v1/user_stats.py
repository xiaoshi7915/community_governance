"""
用户统计API端点
提供用户相关的统计数据
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.response import create_response
from app.core.auth_middleware import get_current_active_user
from app.models.user import User
from app.models.event import Event

router = APIRouter(prefix="/events", tags=["用户统计"])


@router.get(
    "/user/stats",
    summary="获取用户统计信息",
    description="获取当前用户的事件统计数据"
)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户统计信息
    
    返回用户的事件统计数据，包括：
    - 总事件数
    - 各状态事件数
    - 各类型事件数
    """
    try:
        # 获取用户总事件数
        total_events_result = await db.execute(
            select(func.count(Event.id)).where(Event.user_id == current_user.id)
        )
        total_events = total_events_result.scalar() or 0
        
        # 获取各状态事件数
        status_stats_result = await db.execute(
            select(Event.status, func.count(Event.id))
            .where(Event.user_id == current_user.id)
            .group_by(Event.status)
        )
        status_stats = {row[0]: row[1] for row in status_stats_result.fetchall()}
        
        # 获取各类型事件数
        type_stats_result = await db.execute(
            select(Event.event_type, func.count(Event.id))
            .where(Event.user_id == current_user.id)
            .group_by(Event.event_type)
        )
        type_stats = {row[0]: row[1] for row in type_stats_result.fetchall()}
        
        # 获取最近事件
        recent_events_result = await db.execute(
            select(Event)
            .where(Event.user_id == current_user.id)
            .order_by(Event.created_at.desc())
            .limit(5)
        )
        recent_events = recent_events_result.scalars().all()
        
        stats_data = {
            "total_events": total_events,
            "status_stats": {
                "pending": status_stats.get("pending", 0),
                "processing": status_stats.get("processing", 0),
                "resolved": status_stats.get("resolved", 0),
                "closed": status_stats.get("closed", 0)
            },
            "type_stats": type_stats,
            "recent_events": [
                {
                    "id": str(event.id),
                    "title": event.title,
                    "status": event.status,
                    "event_type": event.event_type,
                    "created_at": event.created_at.isoformat() if event.created_at else None
                }
                for event in recent_events
            ]
        }
        
        return create_response(
            data=stats_data,
            message="用户统计信息获取成功"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计信息失败: {str(e)}"
        )