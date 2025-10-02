"""
测试数据工厂和自动化测试数据清理
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from app.models.user import User
from app.models.event import Event, EventTimeline, EventMedia, EventStatus, EventPriority
from app.models.notification import Notification, NotificationTemplate, NotificationStatus, NotificationChannel
from app.services.auth_service import AuthService
from app.services.event_service import EventService
from app.services.notification_service import NotificationService

fake = Faker('zh_CN')


class TestDataFactory:
    """测试数据工厂类"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.event_service = EventService()
        self.notification_service = NotificationService()
        self.created_objects = {
            'users': [],
            'events': [],
            'notifications': [],
            'templates': [],
            'media': []
        }
    
    async def create_user(
        self,
        db_session: AsyncSession,
        phone: Optional[str] = None,
        password: str = "test123456",
        name: Optional[str] = None,
        **kwargs
    ) -> User:
        """创建测试用户"""
        if not phone:
            phone = fake.phone_number().replace('-', '').replace(' ', '')[:11]
            if not phone.startswith('1'):
                phone = '138' + phone[3:]
        
        if not name:
            name = fake.name()
        
        user_data = {
            "phone": phone,
            "password": password,
            "name": name,
            **kwargs
        }
        
        user = await self.auth_service.create_user(db_session, **user_data)
        self.created_objects['users'].append(user.id)
        return user
    
    async def create_multiple_users(
        self,
        db_session: AsyncSession,
        count: int = 5,
        **kwargs
    ) -> List[User]:
        """创建多个测试用户"""
        users = []
        for i in range(count):
            user = await self.create_user(
                db_session,
                phone=f"1380013800{i:01d}",
                name=f"测试用户{i+1}",
                **kwargs
            )
            users.append(user)
        return users
    
    async def create_event(
        self,
        db_session: AsyncSession,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        event_type: str = "道路损坏",
        **kwargs
    ) -> Event:
        """创建测试事件"""
        if not title:
            title = fake.sentence(nb_words=4)
        
        if not description:
            description = fake.text(max_nb_chars=200)
        
        event_data = {
            "title": title,
            "description": description,
            "event_type": event_type,
            "location_lat": float(fake.latitude()),
            "location_lng": float(fake.longitude()),
            "location_address": fake.address(),
            "priority": fake.random_element(elements=["low", "medium", "high"]),
            **kwargs
        }
        
        event = await self.event_service.create_event(db_session, user_id, **event_data)
        self.created_objects['events'].append(event.id)
        return event
    
    async def create_multiple_events(
        self,
        db_session: AsyncSession,
        user_id: str,
        count: int = 10,
        **kwargs
    ) -> List[Event]:
        """创建多个测试事件"""
        events = []
        event_types = ["道路损坏", "垃圾堆积", "违章建筑", "环境污染", "公共设施损坏", "交通问题", "其他"]
        
        for i in range(count):
            event = await self.create_event(
                db_session,
                user_id,
                title=f"测试事件 {i+1}",
                event_type=fake.random_element(elements=event_types),
                **kwargs
            )
            events.append(event)
        return events
    
    async def create_event_with_media(
        self,
        db_session: AsyncSession,
        user_id: str,
        media_count: int = 3,
        **kwargs
    ) -> Event:
        """创建带媒体文件的测试事件"""
        # 生成媒体URL
        media_urls = []
        for i in range(media_count):
            if i % 2 == 0:
                media_urls.append(f"https://example.com/image_{i+1}.jpg")
            else:
                media_urls.append(f"https://example.com/video_{i+1}.mp4")
        
        event_data = {
            "media_urls": media_urls,
            **kwargs
        }
        
        event = await self.create_event(db_session, user_id, **event_data)
        return event
    
    async def create_event_timeline(
        self,
        db_session: AsyncSession,
        event_id: str,
        status_changes: List[str] = None
    ) -> List[EventTimeline]:
        """创建事件时间线"""
        if not status_changes:
            status_changes = ["processing", "completed"]
        
        timeline_entries = []
        operator_id = uuid4()
        
        for status in status_changes:
            updated_event = await self.event_service.update_event_status(
                db_session,
                event_id,
                status,
                operator_id,
                f"状态更新为 {status}"
            )
            timeline_entries.append(updated_event)
        
        return timeline_entries
    
    async def create_notification(
        self,
        db_session: AsyncSession,
        user_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs
    ) -> Notification:
        """创建测试通知"""
        if not title:
            title = fake.sentence(nb_words=3)
        
        if not content:
            content = fake.text(max_nb_chars=100)
        
        notification_data = {
            "title": title,
            "content": content,
            "type": fake.random_element(elements=["event_update", "system", "reminder", "promotion"]),
            "channel": fake.random_element(elements=["push", "sms", "email"]),
            **kwargs
        }
        
        notification = await self.notification_service.send_notification(
            db_session,
            user_id,
            **notification_data
        )
        self.created_objects['notifications'].append(notification.id)
        return notification
    
    async def create_multiple_notifications(
        self,
        db_session: AsyncSession,
        user_id: str,
        count: int = 5,
        **kwargs
    ) -> List[Notification]:
        """创建多个测试通知"""
        notifications = []
        for i in range(count):
            notification = await self.create_notification(
                db_session,
                user_id,
                title=f"测试通知 {i+1}",
                **kwargs
            )
            notifications.append(notification)
        return notifications
    
    async def create_notification_template(
        self,
        db_session: AsyncSession,
        name: Optional[str] = None,
        **kwargs
    ) -> NotificationTemplate:
        """创建通知模板"""
        if not name:
            name = fake.sentence(nb_words=2)
        
        template_data = {
            "name": name,
            "title": fake.sentence(nb_words=3) + " {variable}",
            "content": fake.text(max_nb_chars=100) + " {variable}",
            "type": fake.random_element(elements=["event_update", "system", "reminder"]),
            **kwargs
        }
        
        template = await self.notification_service.create_notification_template(
            db_session,
            **template_data
        )
        self.created_objects['templates'].append(template.id)
        return template
    
    def create_sample_file_data(self, file_type: str = "image") -> Dict[str, Any]:
        """创建示例文件数据"""
        if file_type == "image":
            return {
                "file_key": f"test/images/{fake.uuid4()}.jpg",
                "file_url": f"https://example.com/images/{fake.uuid4()}.jpg",
                "file_name": f"{fake.word()}.jpg",
                "file_size": fake.random_int(min=1024, max=1024*1024),
                "content_type": "image/jpeg",
                "etag": fake.md5()
            }
        elif file_type == "video":
            return {
                "file_key": f"test/videos/{fake.uuid4()}.mp4",
                "file_url": f"https://example.com/videos/{fake.uuid4()}.mp4",
                "file_name": f"{fake.word()}.mp4",
                "file_size": fake.random_int(min=1024*1024, max=100*1024*1024),
                "content_type": "video/mp4",
                "etag": fake.md5()
            }
        else:
            return {
                "file_key": f"test/files/{fake.uuid4()}.txt",
                "file_url": f"https://example.com/files/{fake.uuid4()}.txt",
                "file_name": f"{fake.word()}.txt",
                "file_size": fake.random_int(min=100, max=10240),
                "content_type": "text/plain",
                "etag": fake.md5()
            }
    
    def create_ai_analysis_result(self) -> Dict[str, Any]:
        """创建AI分析结果数据"""
        event_types = ["道路损坏", "垃圾堆积", "违章建筑", "环境污染", "公共设施损坏", "交通问题", "其他"]
        
        return {
            "event_type": fake.random_element(elements=event_types),
            "description": fake.text(max_nb_chars=200),
            "confidence": fake.random.uniform(0.1, 1.0),
            "details": {
                "analysis_method": fake.random_element(elements=["aliyun_ai", "fallback"]),
                "processing_time": fake.random.uniform(0.5, 5.0),
                "model": "qwen-vl-plus"
            },
            "raw_response": {
                "choices": [{"message": {"content": fake.text()}}],
                "usage": {"input_tokens": fake.random_int(50, 200), "output_tokens": fake.random_int(20, 100)}
            }
        }
    
    def create_location_data(self) -> Dict[str, Any]:
        """创建地理位置数据"""
        return {
            "lat": float(fake.latitude()),
            "lng": float(fake.longitude()),
            "address": fake.address(),
            "province": fake.province(),
            "city": fake.city(),
            "district": fake.district(),
            "street": fake.street_name(),
            "street_number": fake.building_number()
        }
    
    async def create_complete_scenario(
        self,
        db_session: AsyncSession,
        user_count: int = 3,
        events_per_user: int = 5,
        notifications_per_user: int = 3
    ) -> Dict[str, List]:
        """创建完整的测试场景"""
        # 创建用户
        users = await self.create_multiple_users(db_session, user_count)
        
        # 为每个用户创建事件和通知
        all_events = []
        all_notifications = []
        
        for user in users:
            # 创建事件
            events = await self.create_multiple_events(
                db_session, 
                user.id, 
                events_per_user
            )
            all_events.extend(events)
            
            # 为部分事件创建时间线
            for i, event in enumerate(events[:2]):
                await self.create_event_timeline(db_session, event.id)
            
            # 创建通知
            notifications = await self.create_multiple_notifications(
                db_session,
                user.id,
                notifications_per_user
            )
            all_notifications.extend(notifications)
        
        # 创建通知模板
        templates = []
        for i in range(3):
            template = await self.create_notification_template(
                db_session,
                name=f"模板 {i+1}"
            )
            templates.append(template)
        
        await db_session.commit()
        
        return {
            "users": users,
            "events": all_events,
            "notifications": all_notifications,
            "templates": templates
        }
    
    async def cleanup_all(self, db_session: AsyncSession):
        """清理所有创建的测试数据"""
        try:
            # 删除通知
            for notification_id in self.created_objects['notifications']:
                try:
                    await db_session.execute(
                        "DELETE FROM notifications WHERE id = :id",
                        {"id": notification_id}
                    )
                except Exception:
                    pass
            
            # 删除模板
            for template_id in self.created_objects['templates']:
                try:
                    await db_session.execute(
                        "DELETE FROM notification_templates WHERE id = :id",
                        {"id": template_id}
                    )
                except Exception:
                    pass
            
            # 删除事件媒体
            for event_id in self.created_objects['events']:
                try:
                    await db_session.execute(
                        "DELETE FROM event_media WHERE event_id = :id",
                        {"id": event_id}
                    )
                except Exception:
                    pass
            
            # 删除事件时间线
            for event_id in self.created_objects['events']:
                try:
                    await db_session.execute(
                        "DELETE FROM event_timeline WHERE event_id = :id",
                        {"id": event_id}
                    )
                except Exception:
                    pass
            
            # 删除事件
            for event_id in self.created_objects['events']:
                try:
                    await db_session.execute(
                        "DELETE FROM events WHERE id = :id",
                        {"id": event_id}
                    )
                except Exception:
                    pass
            
            # 删除用户
            for user_id in self.created_objects['users']:
                try:
                    await db_session.execute(
                        "DELETE FROM users WHERE id = :id",
                        {"id": user_id}
                    )
                except Exception:
                    pass
            
            await db_session.commit()
            
            # 清空记录
            self.created_objects = {
                'users': [],
                'events': [],
                'notifications': [],
                'templates': [],
                'media': []
            }
            
        except Exception as e:
            await db_session.rollback()
            print(f"清理测试数据时发生错误: {e}")


