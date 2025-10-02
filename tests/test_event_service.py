"""
事件管理服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.event_service import EventService
from app.models.user import User
from app.models.event import Event, EventTimeline, EventMedia, EventStatus, EventPriority
from app.core.exceptions import ValidationError, NotFoundError, PermissionError


class TestEventService:
    """事件服务测试类"""
    
    @pytest.fixture
    def event_service(self):
        """创建事件服务实例"""
        return EventService()
    
    @pytest.mark.asyncio
    async def test_create_event_success(self, event_service, db_session: AsyncSession, test_user: User):
        """测试创建事件成功"""
        event_data = {
            "title": "新建事件",
            "description": "这是一个新建的测试事件",
            "event_type": "道路损坏",
            "location_lat": 39.9042,
            "location_lng": 116.4074,
            "location_address": "北京市朝阳区测试街道",
            "priority": "high"
        }
        
        event = await event_service.create_event(db_session, test_user.id, **event_data)
        
        assert event.title == "新建事件"
        assert event.description == "这是一个新建的测试事件"
        assert event.event_type == "道路损坏"
        assert event.user_id == test_user.id
        assert event.status == EventStatus.PENDING
        assert event.priority == EventPriority.HIGH
        assert event.location_lat == 39.9042
        assert event.location_lng == 116.4074
        assert event.id is not None
        assert event.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_event_with_media(self, event_service, db_session: AsyncSession, test_user: User):
        """测试创建带媒体文件的事件"""
        event_data = {
            "title": "带媒体的事件",
            "description": "包含媒体文件的事件",
            "event_type": "垃圾堆积",
            "location_lat": 39.9042,
            "location_lng": 116.4074,
            "location_address": "北京市朝阳区",
            "media_urls": ["https://example.com/image1.jpg", "https://example.com/video1.mp4"]
        }
        
        event = await event_service.create_event(db_session, test_user.id, **event_data)
        
        assert len(event.media_files) == 2
        assert event.media_files[0].file_url == "https://example.com/image1.jpg"
        assert event.media_files[1].file_url == "https://example.com/video1.mp4"
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_data(self, event_service, db_session: AsyncSession, test_user: User):
        """测试创建事件时数据无效"""
        # 测试缺少必填字段
        with pytest.raises(ValidationError, match="标题不能为空"):
            await event_service.create_event(
                db_session, 
                test_user.id,
                title="",
                description="描述",
                event_type="道路损坏"
            )
        
        # 测试无效的事件类型
        with pytest.raises(ValidationError, match="无效的事件类型"):
            await event_service.create_event(
                db_session,
                test_user.id,
                title="测试事件",
                description="描述",
                event_type="无效类型"
            )
        
        # 测试无效的优先级
        with pytest.raises(ValidationError, match="无效的优先级"):
            await event_service.create_event(
                db_session,
                test_user.id,
                title="测试事件",
                description="描述",
                event_type="道路损坏",
                priority="invalid_priority"
            )
    
    @pytest.mark.asyncio
    async def test_get_event_success(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试获取事件成功"""
        event = await event_service.get_event(db_session, test_event.id)
        
        assert event is not None
        assert event.id == test_event.id
        assert event.title == test_event.title
    
    @pytest.mark.asyncio
    async def test_get_event_not_found(self, event_service, db_session: AsyncSession):
        """测试获取不存在的事件"""
        with pytest.raises(NotFoundError, match="事件不存在"):
            await event_service.get_event(db_session, uuid4())
    
    @pytest.mark.asyncio
    async def test_get_user_events_success(self, event_service, db_session: AsyncSession, test_user: User, test_event: Event):
        """测试获取用户事件列表成功"""
        # 创建额外的事件
        await event_service.create_event(
            db_session,
            test_user.id,
            title="第二个事件",
            description="第二个测试事件",
            event_type="垃圾堆积"
        )
        await db_session.commit()
        
        events = await event_service.get_user_events(db_session, test_user.id)
        
        assert len(events) == 2
        assert all(event.user_id == test_user.id for event in events)
    
    @pytest.mark.asyncio
    async def test_get_user_events_with_filters(self, event_service, db_session: AsyncSession, test_user: User):
        """测试带过滤条件的用户事件列表"""
        # 创建不同状态的事件
        await event_service.create_event(
            db_session,
            test_user.id,
            title="待处理事件",
            description="待处理的事件",
            event_type="道路损坏",
            status="pending"
        )
        
        await event_service.create_event(
            db_session,
            test_user.id,
            title="处理中事件",
            description="处理中的事件",
            event_type="垃圾堆积",
            status="processing"
        )
        await db_session.commit()
        
        # 测试状态过滤
        pending_events = await event_service.get_user_events(
            db_session, 
            test_user.id, 
            status="pending"
        )
        assert len(pending_events) == 1
        assert pending_events[0].status == EventStatus.PENDING
        
        # 测试事件类型过滤
        road_events = await event_service.get_user_events(
            db_session,
            test_user.id,
            event_type="道路损坏"
        )
        assert len(road_events) == 1
        assert road_events[0].event_type == "道路损坏"
    
    @pytest.mark.asyncio
    async def test_get_user_events_with_pagination(self, event_service, db_session: AsyncSession, test_user: User):
        """测试分页获取用户事件"""
        # 创建多个事件
        for i in range(5):
            await event_service.create_event(
                db_session,
                test_user.id,
                title=f"事件 {i+1}",
                description=f"第 {i+1} 个事件",
                event_type="道路损坏"
            )
        await db_session.commit()
        
        # 测试分页
        page1_events = await event_service.get_user_events(
            db_session,
            test_user.id,
            skip=0,
            limit=3
        )
        assert len(page1_events) == 3
        
        page2_events = await event_service.get_user_events(
            db_session,
            test_user.id,
            skip=3,
            limit=3
        )
        assert len(page2_events) == 2
    
    @pytest.mark.asyncio
    async def test_update_event_success(self, event_service, db_session: AsyncSession, test_user: User, test_event: Event):
        """测试更新事件成功"""
        update_data = {
            "title": "更新后的标题",
            "description": "更新后的描述",
            "priority": "high"
        }
        
        updated_event = await event_service.update_event(
            db_session,
            test_event.id,
            test_user.id,
            **update_data
        )
        
        assert updated_event.title == "更新后的标题"
        assert updated_event.description == "更新后的描述"
        assert updated_event.priority == EventPriority.HIGH
        assert updated_event.updated_at > test_event.updated_at
    
    @pytest.mark.asyncio
    async def test_update_event_permission_denied(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试更新事件权限不足"""
        other_user_id = uuid4()
        
        with pytest.raises(PermissionError, match="无权限修改此事件"):
            await event_service.update_event(
                db_session,
                test_event.id,
                other_user_id,
                title="尝试更新"
            )
    
    @pytest.mark.asyncio
    async def test_update_event_not_found(self, event_service, db_session: AsyncSession, test_user: User):
        """测试更新不存在的事件"""
        with pytest.raises(NotFoundError, match="事件不存在"):
            await event_service.update_event(
                db_session,
                uuid4(),
                test_user.id,
                title="更新标题"
            )
    
    @pytest.mark.asyncio
    async def test_update_event_status_success(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试更新事件状态成功"""
        operator_id = uuid4()
        
        updated_event = await event_service.update_event_status(
            db_session,
            test_event.id,
            "processing",
            operator_id,
            "开始处理事件"
        )
        
        assert updated_event.status == EventStatus.PROCESSING
        
        # 检查时间线记录
        timeline = await event_service.get_event_timeline(db_session, test_event.id)
        assert len(timeline) == 1
        assert timeline[0].status == EventStatus.PROCESSING
        assert timeline[0].operator_id == operator_id
        assert timeline[0].description == "开始处理事件"
    
    @pytest.mark.asyncio
    async def test_update_event_status_invalid(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试更新事件状态为无效状态"""
        with pytest.raises(ValidationError, match="无效的事件状态"):
            await event_service.update_event_status(
                db_session,
                test_event.id,
                "invalid_status",
                uuid4()
            )
    
    @pytest.mark.asyncio
    async def test_delete_event_success(self, event_service, db_session: AsyncSession, test_user: User, test_event: Event):
        """测试删除事件成功"""
        result = await event_service.delete_event(db_session, test_event.id, test_user.id)
        
        assert result is True
        
        # 验证事件已被删除
        with pytest.raises(NotFoundError):
            await event_service.get_event(db_session, test_event.id)
    
    @pytest.mark.asyncio
    async def test_delete_event_permission_denied(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试删除事件权限不足"""
        other_user_id = uuid4()
        
        with pytest.raises(PermissionError, match="无权限删除此事件"):
            await event_service.delete_event(db_session, test_event.id, other_user_id)
    
    @pytest.mark.asyncio
    async def test_delete_event_not_found(self, event_service, db_session: AsyncSession, test_user: User):
        """测试删除不存在的事件"""
        with pytest.raises(NotFoundError, match="事件不存在"):
            await event_service.delete_event(db_session, uuid4(), test_user.id)
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_success(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试获取事件时间线成功"""
        operator_id = uuid4()
        
        # 添加状态变更
        await event_service.update_event_status(
            db_session,
            test_event.id,
            "processing",
            operator_id,
            "开始处理"
        )
        
        await event_service.update_event_status(
            db_session,
            test_event.id,
            "completed",
            operator_id,
            "处理完成"
        )
        
        timeline = await event_service.get_event_timeline(db_session, test_event.id)
        
        assert len(timeline) == 2
        assert timeline[0].status == EventStatus.PROCESSING
        assert timeline[1].status == EventStatus.COMPLETED
        assert timeline[0].created_at < timeline[1].created_at
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_not_found(self, event_service, db_session: AsyncSession):
        """测试获取不存在事件的时间线"""
        with pytest.raises(NotFoundError, match="事件不存在"):
            await event_service.get_event_timeline(db_session, uuid4())
    
    @pytest.mark.asyncio
    async def test_add_event_media_success(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试添加事件媒体文件成功"""
        media_data = [
            {
                "file_url": "https://example.com/new_image.jpg",
                "media_type": "image",
                "thumbnail_url": "https://example.com/new_image_thumb.jpg"
            },
            {
                "file_url": "https://example.com/new_video.mp4",
                "media_type": "video",
                "thumbnail_url": "https://example.com/new_video_thumb.jpg"
            }
        ]
        
        media_files = await event_service.add_event_media(db_session, test_event.id, media_data)
        
        assert len(media_files) == 2
        assert media_files[0].file_url == "https://example.com/new_image.jpg"
        assert media_files[0].media_type == "image"
        assert media_files[1].file_url == "https://example.com/new_video.mp4"
        assert media_files[1].media_type == "video"
    
    @pytest.mark.asyncio
    async def test_remove_event_media_success(self, event_service, db_session: AsyncSession, test_event: Event):
        """测试删除事件媒体文件成功"""
        # 先添加媒体文件
        media_data = [{
            "file_url": "https://example.com/to_delete.jpg",
            "media_type": "image"
        }]
        media_files = await event_service.add_event_media(db_session, test_event.id, media_data)
        media_id = media_files[0].id
        
        result = await event_service.remove_event_media(db_session, media_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_events_by_location_success(self, event_service, db_session: AsyncSession, test_user: User):
        """测试按地理位置获取事件成功"""
        # 创建不同位置的事件
        await event_service.create_event(
            db_session,
            test_user.id,
            title="附近事件1",
            description="附近的事件",
            event_type="道路损坏",
            location_lat=39.9042,
            location_lng=116.4074
        )
        
        await event_service.create_event(
            db_session,
            test_user.id,
            title="附近事件2",
            description="附近的事件",
            event_type="垃圾堆积",
            location_lat=39.9050,
            location_lng=116.4080
        )
        
        await event_service.create_event(
            db_session,
            test_user.id,
            title="远处事件",
            description="远处的事件",
            event_type="道路损坏",
            location_lat=40.0000,
            location_lng=117.0000
        )
        await db_session.commit()
        
        # 搜索附近事件（半径1公里）
        nearby_events = await event_service.get_events_by_location(
            db_session,
            39.9042,
            116.4074,
            radius_km=1.0
        )
        
        assert len(nearby_events) == 2
        assert all("附近事件" in event.title for event in nearby_events)
    
    @pytest.mark.asyncio
    async def test_get_event_statistics_success(self, event_service, db_session: AsyncSession, test_user: User):
        """测试获取事件统计成功"""
        # 创建不同状态的事件
        await event_service.create_event(
            db_session, test_user.id,
            title="待处理事件1", description="描述", event_type="道路损坏", status="pending"
        )
        await event_service.create_event(
            db_session, test_user.id,
            title="待处理事件2", description="描述", event_type="垃圾堆积", status="pending"
        )
        await event_service.create_event(
            db_session, test_user.id,
            title="处理中事件", description="描述", event_type="道路损坏", status="processing"
        )
        await event_service.create_event(
            db_session, test_user.id,
            title="已完成事件", description="描述", event_type="道路损坏", status="completed"
        )
        await db_session.commit()
        
        stats = await event_service.get_event_statistics(db_session, test_user.id)
        
        assert stats["total_events"] == 4
        assert stats["pending_events"] == 2
        assert stats["processing_events"] == 1
        assert stats["completed_events"] == 1
        assert "道路损坏" in stats["events_by_type"]
        assert "垃圾堆积" in stats["events_by_type"]
        assert stats["events_by_type"]["道路损坏"] == 3
        assert stats["events_by_type"]["垃圾堆积"] == 1
    
    def test_validate_event_type_success(self, event_service):
        """测试事件类型验证成功"""
        valid_types = [
            "道路损坏",
            "垃圾堆积",
            "违章建筑",
            "环境污染",
            "公共设施损坏",
            "交通问题",
            "其他"
        ]
        
        for event_type in valid_types:
            assert event_service._validate_event_type(event_type) is True
    
    def test_validate_event_type_failure(self, event_service):
        """测试事件类型验证失败"""
        invalid_types = [
            "无效类型",
            "",
            None,
            123
        ]
        
        for event_type in invalid_types:
            assert event_service._validate_event_type(event_type) is False
    
    def test_validate_priority_success(self, event_service):
        """测试优先级验证成功"""
        valid_priorities = ["low", "medium", "high"]
        
        for priority in valid_priorities:
            assert event_service._validate_priority(priority) is True
    
    def test_validate_priority_failure(self, event_service):
        """测试优先级验证失败"""
        invalid_priorities = ["invalid", "", None, 123]
        
        for priority in invalid_priorities:
            assert event_service._validate_priority(priority) is False
    
    def test_validate_status_success(self, event_service):
        """测试状态验证成功"""
        valid_statuses = ["pending", "processing", "completed", "rejected"]
        
        for status in valid_statuses:
            assert event_service._validate_status(status) is True
    
    def test_validate_status_failure(self, event_service):
        """测试状态验证失败"""
        invalid_statuses = ["invalid", "", None, 123]
        
        for status in invalid_statuses:
            assert event_service._validate_status(status) is False
    
    def test_calculate_distance(self, event_service):
        """测试距离计算"""
        # 北京天安门到故宫的距离（大约1公里）
        distance = event_service._calculate_distance(
            39.9042, 116.4074,  # 天安门
            39.9163, 116.3972   # 故宫
        )
        
        # 距离应该在0.8-1.2公里之间
        assert 0.8 <= distance <= 1.2
    
    def test_calculate_distance_same_point(self, event_service):
        """测试相同点的距离计算"""
        distance = event_service._calculate_distance(
            39.9042, 116.4074,
            39.9042, 116.4074
        )
        
        assert distance == 0.0
    
    @pytest.mark.asyncio
    async def test_auto_assign_priority(self, event_service, db_session: AsyncSession, test_user: User):
        """测试自动分配优先级"""
        # 测试高优先级事件类型
        high_priority_event = await event_service.create_event(
            db_session,
            test_user.id,
            title="紧急事件",
            description="包含紧急关键词的事件",
            event_type="环境污染"
        )
        
        # 环境污染通常被分配为高优先级
        assert high_priority_event.priority in [EventPriority.HIGH, EventPriority.MEDIUM]
    
    @pytest.mark.asyncio
    async def test_bulk_update_events_success(self, event_service, db_session: AsyncSession, test_user: User):
        """测试批量更新事件成功"""
        # 创建多个事件
        events = []
        for i in range(3):
            event = await event_service.create_event(
                db_session,
                test_user.id,
                title=f"批量事件 {i+1}",
                description="批量更新测试",
                event_type="道路损坏"
            )
            events.append(event)
        await db_session.commit()
        
        event_ids = [event.id for event in events]
        update_data = {"priority": "high"}
        
        updated_count = await event_service.bulk_update_events(
            db_session,
            event_ids,
            test_user.id,
            **update_data
        )
        
        assert updated_count == 3
        
        # 验证更新结果
        for event_id in event_ids:
            event = await event_service.get_event(db_session, event_id)
            assert event.priority == EventPriority.HIGH


if __name__ == "__main__":
    pytest.main([__file__])