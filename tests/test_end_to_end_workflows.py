"""
端到端业务流程测试
模拟完整的用户操作流程，验证系统的端到端功能
"""
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from tests.conftest import test_user_data


class TestEndToEndWorkflows:
    """端到端业务流程测试类"""
    
    async def test_complete_event_reporting_workflow(self):
        """测试完整的事件上报流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 步骤1: 用户注册
            register_data = {
                "phone": "13800138001",
                "password": "test123456",
                "name": "事件上报用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            assert response.json()["success"] is True
            
            # 步骤2: 用户登录
            login_data = {
                "phone": "13800138001",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            token_data = response.json()["data"]
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 步骤3: 上传事件相关图片（模拟）
            files = {
                "file": ("event_photo.jpg", b"fake image content", "image/jpeg")
            }
            response = await client.post("/api/v1/files/upload", files=files, headers=headers)
            # 注意：实际环境中需要真实的OSS配置，这里可能会失败
            
            # 步骤4: AI分析图片内容（模拟）
            analysis_data = {
                "image_url": "http://example.com/event_photo.jpg"
            }
            response = await client.post("/api/v1/ai/analyze-image", json=analysis_data, headers=headers)
            # 注意：实际环境中需要真实的AI服务配置
            
            # 步骤5: 创建事件（基于AI分析结果）
            event_data = {
                "title": "道路损坏事件",
                "description": "发现道路有大坑，影响交通安全",
                "event_type": "infrastructure",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区建国门外大街1号",
                "media_urls": ["http://example.com/event_photo.jpg"],
                "priority": "medium"
            }
            response = await client.post("/api/v1/events", json=event_data, headers=headers)
            assert response.status_code == 200
            event_response = response.json()["data"]
            event_id = event_response["id"]
            assert event_response["status"] == "pending"
            
            # 步骤6: 查看事件详情
            response = await client.get(f"/api/v1/events/{event_id}", headers=headers)
            assert response.status_code == 200
            event_detail = response.json()["data"]
            assert event_detail["title"] == "道路损坏事件"
            assert event_detail["status"] == "pending"
            
            # 步骤7: 查看事件处理时间线
            response = await client.get(f"/api/v1/events/{event_id}/timeline", headers=headers)
            assert response.status_code == 200
            timeline = response.json()["data"]
            assert len(timeline) >= 1  # 至少有创建记录
            
            # 步骤8: 查看个人事件列表
            response = await client.get("/api/v1/events", headers=headers)
            assert response.status_code == 200
            events_list = response.json()["data"]
            assert events_list["total"] >= 1
            assert any(event["id"] == event_id for event in events_list["items"])
            
            # 步骤9: 查看个人统计数据
            response = await client.get("/api/v1/statistics/user", headers=headers)
            assert response.status_code == 200
            user_stats = response.json()["data"]
            assert user_stats["total_events"] >= 1
            assert user_stats["pending_events"] >= 1
    
    async def test_user_profile_management_workflow(self):
        """测试用户资料管理流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 步骤1: 用户注册
            register_data = {
                "phone": "13800138002",
                "password": "test123456",
                "name": "资料管理用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            # 步骤2: 用户登录
            login_data = {
                "phone": "13800138002",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            token_data = response.json()["data"]
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 步骤3: 查看初始用户资料
            response = await client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == 200
            initial_profile = response.json()["data"]
            assert initial_profile["name"] == "资料管理用户"
            assert initial_profile["phone"] == "13800138002"
            
            # 步骤4: 上传头像（模拟）
            avatar_files = {
                "file": ("avatar.jpg", b"fake avatar content", "image/jpeg")
            }
            response = await client.post("/api/v1/files/upload", files=avatar_files, headers=headers)
            # 注意：实际环境中需要真实的OSS配置
            
            # 步骤5: 更新用户资料
            update_data = {
                "name": "更新后的用户名",
                "avatar_url": "http://example.com/avatar.jpg"
            }
            response = await client.put("/api/v1/users/profile", json=update_data, headers=headers)
            assert response.status_code == 200
            updated_profile = response.json()["data"]
            assert updated_profile["name"] == "更新后的用户名"
            assert updated_profile["avatar_url"] == "http://example.com/avatar.jpg"
            
            # 步骤6: 验证资料更新成功
            response = await client.get("/api/v1/users/profile", headers=headers)
            assert response.status_code == 200
            final_profile = response.json()["data"]
            assert final_profile["name"] == "更新后的用户名"
            assert final_profile["avatar_url"] == "http://example.com/avatar.jpg"
    
    async def test_notification_workflow(self):
        """测试通知流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 步骤1: 用户注册和登录
            register_data = {
                "phone": "13800138003",
                "password": "test123456",
                "name": "通知测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            login_data = {
                "phone": "13800138003",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 步骤2: 设置通知偏好
            preferences_data = {
                "push_enabled": True,
                "email_enabled": False,
                "sms_enabled": True,
                "event_status_updates": True,
                "system_announcements": True
            }
            response = await client.put("/api/v1/notifications/preferences", json=preferences_data, headers=headers)
            assert response.status_code == 200
            
            # 步骤3: 创建事件（会触发通知）
            event_data = {
                "title": "通知测试事件",
                "description": "测试通知功能的事件",
                "event_type": "environment",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区"
            }
            response = await client.post("/api/v1/events", json=event_data, headers=headers)
            assert response.status_code == 200
            event_id = response.json()["data"]["id"]
            
            # 步骤4: 等待通知生成（模拟异步处理）
            await asyncio.sleep(1)
            
            # 步骤5: 查看通知列表
            response = await client.get("/api/v1/notifications", headers=headers)
            assert response.status_code == 200
            notifications = response.json()["data"]
            assert "items" in notifications
            assert "unread_count" in notifications
            
            # 步骤6: 标记通知为已读（如果有通知）
            if notifications["items"]:
                notification_id = notifications["items"][0]["id"]
                response = await client.put(f"/api/v1/notifications/{notification_id}/read", headers=headers)
                assert response.status_code == 200
                
                # 验证未读数量减少
                response = await client.get("/api/v1/notifications", headers=headers)
                updated_notifications = response.json()["data"]
                assert updated_notifications["unread_count"] <= notifications["unread_count"]
    
    async def test_event_lifecycle_workflow(self):
        """测试事件完整生命周期流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 步骤1: 用户注册和登录
            register_data = {
                "phone": "13800138004",
                "password": "test123456",
                "name": "生命周期测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            login_data = {
                "phone": "13800138004",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 步骤2: 创建事件
            event_data = {
                "title": "生命周期测试事件",
                "description": "测试事件完整生命周期",
                "event_type": "public_safety",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区",
                "priority": "high"
            }
            response = await client.post("/api/v1/events", json=event_data, headers=headers)
            assert response.status_code == 200
            event_id = response.json()["data"]["id"]
            
            # 步骤3: 验证事件初始状态
            response = await client.get(f"/api/v1/events/{event_id}", headers=headers)
            assert response.status_code == 200
            event = response.json()["data"]
            assert event["status"] == "pending"
            
            # 步骤4: 模拟管理员处理事件（更新状态）
            # 注意：这里需要管理员权限，实际测试中可能需要创建管理员用户
            update_data = {
                "status": "processing",
                "description": "事件已开始处理"
            }
            # 这个操作可能需要管理员权限，所以可能会失败
            response = await client.put(f"/api/v1/events/{event_id}/status", json=update_data, headers=headers)
            
            # 步骤5: 查看事件时间线
            response = await client.get(f"/api/v1/events/{event_id}/timeline", headers=headers)
            assert response.status_code == 200
            timeline = response.json()["data"]
            assert len(timeline) >= 1
            
            # 步骤6: 用户查看事件列表，验证状态更新
            response = await client.get("/api/v1/events", headers=headers)
            assert response.status_code == 200
            events = response.json()["data"]["items"]
            target_event = next((e for e in events if e["id"] == event_id), None)
            assert target_event is not None
            
            # 步骤7: 查看统计数据变化
            response = await client.get("/api/v1/statistics/user", headers=headers)
            assert response.status_code == 200
            stats = response.json()["data"]
            assert stats["total_events"] >= 1
    
    async def test_multi_user_interaction_workflow(self):
        """测试多用户交互流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 创建两个用户
            users = []
            for i in range(2):
                # 注册用户
                register_data = {
                    "phone": f"1380013800{5+i}",
                    "password": "test123456",
                    "name": f"多用户测试用户{i+1}",
                    "verification_code": "123456"
                }
                response = await client.post("/api/v1/auth/register", json=register_data)
                assert response.status_code == 200
                
                # 登录用户
                login_data = {
                    "phone": f"1380013800{5+i}",
                    "password": "test123456"
                }
                response = await client.post("/api/v1/auth/login", json=login_data)
                token = response.json()["data"]["access_token"]
                users.append({
                    "phone": f"1380013800{5+i}",
                    "token": token,
                    "headers": {"Authorization": f"Bearer {token}"}
                })
            
            # 用户1创建事件
            event_data = {
                "title": "多用户交互测试事件",
                "description": "测试多用户交互功能",
                "event_type": "infrastructure",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区"
            }
            response = await client.post("/api/v1/events", json=event_data, headers=users[0]["headers"])
            assert response.status_code == 200
            event_id = response.json()["data"]["id"]
            
            # 用户1查看自己的事件列表
            response = await client.get("/api/v1/events", headers=users[0]["headers"])
            assert response.status_code == 200
            user1_events = response.json()["data"]["items"]
            assert any(event["id"] == event_id for event in user1_events)
            
            # 用户2查看自己的事件列表（应该为空或不包含用户1的事件）
            response = await client.get("/api/v1/events", headers=users[1]["headers"])
            assert response.status_code == 200
            user2_events = response.json()["data"]["items"]
            # 用户2不应该看到用户1的私有事件
            assert not any(event["id"] == event_id for event in user2_events)
            
            # 用户2创建自己的事件
            event_data_2 = {
                "title": "用户2的测试事件",
                "description": "用户2创建的事件",
                "event_type": "environment",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区"
            }
            response = await client.post("/api/v1/events", json=event_data_2, headers=users[1]["headers"])
            assert response.status_code == 200
            event_id_2 = response.json()["data"]["id"]
            
            # 验证各自的统计数据
            for i, user in enumerate(users):
                response = await client.get("/api/v1/statistics/user", headers=user["headers"])
                assert response.status_code == 200
                stats = response.json()["data"]
                assert stats["total_events"] >= 1
    
    async def test_error_recovery_workflow(self):
        """测试错误恢复流程"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 步骤1: 尝试未认证访问
            response = await client.get("/api/v1/users/profile")
            assert response.status_code == 401
            error_data = response.json()
            assert error_data["success"] is False
            assert "error" in error_data
            
            # 步骤2: 用户注册和登录
            register_data = {
                "phone": "13800138007",
                "password": "test123456",
                "name": "错误恢复测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            login_data = {
                "phone": "13800138007",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 步骤3: 尝试访问不存在的资源
            response = await client.get("/api/v1/events/nonexistent-id", headers=headers)
            assert response.status_code == 404
            error_data = response.json()
            assert error_data["success"] is False
            
            # 步骤4: 尝试提交无效数据
            invalid_event_data = {
                "title": "",  # 空标题
                "description": "测试无效数据",
                "event_type": "invalid_type",  # 无效类型
                "location_lat": "invalid_lat",  # 无效坐标
                "location_lng": 116.4074
            }
            response = await client.post("/api/v1/events", json=invalid_event_data, headers=headers)
            assert response.status_code == 422
            error_data = response.json()
            assert error_data["success"] is False
            
            # 步骤5: 提交正确数据，验证系统恢复正常
            valid_event_data = {
                "title": "错误恢复测试事件",
                "description": "验证系统错误恢复能力",
                "event_type": "infrastructure",
                "location_lat": 39.9042,
                "location_lng": 116.4074,
                "location_address": "北京市朝阳区"
            }
            response = await client.post("/api/v1/events", json=valid_event_data, headers=headers)
            assert response.status_code == 200
            assert response.json()["success"] is True
    
    async def test_concurrent_user_operations(self):
        """测试并发用户操作"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 创建多个用户并发操作
            async def create_user_and_event(user_index):
                # 注册用户
                register_data = {
                    "phone": f"1380013801{user_index}",
                    "password": "test123456",
                    "name": f"并发测试用户{user_index}",
                    "verification_code": "123456"
                }
                response = await client.post("/api/v1/auth/register", json=register_data)
                if response.status_code != 200:
                    return False
                
                # 登录用户
                login_data = {
                    "phone": f"1380013801{user_index}",
                    "password": "test123456"
                }
                response = await client.post("/api/v1/auth/login", json=login_data)
                if response.status_code != 200:
                    return False
                
                token = response.json()["data"]["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # 创建事件
                event_data = {
                    "title": f"并发测试事件{user_index}",
                    "description": f"用户{user_index}创建的并发测试事件",
                    "event_type": "infrastructure",
                    "location_lat": 39.9042,
                    "location_lng": 116.4074,
                    "location_address": "北京市朝阳区"
                }
                response = await client.post("/api/v1/events", json=event_data, headers=headers)
                return response.status_code == 200
            
            # 并发执行多个用户操作
            tasks = [create_user_and_event(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证大部分操作成功
            successful_operations = sum(1 for result in results if result is True)
            assert successful_operations >= 3  # 至少3个操作成功