"""
通知系统测试
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime

from app.models.notification import (
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)
from app.services.notification_service import notification_service
from app.services.notification_preference_service import notification_preference_service
from app.services.notification_template_service import notification_template_service
from app.core.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_notification_service():
    """测试通知服务基本功能"""
    async with AsyncSessionLocal() as db:
        # 创建测试用户ID
        test_user_id = uuid4()
        
        # 创建通知
        notification = await notification_service.create_notification(
            user_id=test_user_id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            channel=NotificationChannel.IN_APP,
            title="测试通知",
            content="这是一个测试通知",
            recipient=str(test_user_id),
            priority=NotificationPriority.NORMAL,
            db=db
        )
        
        assert notification is not None
        assert notification.title == "测试通知"
        assert notification.status == NotificationStatus.PENDING
        
        # 发送通知
        success = await notification_service.send_notification(notification.id, db)
        assert success is True
        
        # 获取用户通知
        notifications = await notification_service.get_user_notifications(
            user_id=test_user_id,
            db=db
        )
        
        assert len(notifications) >= 1
        assert any(n.id == notification.id for n in notifications)
        
        print("✓ 通知服务测试通过")


@pytest.mark.asyncio
async def test_notification_preferences():
    """测试通知偏好服务"""
    async with AsyncSessionLocal() as db:
        test_user_id = uuid4()
        
        # 初始化默认偏好
        preferences = await notification_preference_service.initialize_default_preferences(
            user_id=test_user_id,
            db=db
        )
        
        assert len(preferences) > 0
        
        # 获取偏好摘要
        summary = await notification_preference_service.get_preference_summary(
            user_id=test_user_id,
            db=db
        )
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        
        # 更新偏好
        updated_preference = await notification_preference_service.set_user_preference(
            user_id=test_user_id,
            notification_type=NotificationType.EVENT_STATUS_CHANGE,
            channel=NotificationChannel.PUSH,
            enabled=False,
            db=db
        )
        
        assert updated_preference.enabled is False
        
        print("✓ 通知偏好服务测试通过")


@pytest.mark.asyncio
async def test_notification_templates():
    """测试通知模板服务"""
    async with AsyncSessionLocal() as db:
        # 初始化默认模板
        templates = await notification_template_service.initialize_default_templates(db)
        
        # 获取所有模板
        all_templates = await notification_template_service.get_all_templates(db=db)
        assert len(all_templates) > 0
        
        # 获取特定类型的模板
        event_templates = await notification_template_service.get_templates_by_type_and_channel(
            notification_type=NotificationType.EVENT_STATUS_CHANGE,
            channel=NotificationChannel.PUSH,
            db=db
        )
        
        assert len(event_templates) > 0
        
        # 创建自定义模板
        custom_template = await notification_template_service.create_template(
            template_key="test_template",
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            channel=NotificationChannel.IN_APP,
            title_template="测试模板",
            content_template="这是一个测试模板：{content}",
            variables={"content": "模板内容"},
            db=db
        )
        
        assert custom_template is not None
        assert custom_template.template_key == "test_template"
        
        print("✓ 通知模板服务测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("开始测试通知系统...")
    
    try:
        await test_notification_service()
        await test_notification_preferences()
        await test_notification_templates()
        
        print("\n🎉 所有通知系统测试通过！")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())