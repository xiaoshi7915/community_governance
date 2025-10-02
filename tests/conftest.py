"""
测试配置和共享fixtures
"""
import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models import Base
from app.models.user import User
from app.models.event import Event, EventTimeline, EventMedia
from app.models.notification import Notification, NotificationTemplate


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# 创建测试会话工厂
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
    
    # 清理数据库
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=False)
    mock_redis.expire = Mock(return_value=True)
    mock_redis.hget = Mock(return_value=None)
    mock_redis.hset = Mock(return_value=True)
    mock_redis.hdel = Mock(return_value=1)
    mock_redis.hgetall = Mock(return_value={})
    return mock_redis


@pytest.fixture
def override_get_db(db_session):
    """覆盖数据库依赖"""
    async def _override_get_db():
        yield db_session
    return _override_get_db


@pytest.fixture
def override_get_redis(mock_redis):
    """覆盖Redis依赖"""
    async def _override_get_redis():
        return mock_redis
    return _override_get_redis


@pytest.fixture
def test_client(override_get_db, override_get_redis):
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_get_db, override_get_redis):
    """创建异步测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    from app.services.auth_service import AuthService
    
    auth_service = AuthService()
    user_data = {
        "phone": "13800138000",
        "password": "test123456",
        "name": "测试用户"
    }
    
    user = await auth_service.create_user(db_session, **user_data)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_event(db_session: AsyncSession, test_user: User):
    """创建测试事件"""
    from app.services.event_service import EventService
    
    event_service = EventService()
    event_data = {
        "title": "测试事件",
        "description": "这是一个测试事件",
        "event_type": "道路损坏",
        "location_lat": 39.9042,
        "location_lng": 116.4074,
        "location_address": "北京市朝阳区",
        "priority": "medium"
    }
    
    event = await event_service.create_event(db_session, test_user.id, **event_data)
    await db_session.commit()
    return event


@pytest.fixture
def mock_oss_service():
    """模拟OSS服务"""
    with patch('app.services.oss_service.OSSService') as mock:
        mock_instance = Mock()
        mock_instance.upload_file.return_value = {
            "file_key": "test/file.png",
            "file_url": "https://example.com/test/file.png",
            "file_name": "file.png",
            "etag": "test-etag"
        }
        mock_instance.generate_presigned_url.return_value = "https://example.com/presigned-url"
        mock_instance.delete_file.return_value = True
        mock_instance.get_file_info.return_value = {
            "file_key": "test/file.png",
            "file_size": 1024,
            "content_type": "image/png",
            "etag": "test-etag"
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ai_service():
    """模拟AI服务"""
    with patch('app.services.ai_service.AIService') as mock:
        from app.services.ai_service import AIAnalysisResult, EventClassification
        
        mock_instance = Mock()
        mock_instance.analyze_image.return_value = AIAnalysisResult(
            event_type="道路损坏",
            description="道路表面有裂缝",
            confidence=0.8,
            details={"test": True},
            raw_response={}
        )
        mock_instance.analyze_video.return_value = AIAnalysisResult(
            event_type="垃圾堆积",
            description="垃圾堆积严重",
            confidence=0.7,
            details={"test": True},
            raw_response={}
        )
        mock_instance.classify_event_type.return_value = EventClassification(
            primary_type="道路损坏",
            secondary_type=None,
            confidence=0.8,
            suggested_priority="high",
            keywords=["道路", "损坏"]
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_location_service():
    """模拟地理位置服务"""
    with patch('app.services.location_service.LocationService') as mock:
        mock_instance = Mock()
        mock_instance.get_address_from_coordinates.return_value = {
            "formatted_address": "北京市朝阳区测试街道123号",
            "province": "北京市",
            "city": "北京市",
            "district": "朝阳区",
            "street": "测试街道",
            "street_number": "123号"
        }
        mock_instance.get_coordinates_from_address.return_value = {
            "lat": 39.9042,
            "lng": 116.4074
        }
        mock_instance.validate_address.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_notification_service():
    """模拟通知服务"""
    with patch('app.services.notification_service.NotificationService') as mock:
        mock_instance = Mock()
        mock_instance.send_notification.return_value = {
            "success": True,
            "notification_id": "test-notification-id",
            "message": "通知发送成功"
        }
        mock_instance.send_push_notification.return_value = True
        mock_instance.send_sms_notification.return_value = True
        mock_instance.send_email_notification.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_image_file():
    """创建示例图片文件"""
    from io import BytesIO
    from fastapi import UploadFile
    
    # 创建一个简单的PNG文件内容
    content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    
    file = UploadFile(
        filename="test.png",
        file=BytesIO(content),
        size=len(content),
        headers={"content-type": "image/png"}
    )
    return file


@pytest.fixture
def sample_video_file():
    """创建示例视频文件"""
    from io import BytesIO
    from fastapi import UploadFile
    
    # 创建一个简单的视频文件内容（模拟）
    content = b'fake_video_content'
    
    file = UploadFile(
        filename="test.mp4",
        file=BytesIO(content),
        size=len(content),
        headers={"content-type": "video/mp4"}
    )
    return file


@pytest.fixture
def auth_headers(test_user):
    """创建认证头"""
    from app.core.security import create_access_token
    
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_user_data(**kwargs):
        """创建用户数据"""
        default_data = {
            "phone": "13800138000",
            "password": "test123456",
            "name": "测试用户",
            "avatar_url": None
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_event_data(**kwargs):
        """创建事件数据"""
        default_data = {
            "title": "测试事件",
            "description": "这是一个测试事件",
            "event_type": "道路损坏",
            "location_lat": 39.9042,
            "location_lng": 116.4074,
            "location_address": "北京市朝阳区",
            "priority": "medium",
            "status": "pending"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_notification_data(**kwargs):
        """创建通知数据"""
        default_data = {
            "title": "测试通知",
            "content": "这是一个测试通知",
            "type": "event_update",
            "channel": "push"
        }
        default_data.update(kwargs)
        return default_data


@pytest.fixture
def test_data_factory():
    """测试数据工厂fixture"""
    return TestDataFactory


# 清理函数
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """自动清理测试数据"""
    yield
    
    # 测试完成后清理
    try:
        # 清理测试数据库文件
        if os.path.exists("./test.db"):
            os.remove("./test.db")
    except Exception:
        pass  # 忽略清理错误


# 环境变量设置
@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境变量"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    yield
    # 清理环境变量
    os.environ.pop("TESTING", None)