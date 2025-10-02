#!/usr/bin/env python3
"""
基层治理智能体系统 - API接口全面测试脚本
测试所有API接口和不同角色的权限
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# API基础URL
BASE_URL = "http://localhost:8000"

# 测试账号
TEST_ACCOUNTS = {
    "citizen": {"phone": "13800138001", "password": "citizen123", "name": "张小民"},
    "grid_worker": {"phone": "13800138002", "password": "grid123", "name": "李网格"},
    "manager": {"phone": "13800138003", "password": "manager123", "name": "王管理"},
    "decision_maker": {"phone": "13800138004", "password": "decision123", "name": "赵决策"}
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """记录测试结果"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   详情: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def test_health_check(self):
        """测试健康检查接口"""
        print("\n🔍 测试健康检查接口...")
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("健康检查", True, f"服务状态: {data.get('data', {}).get('status', 'unknown')}")
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("健康检查", False, f"请求失败: {str(e)}")
    
    def test_login(self, role: str, account: Dict[str, str]) -> Optional[str]:
        """测试登录接口"""
        print(f"\n🔐 测试 {role} 角色登录...")
        try:
            login_data = {
                "phone": account["phone"],
                "password": account["password"]
            }
            
            response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                # 新的响应格式直接包含token信息
                if "access_token" in data:
                    token = data.get("access_token")
                    user_info = data.get("user", {})
                    self.tokens[role] = token
                    self.log_test(f"{role}登录", True, f"用户: {user_info.get('name')} ({user_info.get('role', 'unknown')})")
                    return token
                else:
                    self.log_test(f"{role}登录", False, "响应格式错误")
            else:
                self.log_test(f"{role}登录", False, f"状态码: {response.status_code}, 响应: {response.text}")
        except Exception as e:
            self.log_test(f"{role}登录", False, f"请求失败: {str(e)}")
        return None
    
    def test_user_profile(self, role: str, token: str):
        """测试用户信息接口"""
        print(f"\n👤 测试 {role} 用户信息...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{BASE_URL}/api/v1/users/profile", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # 新的响应格式直接包含用户信息
                if "name" in data:
                    self.log_test(f"{role}用户信息", True, f"姓名: {data.get('name')}, 角色: {data.get('role')}")
                else:
                    self.log_test(f"{role}用户信息", False, "响应格式错误")
            else:
                self.log_test(f"{role}用户信息", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test(f"{role}用户信息", False, f"请求失败: {str(e)}")
    
    def test_events_list(self, role: str, token: str):
        """测试事件列表接口"""
        print(f"\n📋 测试 {role} 事件列表...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{BASE_URL}/api/v1/events/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    events = data.get("data", {}).get("items", [])
                    self.log_test(f"{role}事件列表", True, f"获取到 {len(events)} 个事件")
                    
                    # 显示前3个事件的基本信息
                    for i, event in enumerate(events[:3]):
                        print(f"   事件{i+1}: {event.get('title')} ({event.get('event_type')}) - {event.get('status')}")
                else:
                    self.log_test(f"{role}事件列表", False, data.get("message"))
            else:
                self.log_test(f"{role}事件列表", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test(f"{role}事件列表", False, f"请求失败: {str(e)}")
    
    def test_create_event(self, role: str, token: str):
        """测试创建事件接口（仅市民和网格员）"""
        if role not in ["citizen", "grid_worker"]:
            return
            
        print(f"\n📝 测试 {role} 创建事件...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            event_data = {
                "title": f"测试事件-{role}",
                "description": f"这是{role}角色创建的测试事件",
                "event_type": "基础设施",
                "address": "测试地址123号",
                "latitude": 39.9042,
                "longitude": 116.4074,
                "priority": "MEDIUM"
            }
            
            response = self.session.post(f"{BASE_URL}/api/v1/events/", json=event_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    event = data.get("data", {})
                    self.log_test(f"{role}创建事件", True, f"事件ID: {event.get('id')}")
                else:
                    self.log_test(f"{role}创建事件", False, data.get("message"))
            else:
                self.log_test(f"{role}创建事件", False, f"状态码: {response.status_code}, 响应: {response.text}")
        except Exception as e:
            self.log_test(f"{role}创建事件", False, f"请求失败: {str(e)}")
    
    def test_notifications(self, role: str, token: str):
        """测试通知接口"""
        print(f"\n🔔 测试 {role} 通知列表...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{BASE_URL}/api/v1/notifications/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # 新的响应格式直接包含通知列表
                if "notifications" in data:
                    notifications = data.get("notifications", [])
                    self.log_test(f"{role}通知列表", True, f"获取到 {len(notifications)} 条通知")
                    
                    # 显示前3条通知
                    for i, notif in enumerate(notifications[:3]):
                        status = "已读" if notif.get("read_at") else "未读"
                        print(f"   通知{i+1}: {notif.get('title')} - {status}")
                else:
                    self.log_test(f"{role}通知列表", False, "响应格式错误")
            else:
                self.log_test(f"{role}通知列表", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test(f"{role}通知列表", False, f"请求失败: {str(e)}")
    
    def test_statistics(self, role: str, token: str):
        """测试统计接口（管理员和决策者）"""
        if role not in ["manager", "decision_maker"]:
            return
            
        print(f"\n📊 测试 {role} 统计数据...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(f"{BASE_URL}/api/v1/statistics/user", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stats = data.get("data", {})
                    self.log_test(f"{role}统计数据", True, f"获取统计数据成功")
                    print(f"   总事件数: {stats.get('total_events', 0)}")
                    print(f"   总用户数: {stats.get('total_users', 0)}")
                else:
                    self.log_test(f"{role}统计数据", False, data.get("message"))
            else:
                self.log_test(f"{role}统计数据", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test(f"{role}统计数据", False, f"请求失败: {str(e)}")
    
    def test_admin_functions(self, role: str, token: str):
        """测试管理员功能"""
        if role != "manager":
            return
            
        print(f"\n🛠️ 测试 {role} 管理员功能...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试用户列表
            response = self.session.get(f"{BASE_URL}/api/v1/admin/tasks/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    users = data.get("data", {}).get("items", [])
                    self.log_test(f"{role}用户管理", True, f"获取到 {len(users)} 个用户")
                else:
                    self.log_test(f"{role}用户管理", False, data.get("message"))
            else:
                self.log_test(f"{role}用户管理", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test(f"{role}管理员功能", False, f"请求失败: {str(e)}")
    
    def test_file_upload(self, role: str, token: str):
        """测试文件上传接口"""
        print(f"\n📁 测试 {role} 文件上传...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # 创建一个测试图片文件
            test_content = b"fake image content for testing"
            files = {"file": ("test.jpg", test_content, "image/jpeg")}
            
            response = self.session.post(f"{BASE_URL}/api/v1/files/upload", files=files, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # 新的响应格式直接包含文件信息
                if "file_key" in data or "id" in data:
                    file_id = data.get("id") or data.get("file_key")
                    self.log_test(f"{role}文件上传", True, f"文件ID: {file_id}")
                else:
                    self.log_test(f"{role}文件上传", False, "响应格式错误")
            else:
                self.log_test(f"{role}文件上传", False, f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test(f"{role}文件上传", False, f"请求失败: {str(e)}")
    
    def run_comprehensive_test(self):
        """运行全面测试"""
        print("🚀 开始基层治理智能体系统API全面测试")
        print("=" * 60)
        
        # 1. 测试健康检查
        self.test_health_check()
        
        # 2. 测试所有角色登录和功能
        for role, account in TEST_ACCOUNTS.items():
            print(f"\n{'='*20} 测试 {role.upper()} 角色 {'='*20}")
            
            # 登录
            token = self.test_login(role, account)
            if not token:
                continue
            
            # 基础功能测试
            self.test_user_profile(role, token)
            self.test_events_list(role, token)
            self.test_notifications(role, token)
            self.test_file_upload(role, token)
            
            # 角色特定功能测试
            self.test_create_event(role, token)
            self.test_statistics(role, token)
            self.test_admin_functions(role, token)
        
        # 3. 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📋 测试报告总结")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n🎯 测试完成！")

def main():
    """主函数"""
    tester = APITester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
