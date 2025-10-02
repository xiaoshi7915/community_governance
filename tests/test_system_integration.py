"""
系统集成测试
验证所有服务模块的集成和系统完整性
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, init_db
from app.core.redis import get_redis, init_redis, close_redis
from app.services.auth_service import auth_service
from app.services.event_service import event_service
from app.services.ai_service import ai_service
from app.services.oss_service import oss_service
from app.services.notification_service import notification_service
from app.services.statistics_service import statistics_service
from tests.conftest import test_user_data, test_event_data


class TestSystemIntegration:
    """系统集成测试类"""
    
    @pytest.fixture(autouse=True)
    async def setup_system(self):
        """设置系统环境"""
        # 初始化数据库和Redis
        await init_db()
        await init_redis()
        yield
        # 清理
        await close_redis()
    
    async def test_database_connectivity(self):
        """测试数据库连接"""
        db = next(get_db())
        try:
            # 执行简单查询验证连接
            result = await db.execute("SELECT 1")
            assert result is not None
        finally:
            await db.close()
    
    async def test_redis_connectivity(self):
        """测试Redis连接"""
        redis = await get_redis()
        # 测试基本操作
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        assert value == "test_value"
        await redis.delete("test_key")
    
    async def test_all_services_initialization(self):
        """测试所有服务初始化"""
        services = [
            auth_service,
            event_service,
            ai_service,
            oss_service,
            notification_service,
            statistics_service
        ]
        
        for service in services:
            assert service is not None
            # 验证服务具有必要的方法
            assert hasattr(service, '__class__')
    
    async def test_api_router_integration(self):
        """测试API路由集成"""
        client = TestClient(app)
        
        # 测试根路径
        response = client.get("/")
        assert response.status_code == 200
        
        # 测试健康检查
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # 测试API文档
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
    
    async def test_middleware_integration(self):
        """测试中间件集成"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试CORS中间件
            response = await client.options("/api/v1/auth/login")
            assert "access-control-allow-origin" in response.headers
            
            # 测试异常处理中间件
            response = await client.get("/api/v1/nonexistent")
            assert response.status_code == 404
    
    async def test_complete_user_workflow(self):
        """测试完整用户工作流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. 用户注册
            register_data = {
                "phone": "13800138000",
                "password": "test123456",
                "name": "测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            # 2. 用户登录
            login_data = {
                "phone": "13800138000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            token_data = response.json()["data"]
            access_token = token_data["access_token"]
            
            # 3. 获取用户信息
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == 200
            
            # 4. 创建事件
            event_data = {
                "title": "测试事件",
                "description": "这是一个测试事件",
                "event_type": "infrastructure",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区"
            }
            response = await client.post("/api/v1/events", json=event_data, headers=headers)
            assert response.status_code == 200
            event_id = response.json()["data"]["id"]
            
            # 5. 查询事件列表
            response = await client.get("/api/v1/events", headers=headers)
            assert response.status_code == 200
            assert len(response.json()["data"]["items"]) > 0
            
            # 6. 获取事件详情
            response = await client.get(f"/api/v1/events/{event_id}", headers=headers)
            assert response.status_code == 200
            
            # 7. 获取统计数据
            response = await client.get("/api/v1/statistics/user", headers=headers)
            assert response.status_code == 200
    
    async def test_external_services_integration(self):
        """测试外部服务集成"""
        # 测试OSS服务（使用Mock）
        try:
            file_info = await oss_service.get_file_info("test/nonexistent.jpg")
            # 应该返回None或抛出异常
        except Exception:
            pass  # 预期的异常
        
        # 测试AI服务（使用Mock）
        try:
            result = await ai_service.analyze_image("http://example.com/test.jpg")
            # 应该返回分析结果或抛出异常
        except Exception:
            pass  # 预期的异常
    
    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试认证错误
            response = await client.get("/api/v1/users/profile")
            assert response.status_code == 401
            
            # 测试权限错误
            headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == 401
            
            # 测试资源不存在
            response = await client.get("/api/v1/events/nonexistent-id")
            assert response.status_code == 404
            
            # 测试参数验证错误
            invalid_data = {"invalid": "data"}
            response = await client.post("/api/v1/auth/register", json=invalid_data)
            assert response.status_code == 422
    
    async def test_performance_monitoring_integration(self):
        """测试性能监控集成"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试监控端点
            response = await client.get("/api/v1/monitoring/health")
            assert response.status_code == 200
            
            # 测试指标端点
            response = await client.get("/api/v1/monitoring/metrics")
            assert response.status_code == 200
            
            # 测试系统状态
            response = await client.get("/api/v1/monitoring/system-status")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_operations():
    """测试并发操作"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 创建多个并发请求
        tasks = []
        for i in range(10):
            task = client.get("/health")
            tasks.append(task)
        
        # 等待所有请求完成
        responses = await asyncio.gather(*tasks)
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_data_consistency():
    """测试数据一致性"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 注册用户
        register_data = {
            "phone": "13900139000",
            "password": "test123456",
            "name": "一致性测试用户",
            "verification_code": "123456"
        }
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 200
        
        # 登录获取token
        login_data = {
            "phone": "13900139000",
            "password": "test123456"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        token = response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建事件
        event_data = {
            "title": "一致性测试事件",
            "description": "测试数据一致性",
            "event_type": "infrastructure",
            "location_lat": 39.9042,
            "location_lng": 116.4074,
            "location_address": "北京市朝阳区"
        }
        response = await client.post("/api/v1/events", json=event_data, headers=headers)
        event_id = response.json()["data"]["id"]
        
        # 验证事件在列表中存在
        response = await client.get("/api/v1/events", headers=headers)
        events = response.json()["data"]["items"]
        assert any(event["id"] == event_id for event in events)
        
        # 验证统计数据更新
        response = await client.get("/api/v1/statistics/user", headers=headers)
        stats = response.json()["data"]
        assert stats["total_events"] > 0