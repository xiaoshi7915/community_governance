"""
事件服务通知集成
为现有的事件服务添加通知触发功能
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import EventStatus
from app.services.event_service import event_service
from app.services.notification_trigger_service import notification_trigger_service


logger = logging.getLogger(__name__)


class EventNotificationIntegration:
    """事件通知集成类"""
    
    def __init__(self):
        self.event_service = event_service
        self.notification_trigger_service = notification_trigger_service
    
    async def update_event_status_with_notifications(
        self,
        event_id: UUID,
        new_status: EventStatus,
        operator_id: UUID,
        description: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        更新事件状态并触发通知
        
        Args:
            event_id: 事件ID
            new_status: 新状态
            operator_id: 操作者ID
            description: 状态变更描述
            db: 数据库会话
            
        Returns:
            Dict: 更新结果，包含通知信息
        """
        # 首先获取当前事件状态
        event_detail = await self.event_service.get_event_detail(event_id, db=db)
        if not event_detail["success"]:
            return event_detail
        
        old_status = EventStatus(event_detail["event"]["status"])
        
        # 更新事件状态
        update_result = await self.event_service.update_event_status(
            event_id=event_id,
            new_status=new_status,
            operator_id=operator_id,
            description=description,
            db=db
        )
        
        if not update_result["success"]:
            return update_result
        
        # 触发通知
        try:
            notification_ids = await self.notification_trigger_service.trigger_event_status_change_notifications(
                event_id=event_id,
                old_status=old_status,
                new_status=new_status,
                db=db
            )
            
            # 添加通知信息到结果中
            update_result["notifications"] = {
                "triggered_count": len(notification_ids),
                "notification_ids": notification_ids
            }
            
            logger.info(f"Event status updated with notifications: {event_id}, notifications: {len(notification_ids)}")
        
        except Exception as e:
            logger.error(f"Failed to trigger notifications for event {event_id}: {e}")
            # 即使通知失败，也不影响状态更新的成功
            update_result["notifications"] = {
                "triggered_count": 0,
                "notification_ids": [],
                "error": str(e)
            }
        
        return update_result


# 创建全局事件通知集成实例
event_notification_integration = EventNotificationIntegration()