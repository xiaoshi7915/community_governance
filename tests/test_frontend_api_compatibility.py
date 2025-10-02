"""
前后端API兼容性测试
验证API接口与前端期望的数据格式和行为一致性
"""
import pytest
from httpx import AsyncClient
from app.main import app
from tests.conftest import test_user_data


class TestFrontendAPICompatibility:
    """前后端API兼容性测试类"""
    
    async def test_auth_api_compatibility(self):
        """测试认证API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试注册API响应格式
            register_data = {
                "phone": "13700137000",
                "password": "test123456",
                "name": "兼容性测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            data = response.json()
            # 验证响应格式符合前端期望
            assert "success" in data
            assert "data" in data
            assert "message" in data
            assert "timestamp" in data
            
            # 测试登录API响应格式
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            
            data = response.json()
            token_data = data["data"]
            # 验证token格式
            assert "access_token" in token_data
            assert "refresh_token" in token_data
            assert "token_type" in token_data
            assert "expires_in" in token_data
            assert token_data["token_type"] == "bearer"
    
    async def test_events_api_compatibility(self):
        """测试事件API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 先登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试创建事件API
            event_data = {
                "title": "前端兼容性测试事件",
                "description": "测试前端API兼容性",
                "event_type": "infrastructure",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区",
                "media_urls": []
            }
            response = await client.post("/api/v1/events", json=event_data, headers=headers)
            assert response.status_code == 200
            
            event_response = response.json()["data"]
            event_id = event_response["id"]
            
            # 验证事件响应格式符合前端期望
            required_fields = [
                "id", "title", "description", "event_type", "status",
                "location_lat", "location_lng", "location_address",
                "created_at", "updated_at", "user_id", "priority"
            ]
            for field in required_fields:
                assert field in event_response
            
            # 测试事件列表API
            response = await client.get("/api/v1/events", headers=headers)
            assert response.status_code == 200
            
            list_data = response.json()["data"]
            # 验证分页格式
            assert "items" in list_data
            assert "total" in list_data
            assert "page" in list_data
            assert "size" in list_data
            assert "pages" in list_data
            
            # 验证事件项格式
            if list_data["items"]:
                event_item = list_data["items"][0]
                for field in required_fields:
                    assert field in event_item
            
            # 测试事件详情API
            response = await client.get(f"/api/v1/events/{event_id}", headers=headers)
            assert response.status_code == 200
            
            detail_data = response.json()["data"]
            for field in required_fields:
                assert field in detail_data
            
            # 测试事件时间线API
            response = await client.get(f"/api/v1/events/{event_id}/timeline", headers=headers)
            assert response.status_code == 200
            
            timeline_data = response.json()["data"]
            assert isinstance(timeline_data, list)
            if timeline_data:
                timeline_item = timeline_data[0]
                timeline_fields = ["id", "event_id", "status", "description", "created_at"]
                for field in timeline_fields:
                    assert field in timeline_item
    
    async def test_user_profile_api_compatibility(self):
        """测试用户资料API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取用户资料
            response = await client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == 200
            
            profile_data = response.json()["data"]
            required_fields = ["id", "phone", "name", "avatar_url", "created_at", "updated_at"]
            for field in required_fields:
                assert field in profile_data
            
            # 测试更新用户资料
            update_data = {
                "name": "更新后的用户名",
                "avatar_url": "http://example.com/avatar.jpg"
            }
            response = await client.put("/api/v1/users/profile", json=update_data, headers=headers)
            assert response.status_code == 200
            
            updated_profile = response.json()["data"]
            assert updated_profile["name"] == "更新后的用户名"
            assert updated_profile["avatar_url"] == "http://example.com/avatar.jpg"
    
    async def test_file_upload_api_compatibility(self):
        """测试文件上传API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 模拟文件上传（使用测试文件）
            files = {
                "file": ("test.jpg", b"fake image content", "image/jpeg")
            }
            response = await client.post("/api/v1/files/upload", files=files, headers=headers)
            
            # 验证响应格式（即使上传失败，也要验证错误格式）
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "timestamp" in data
            
            if data["success"]:
                file_data = data["data"]
                required_fields = ["id", "filename", "file_url", "file_size", "content_type"]
                for field in required_fields:
                    assert field in file_data
    
    async def test_ai_analysis_api_compatibility(self):
        """测试AI分析API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试图像分析API
            analysis_data = {
                "image_url": "http://example.com/test.jpg"
            }
            response = await client.post("/api/v1/ai/analyze-image", json=analysis_data, headers=headers)
            
            # 验证响应格式
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "timestamp" in data
            
            if data["success"]:
                ai_result = data["data"]
                required_fields = ["event_type", "description", "confidence", "analysis_details"]
                for field in required_fields:
                    assert field in ai_result
            
            # 测试获取事件类型列表
            response = await client.get("/api/v1/ai/event-types", headers=headers)
            assert response.status_code == 200
            
            types_data = response.json()["data"]
            assert isinstance(types_data, list)
            if types_data:
                type_item = types_data[0]
                assert "code" in type_item
                assert "name" in type_item
                assert "description" in type_item
    
    async def test_statistics_api_compatibility(self):
        """测试统计API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试用户统计API
            response = await client.get("/api/v1/statistics/user", headers=headers)
            assert response.status_code == 200
            
            stats_data = response.json()["data"]
            required_fields = [
                "total_events", "pending_events", "processing_events", 
                "completed_events", "completion_rate", "avg_response_time"
            ]
            for field in required_fields:
                assert field in stats_data
            
            # 测试事件统计API
            response = await client.get("/api/v1/statistics/events", headers=headers)
            assert response.status_code == 200
            
            event_stats = response.json()["data"]
            assert "by_type" in event_stats
            assert "by_status" in event_stats
            assert "by_date" in event_stats
    
    async def test_notification_api_compatibility(self):
        """测试通知API兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取通知列表
            response = await client.get("/api/v1/notifications", headers=headers)
            assert response.status_code == 200
            
            notifications_data = response.json()["data"]
            assert "items" in notifications_data
            assert "total" in notifications_data
            assert "unread_count" in notifications_data
            
            # 测试通知偏好设置
            preferences_data = {
                "push_enabled": True,
                "email_enabled": False,
                "sms_enabled": True
            }
            response = await client.put("/api/v1/notifications/preferences", json=preferences_data, headers=headers)
            assert response.status_code == 200
    
    async def test_error_response_compatibility(self):
        """测试错误响应兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试认证错误
            response = await client.get("/api/v1/users/profile")
            assert response.status_code == 401
            
            error_data = response.json()
            assert "success" in error_data
            assert error_data["success"] is False
            assert "error" in error_data
            assert "timestamp" in error_data
            
            error_info = error_data["error"]
            assert "code" in error_info
            assert "message" in error_info
            
            # 测试参数验证错误
            invalid_data = {"invalid": "data"}
            response = await client.post("/api/v1/auth/register", json=invalid_data)
            assert response.status_code == 422
            
            validation_error = response.json()
            assert "success" in validation_error
            assert validation_error["success"] is False
            assert "error" in validation_error
            
            # 测试资源不存在错误
            response = await client.get("/api/v1/events/nonexistent-id")
            assert response.status_code == 404
            
            not_found_error = response.json()
            assert "success" in not_found_error
            assert not_found_error["success"] is False
    
    async def test_pagination_compatibility(self):
        """测试分页兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试事件列表分页
            response = await client.get("/api/v1/events?page=1&size=10", headers=headers)
            assert response.status_code == 200
            
            data = response.json()["data"]
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data
            assert "pages" in data
            assert data["page"] == 1
            assert data["size"] == 10
            
            # 测试通知列表分页
            response = await client.get("/api/v1/notifications?page=1&size=20", headers=headers)
            assert response.status_code == 200
            
            data = response.json()["data"]
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data
            assert data["page"] == 1
            assert data["size"] == 20
    
    async def test_filtering_compatibility(self):
        """测试筛选功能兼容性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 登录获取token
            login_data = {
                "phone": "13700137000",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试事件状态筛选
            response = await client.get("/api/v1/events?status=pending", headers=headers)
            assert response.status_code == 200
            
            # 测试事件类型筛选
            response = await client.get("/api/v1/events?event_type=infrastructure", headers=headers)
            assert response.status_code == 200
            
            # 测试日期范围筛选
            response = await client.get("/api/v1/events?start_date=2024-01-01&end_date=2024-12-31", headers=headers)
            assert response.status_code == 200
            
            # 验证筛选结果格式一致
            data = response.json()["data"]
            assert "items" in data
            assert "total" in data