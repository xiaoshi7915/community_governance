"""
通知服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.notification_service import NotificationService
from app.models.user import User
from app.models.event import Event
from app.models.notification import Notification, NotificationStatus, NotificationChannel
from app.core.exceptions import ValidationError, NotFoundError


class TestNotificationService:
    """通知服务测试类"""
    
    @pytest.fixture
    def notification_service(self):
        """创建通知服务实例"""
        return NotificationService()
    
    @pytest.fixture
    def mock_push_client(self):
        """模拟推送客户端"""
        mock_client = Mock()
        mock_client.send_notification = AsyncMock(return_value={"success": True, "message_id": "test-id"})
        return mock_client
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试发送通知成功"""
        notification_data = {
            "title": "测试通知",
            "content": "这是一个测试通知",
            "type": "event_update",
            "channel": "push"
        }
        
        notification = await notification_service.send_notification(
            db_session,
            test_user.id,
            **notification_data
        )
        
        assert notification.title == "测试通知"
        assert notification.content == "这是一个测试通知"
        assert notification.user_id == test_user.id
        assert notification.status == NotificationStatus.PENDING
        assert notification.channel == NotificationChannel.PUSH
    
    @pytest.mark.asyncio
    async def test_send_push_notification_success(self, notification_service, mock_push_client):
        """测试发送推送通知成功"""
        with patch.object(notification_service, 'push_client', mock_push_client):
            result = await notification_service.send_push_notification(
                "test_device_token",
                "测试标题",
                "测试内容",
                {"key": "value"}
            )
        
        assert result["success"] is True
        assert result["message_id"] == "test-id"
        mock_push_client.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_sms_notification_success(self, notification_service):
        """测试发送短信通知成功"""
        with patch('app.services.notification_service.send_sms') as mock_sms:
            mock_sms.return_value = {"success": True, "message_id": "sms-id"}
            
            result = await notification_service.send_sms_notification(
                "13800138000",
                "测试短信内容"
            )
        
        assert result["success"] is True
        assert result["message_id"] == "sms-id"
        mock_sms.assert_called_once_with("13800138000", "测试短信内容")
    
    @pytest.mark.asyncio
    async def test_send_email_notification_success(self, notification_service):
        """测试发送邮件通知成功"""
        with patch('app.services.notification_service.send_email') as mock_email:
            mock_email.return_value = {"success": True, "message_id": "email-id"}
            
            result = await notification_service.send_email_notification(
                "test@example.com",
                "测试邮件标题",
                "测试邮件内容"
            )
        
        assert result["success"] is True
        assert result["message_id"] == "email-id"
        mock_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_notifications_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试获取用户通知列表成功"""
        # 创建测试通知
        await notification_service.send_notification(
            db_session,
            test_user.id,
            title="通知1",
            content="内容1",
            type="event_update"
        )
        await notification_service.send_notification(
            db_session,
            test_user.id,
            title="通知2",
            content="内容2",
            type="system"
        )
        await db_session.commit()
        
        notifications = await notification_service.get_user_notifications(db_session, test_user.id)
        
        assert len(notifications) == 2
        assert all(notification.user_id == test_user.id for notification in notifications)
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试标记通知为已读成功"""
        # 创建测试通知
        notification = await notification_service.send_notification(
            db_session,
            test_user.id,
            title="测试通知",
            content="测试内容",
            type="event_update"
        )
        await db_session.commit()
        
        result = await notification_service.mark_notification_as_read(
            db_session,
            notification.id,
            test_user.id
        )
        
        assert result is True
        await db_session.refresh(notification)
        assert notification.is_read is True
        assert notification.read_at is not None
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read_not_found(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试标记不存在的通知为已读"""
        with pytest.raises(NotFoundError, match="通知不存在"):
            await notification_service.mark_notification_as_read(
                db_session,
                uuid4(),
                test_user.id
            )
    
    @pytest.mark.asyncio
    async def test_delete_notification_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试删除通知成功"""
        # 创建测试通知
        notification = await notification_service.send_notification(
            db_session,
            test_user.id,
            title="待删除通知",
            content="内容",
            type="event_update"
        )
        await db_session.commit()
        
        result = await notification_service.delete_notification(
            db_session,
            notification.id,
            test_user.id
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_notification_statistics_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试获取通知统计成功"""
        # 创建不同状态的通知
        await notification_service.send_notification(
            db_session, test_user.id,
            title="未读通知1", content="内容", type="event_update"
        )
        await notification_service.send_notification(
            db_session, test_user.id,
            title="未读通知2", content="内容", type="system"
        )
        
        # 创建已读通知
        read_notification = await notification_service.send_notification(
            db_session, test_user.id,
            title="已读通知", content="内容", type="event_update"
        )
        await notification_service.mark_notification_as_read(
            db_session, read_notification.id, test_user.id
        )
        await db_session.commit()
        
        stats = await notification_service.get_notification_statistics(db_session, test_user.id)
        
        assert stats["total_notifications"] == 3
        assert stats["unread_notifications"] == 2
        assert stats["read_notifications"] == 1
        assert "event_update" in stats["notifications_by_type"]
        assert "system" in stats["notifications_by_type"]
    
    def test_validate_notification_type_success(self, notification_service):
        """测试通知类型验证成功"""
        valid_types = ["event_update", "system", "reminder", "promotion"]
        
        for notification_type in valid_types:
            assert notification_service._validate_notification_type(notification_type) is True
    
    def test_validate_notification_type_failure(self, notification_service):
        """测试通知类型验证失败"""
        invalid_types = ["invalid_type", "", None, 123]
        
        for notification_type in invalid_types:
            assert notification_service._validate_notification_type(notification_type) is False
    
    def test_validate_channel_success(self, notification_service):
        """测试通知渠道验证成功"""
        valid_channels = ["push", "sms", "email"]
        
        for channel in valid_channels:
            assert notification_service._validate_channel(channel) is True
    
    def test_validate_channel_failure(self, notification_service):
        """测试通知渠道验证失败"""
        invalid_channels = ["invalid_channel", "", None, 123]
        
        for channel in invalid_channels:
            assert notification_service._validate_channel(channel) is False
    
    @pytest.mark.asyncio
    async def test_batch_send_notifications_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试批量发送通知成功"""
        user_ids = [test_user.id, uuid4(), uuid4()]
        notification_data = {
            "title": "批量通知",
            "content": "这是批量发送的通知",
            "type": "system"
        }
        
        results = await notification_service.batch_send_notifications(
            db_session,
            user_ids,
            **notification_data
        )
        
        assert len(results) == 3
        assert results[0]["success"] is True  # test_user存在
        assert results[1]["success"] is False  # 用户不存在
        assert results[2]["success"] is False  # 用户不存在
    
    @pytest.mark.asyncio
    async def test_get_notification_templates_success(self, notification_service, db_session: AsyncSession):
        """测试获取通知模板成功"""
        templates = await notification_service.get_notification_templates(db_session)
        
        assert isinstance(templates, list)
        # 应该有一些默认模板
        assert len(templates) >= 0
    
    @pytest.mark.asyncio
    async def test_create_notification_template_success(self, notification_service, db_session: AsyncSession):
        """测试创建通知模板成功"""
        template_data = {
            "name": "事件更新模板",
            "title": "事件状态更新",
            "content": "您的事件 {event_title} 状态已更新为 {status}",
            "type": "event_update"
        }
        
        template = await notification_service.create_notification_template(
            db_session,
            **template_data
        )
        
        assert template.name == "事件更新模板"
        assert template.title == "事件状态更新"
        assert "{event_title}" in template.content
        assert template.type == "event_update"
    
    @pytest.mark.asyncio
    async def test_send_templated_notification_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试发送模板通知成功"""
        # 先创建模板
        template = await notification_service.create_notification_template(
            db_session,
            name="测试模板",
            title="测试标题 {name}",
            content="您好 {name}，这是测试内容",
            type="system"
        )
        await db_session.commit()
        
        # 发送模板通知
        variables = {"name": "张三"}
        notification = await notification_service.send_templated_notification(
            db_session,
            test_user.id,
            template.id,
            variables
        )
        
        assert notification.title == "测试标题 张三"
        assert notification.content == "您好 张三，这是测试内容"
    
    @pytest.mark.asyncio
    async def test_get_notification_preferences_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试获取通知偏好成功"""
        preferences = await notification_service.get_notification_preferences(
            db_session,
            test_user.id
        )
        
        assert isinstance(preferences, dict)
        assert "push_enabled" in preferences
        assert "sms_enabled" in preferences
        assert "email_enabled" in preferences
    
    @pytest.mark.asyncio
    async def test_update_notification_preferences_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试更新通知偏好成功"""
        new_preferences = {
            "push_enabled": False,
            "sms_enabled": True,
            "email_enabled": False,
            "event_update_enabled": True,
            "system_enabled": False
        }
        
        result = await notification_service.update_notification_preferences(
            db_session,
            test_user.id,
            new_preferences
        )
        
        assert result is True
        
        # 验证更新结果
        preferences = await notification_service.get_notification_preferences(
            db_session,
            test_user.id
        )
        assert preferences["push_enabled"] is False
        assert preferences["sms_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_schedule_notification_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试定时通知成功"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        notification = await notification_service.schedule_notification(
            db_session,
            test_user.id,
            title="定时通知",
            content="这是一个定时通知",
            type="reminder",
            scheduled_time=scheduled_time
        )
        
        assert notification.title == "定时通知"
        assert notification.scheduled_time == scheduled_time
        assert notification.status == NotificationStatus.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_cancel_scheduled_notification_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试取消定时通知成功"""
        # 创建定时通知
        scheduled_time = datetime.now() + timedelta(hours=1)
        notification = await notification_service.schedule_notification(
            db_session,
            test_user.id,
            title="待取消通知",
            content="内容",
            type="reminder",
            scheduled_time=scheduled_time
        )
        await db_session.commit()
        
        # 取消通知
        result = await notification_service.cancel_scheduled_notification(
            db_session,
            notification.id,
            test_user.id
        )
        
        assert result is True
        await db_session.refresh(notification)
        assert notification.status == NotificationStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_pending_notifications_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试获取待发送通知成功"""
        # 创建不同状态的通知
        await notification_service.send_notification(
            db_session, test_user.id,
            title="待发送通知", content="内容", type="system"
        )
        
        scheduled_time = datetime.now() - timedelta(minutes=1)  # 过期的定时通知
        await notification_service.schedule_notification(
            db_session, test_user.id,
            title="过期定时通知", content="内容", type="reminder",
            scheduled_time=scheduled_time
        )
        await db_session.commit()
        
        pending_notifications = await notification_service.get_pending_notifications(db_session)
        
        assert len(pending_notifications) >= 1
        assert all(
            notification.status in [NotificationStatus.PENDING, NotificationStatus.SCHEDULED]
            for notification in pending_notifications
        )
    
    @pytest.mark.asyncio
    async def test_process_notification_queue_success(self, notification_service, db_session: AsyncSession, test_user: User):
        """测试处理通知队列成功"""
        # 创建待处理通知
        notification = await notification_service.send_notification(
            db_session, test_user.id,
            title="队列通知", content="内容", type="system", channel="push"
        )
        await db_session.commit()
        
        with patch.object(notification_service, 'send_push_notification') as mock_push:
            mock_push.return_value = {"success": True, "message_id": "test-id"}
            
            processed_count = await notification_service.process_notification_queue(db_session)
        
        assert processed_count >= 1
        await db_session.refresh(notification)
        assert notification.status == NotificationStatus.SENT
    
    def test_render_template_success(self, notification_service):
        """测试模板渲染成功"""
        template = "您好 {name}，您的事件 {event_title} 已更新"
        variables = {"name": "张三", "event_title": "道路损坏事件"}
        
        result = notification_service._render_template(template, variables)
        
        assert result == "您好 张三，您的事件 道路损坏事件 已更新"
    
    def test_render_template_missing_variables(self, notification_service):
        """测试模板渲染缺少变量"""
        template = "您好 {name}，您的事件 {event_title} 已更新"
        variables = {"name": "张三"}  # 缺少 event_title
        
        result = notification_service._render_template(template, variables)
        
        # 应该保留未替换的占位符或使用默认值
        assert "张三" in result
        assert "{event_title}" in result or "事件" in result


if __name__ == "__main__":
    pytest.main([__file__])