class TestDataCleaner:
    """测试数据清理器"""
    
    @staticmethod
    async def cleanup_test_database(db_session: AsyncSession):
        """清理整个测试数据库"""
        try:
            # 按依赖关系顺序删除表数据
            tables = [
                "event_media",
                "event_timeline", 
                "notifications",
                "notification_templates",
                "events",
                "users"
            ]
            
            for table in tables:
                try:
                    await db_session.execute(f"DELETE FROM {table}")
                except Exception:
                    pass  # 忽略表不存在的错误
            
            await db_session.commit()
            
        except Exception as e:
            await db_session.rollback()
            print(f"清理测试数据库时发生错误: {e}")
    
    @staticmethod
    async def cleanup_old_test_data(db_session: AsyncSession, days_old: int = 1):
        """清理指定天数前的测试数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # 删除旧的测试数据
            await db_session.execute(
                "DELETE FROM notifications WHERE created_at < :cutoff AND title LIKE '测试%'",
                {"cutoff": cutoff_date}
            )
            
            await db_session.execute(
                "DELETE FROM events WHERE created_at < :cutoff AND title LIKE '测试%'",
                {"cutoff": cutoff_date}
            )
            
            await db_session.execute(
                "DELETE FROM users WHERE created_at < :cutoff AND name LIKE '测试%'",
                {"cutoff": cutoff_date}
            )
            
            await db_session.commit()
            
        except Exception as e:
            await db_session.rollback()
            print(f"清理旧测试数据时发生错误: {e}")


# Pytest fixtures
@pytest.fixture
def test_data_factory():
    """测试数据工厂fixture"""
    return TestDataFactory()


@pytest.fixture
async def test_scenario(db_session: AsyncSession, test_data_factory: TestDataFactory):
    """完整测试场景fixture"""
    scenario = await test_data_factory.create_complete_scenario(db_session)
    yield scenario
    # 自动清理
    await test_data_factory.cleanup_all(db_session)


@pytest.fixture(autouse=True)
async def auto_cleanup(db_session: AsyncSession):
    """自动清理fixture"""
    yield
    # 测试完成后自动清理
    await TestDataCleaner.cleanup_test_database(db_session)


if __name__ == "__main__":
    # 可以单独运行此文件来测试数据工厂
    import asyncio
    from tests.conftest import TestSessionLocal, test_engine
    
    async def test_factory():
        async with TestSessionLocal() as session:
            factory = TestDataFactory()
            
            # 创建测试场景
            scenario = await factory.create_complete_scenario(session)
            
            print(f"创建了 {len(scenario['users'])} 个用户")
            print(f"创建了 {len(scenario['events'])} 个事件")
            print(f"创建了 {len(scenario['notifications'])} 个通知")
            print(f"创建了 {len(scenario['templates'])} 个模板")
            
            # 清理数据
            await factory.cleanup_all(session)
            print("清理完成")
    
    asyncio.run(test_factory())