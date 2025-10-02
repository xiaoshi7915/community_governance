"""
API端点集成测试
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch
import json
from io import BytesIO

from app.models.user import User
from app.models.event import Event


class TestAuthAPIIntegration:
    """认证API集成测试"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient):
        """测试用户注册成功"""
        user_data = {
            "phone": "13800138001",
            "password": "test123456",
            "name": "新用户"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert data["data"]["user"]["phone"] == "13800138001"
        assert data["data"]["user"]["name"] == "新用户"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, async_client: AsyncClient, test_user: User):
        """测试注册重复手机号"""
        user_data = {
            "phone": test_user.phone,
            "password": "test123456",
            "name": "重复用户"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "手机号已被注册" in data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_register_invalid_data(self, async_client: AsyncClient):
        """测试注册无效数据"""
        user_data = {
            "phone": "invalid_phone",
            "password": "123",  # 太短
            "name": ""  # 空名称
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """测试用户登录成功"""
        login_data = {
            "phone": test_user.phone,
            "password": "test123456"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient, test_user: User):
        """测试登录无效凭据"""
        login_data = {
            "phone": test_user.phone,
            "password": "wrong_password"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "手机号或密码错误" in data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self, async_client: AsyncClient, test_user: User, auth_headers):
        """测试获取用户资料成功"""
        response = await async_client.get("/api/v1/users/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_user.id)
        assert data["data"]["phone"] == test_user.phone
        assert data["data"]["name"] == test_user.name
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, async_client: AsyncClient):
        """测试未授权获取用户资料"""
        response = await async_client.get("/api/v1/users/profile")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_profile_success(self, async_client: AsyncClient, test_user: User, auth_headers):
        """测试更新用户资料成功"""
        update_data = {
            "name": "更新后的用户名",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        
        response = await async_client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "更新后的用户名"
        assert data["data"]["avatar_url"] == "https://example.com/avatar.jpg"
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client: AsyncClient, test_user: User):
        """测试刷新令牌成功"""
        # 先登录获取令牌
        login_data = {"phone": test_user.phone, "password": "test123456"}
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        login_data = login_response.json()["data"]
        
        refresh_data = {"refresh_token": login_data["refresh_token"]}
        response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    @pytest.mark.asyncio
    async def test_logout_success(self, async_client: AsyncClient, test_user: User, auth_headers):
        """测试用户登出成功"""
        # 先登录获取令牌
        login_data = {"phone": test_user.phone, "password": "test123456"}
        login_response = await async_client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()["data"]
        
        logout_data = {"refresh_token": tokens["refresh_token"]}
        response = await async_client.post("/api/v1/auth/logout", json=logout_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestEventAPIIntegration:
    """事件API集成测试"""
    
    @pytest.mark.asyncio
    async def test_create_event_success(self, async_client: AsyncClient, test_user: User, auth_headers):
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
        
        response = await async_client.post("/api/v1/events", json=event_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "新建事件"
        assert data["data"]["event_type"] == "道路损坏"
        assert data["data"]["user_id"] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_create_event_unauthorized(self, async_client: AsyncClient):
        """测试未授权创建事件"""
        event_data = {
            "title": "测试事件",
            "description": "描述",
            "event_type": "道路损坏"
        }
        
        response = await async_client.post("/api/v1/events", json=event_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_event_invalid_data(self, async_client: AsyncClient, auth_headers):
        """测试创建事件无效数据"""
        event_data = {
            "title": "",  # 空标题
            "description": "描述",
            "event_type": "无效类型"  # 无效事件类型
        }
        
        response = await async_client.post("/api/v1/events", json=event_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_events_success(self, async_client: AsyncClient, test_user: User, test_event: Event, auth_headers):
        """测试获取事件列表成功"""
        response = await async_client.get("/api/v1/events", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == str(test_event.id)
    
    @pytest.mark.asyncio
    async def test_get_events_with_filters(self, async_client: AsyncClient, test_user: User, auth_headers):
        """测试带过滤条件获取事件列表"""
        # 创建不同类型的事件
        event_data1 = {
            "title": "道路事件",
            "description": "道路问题",
            "event_type": "道路损坏",
            "status": "pending"
        }
        event_data2 = {
            "title": "垃圾事件",
            "description": "垃圾问题",
            "event_type": "垃圾堆积",
            "status": "processing"
        }
        
        await async_client.post("/api/v1/events", json=event_data1, headers=auth_headers)
        await async_client.post("/api/v1/events", json=event_data2, headers=auth_headers)
        
        # 测试按事件类型过滤
        response = await async_client.get("/api/v1/events?event_type=道路损坏", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(event["event_type"] == "道路损坏" for event in data["data"])
        
        # 测试按状态过滤
        response = await async_client.get("/api/v1/events?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(event["status"] == "pending" for event in data["data"])
    
    @pytest.mark.asyncio
    async def test_get_event_detail_success(self, async_client: AsyncClient, test_event: Event, auth_headers):
        """测试获取事件详情成功"""
        response = await async_client.get(f"/api/v1/events/{test_event.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_event.id)
        assert data["data"]["title"] == test_event.title
    
    @pytest.mark.asyncio
    async def test_get_event_detail_not_found(self, async_client: AsyncClient, auth_headers):
        """测试获取不存在事件详情"""
        from uuid import uuid4
        
        response = await async_client.get(f"/api/v1/events/{uuid4()}", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "事件不存在" in data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_update_event_success(self, async_client: AsyncClient, test_event: Event, auth_headers):
        """测试更新事件成功"""
        update_data = {
            "title": "更新后的标题",
            "description": "更新后的描述",
            "priority": "high"
        }
        
        response = await async_client.put(f"/api/v1/events/{test_event.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "更新后的标题"
        assert data["data"]["description"] == "更新后的描述"
    
    @pytest.mark.asyncio
    async def test_delete_event_success(self, async_client: AsyncClient, test_event: Event, auth_headers):
        """测试删除事件成功"""
        response = await async_client.delete(f"/api/v1/events/{test_event.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证事件已被删除
        get_response = await async_client.get(f"/api/v1/events/{test_event.id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_success(self, async_client: AsyncClient, test_event: Event, auth_headers):
        """测试获取事件时间线成功"""
        response = await async_client.get(f"/api/v1/events/{test_event.id}/timeline", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestFileAPIIntegration:
    """文件API集成测试"""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, async_client: AsyncClient, auth_headers, mock_oss_service):
        """测试文件上传成功"""
        # 创建测试文件
        file_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        
        files = {"file": ("test.png", BytesIO(file_content), "image/png")}
        data = {"folder": "test"}
        
        with patch('app.services.oss_service.oss_service', mock_oss_service):
            response = await async_client.post("/api/v1/files/upload", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["success"] is True
        assert "file_url" in response_data["data"]
        assert "file_key" in response_data["data"]
    
    @pytest.mark.asyncio
    async def test_upload_file_unauthorized(self, async_client: AsyncClient):
        """测试未授权文件上传"""
        file_content = b"test content"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        
        response = await async_client.post("/api/v1/files/upload", files=files)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_file_url_success(self, async_client: AsyncClient, auth_headers, mock_oss_service):
        """测试获取文件URL成功"""
        file_key = "test/file.png"
        
        with patch('app.services.oss_service.oss_service', mock_oss_service):
            response = await async_client.get(f"/api/v1/files/{file_key}/url", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "url" in data["data"]
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, async_client: AsyncClient, auth_headers, mock_oss_service):
        """测试删除文件成功"""
        file_key = "test/file.png"
        
        with patch('app.services.oss_service.oss_service', mock_oss_service):
            response = await async_client.delete(f"/api/v1/files/{file_key}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAIAPIIntegration:
    """AI识别API集成测试"""
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self, async_client: AsyncClient, auth_headers, mock_ai_service):
        """测试图像识别成功"""
        analyze_data = {
            "image_url": "https://example.com/test.jpg"
        }
        
        with patch('app.services.ai_service.ai_service', mock_ai_service):
            response = await async_client.post("/api/v1/ai/analyze-image", json=analyze_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event_type" in data["data"]
        assert "description" in data["data"]
        assert "confidence" in data["data"]
    
    @pytest.mark.asyncio
    async def test_analyze_video_success(self, async_client: AsyncClient, auth_headers, mock_ai_service):
        """测试视频识别成功"""
        analyze_data = {
            "video_url": "https://example.com/test.mp4"
        }
        
        with patch('app.services.ai_service.ai_service', mock_ai_service):
            response = await async_client.post("/api/v1/ai/analyze-video", json=analyze_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event_type" in data["data"]
        assert "description" in data["data"]
        assert "confidence" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_event_types_success(self, async_client: AsyncClient, auth_headers):
        """测试获取事件类型列表成功"""
        response = await async_client.get("/api/v1/ai/event-types", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0


class TestHealthCheckIntegration:
    """健康检查集成测试"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        """测试根路径端点"""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, async_client: AsyncClient):
        """测试健康检查端点"""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data


class TestErrorHandlingIntegration:
    """错误处理集成测试"""
    
    @pytest.mark.asyncio
    async def test_404_error(self, async_client: AsyncClient):
        """测试404错误处理"""
        response = await async_client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_validation_error(self, async_client: AsyncClient, auth_headers):
        """测试数据验证错误"""
        invalid_data = {
            "title": "",  # 空标题
            "event_type": "invalid_type"  # 无效类型
        }
        
        response = await async_client.post("/api/v1/events", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, async_client: AsyncClient):
        """测试认证错误"""
        response = await async_client.get("/api/v1/users/profile")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestPaginationIntegration:
    """分页集成测试"""
    
    @pytest.mark.asyncio
    async def test_events_pagination(self, async_client: AsyncClient, test_user: User, auth_headers):
        """测试事件列表分页"""
        # 创建多个事件
        for i in range(5):
            event_data = {
                "title": f"事件 {i+1}",
                "description": f"第 {i+1} 个事件",
                "event_type": "道路损坏"
            }
            await async_client.post("/api/v1/events", json=event_data, headers=auth_headers)
        
        # 测试第一页
        response = await async_client.get("/api/v1/events?skip=0&limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        
        # 测试第二页
        response = await async_client.get("/api/v1/events?skip=3&limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2  # 至少有2个事件（包括test_event）


if __name__ == "__main__":
    pytest.main([__file__])