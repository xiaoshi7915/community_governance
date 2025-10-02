#!/usr/bin/env python3
"""
前端后端联调测试脚本
测试前端和后端的完整集成
"""
import requests
import json
import time
from typing import Dict, List

# 服务地址
BACKEND_URL = "http://115.190.152.96:8000"
FRONTEND_URL = "http://115.190.152.96:3002"

# 测试账号
TEST_ACCOUNTS = {
    "citizen": {"phone": "13800138001", "password": "citizen123", "name": "张小民"},
    "grid_worker": {"phone": "13800138002", "password": "grid123", "name": "李网格"},
    "manager": {"phone": "13800138003", "password": "manager123", "name": "王管理"},
    "decision_maker": {"phone": "13800138004", "password": "decision123", "name": "赵决策"}
}

class FrontendBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_backend_health(self):
        """测试后端健康状态"""
        print("\n🔍 测试后端服务健康状态...")
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("后端健康检查", True, f"状态: {data.get('status')}")
                return True
            else:
                self.log_test("后端健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("后端健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_frontend_accessibility(self):
        """测试前端服务可访问性"""
        print("\n🌐 测试前端服务可访问性...")
        try:
            response = self.session.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                self.log_test("前端服务访问", True, f"状态码: {response.status_code}")
                return True
            else:
                self.log_test("前端服务访问", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("前端服务访问", False, f"连接失败: {str(e)}")
            return False
    
    def test_cors_configuration(self):
        """测试CORS配置"""
        print("\n🔗 测试CORS配置...")
        try:
            headers = {
                "Origin": FRONTEND_URL,
                "Content-Type": "application/json"
            }
            response = self.session.options(f"{BACKEND_URL}/api/v1/auth/login", headers=headers, timeout=5)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }
            
            if any(cors_headers.values()):
                self.log_test("CORS配置", True, f"CORS头部存在")
                return True
            else:
                self.log_test("CORS配置", False, "缺少CORS头部")
                return False
        except Exception as e:
            self.log_test("CORS配置", False, f"测试失败: {str(e)}")
            return False
    
    def test_login_api(self, role: str):
        """测试登录API"""
        account = TEST_ACCOUNTS[role]
        print(f"\n🔐 测试 {role} 登录API...")
        
        try:
            headers = {
                "Origin": FRONTEND_URL,
                "Content-Type": "application/json"
            }
            
            login_data = {
                "phone": account["phone"],
                "password": account["password"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/login", 
                json=login_data, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token"):
                    self.tokens[role] = data["access_token"]
                    user = data.get("user", {})
                    self.log_test(f"{role}登录API", True, f"用户: {user.get('name')} ({user.get('role')})")
                    return True
                else:
                    self.log_test(f"{role}登录API", False, "响应中缺少access_token")
                    return False
            else:
                self.log_test(f"{role}登录API", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"{role}登录API", False, f"请求失败: {str(e)}")
            return False
    
    def test_authenticated_api(self, role: str):
        """测试需要认证的API"""
        if role not in self.tokens:
            self.log_test(f"{role}认证API", False, "缺少认证令牌")
            return False
        
        print(f"\n👤 测试 {role} 认证API...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.tokens[role]}",
                "Origin": FRONTEND_URL,
                "Content-Type": "application/json"
            }
            
            # 测试用户信息API
            response = self.session.get(
                f"{BACKEND_URL}/api/v1/users/profile", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("name"):
                    self.log_test(f"{role}用户信息API", True, f"姓名: {data.get('name')}")
                    return True
                else:
                    self.log_test(f"{role}用户信息API", False, "响应格式错误")
                    return False
            else:
                self.log_test(f"{role}用户信息API", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"{role}用户信息API", False, f"请求失败: {str(e)}")
            return False
    
    def test_permission_control(self, role: str):
        """测试权限控制"""
        if role not in self.tokens:
            self.log_test(f"{role}权限控制", False, "缺少认证令牌")
            return
        
        print(f"\n🛡️ 测试 {role} 权限控制...")
        
        headers = {
            "Authorization": f"Bearer {self.tokens[role]}",
            "Origin": FRONTEND_URL,
            "Content-Type": "application/json"
        }
        
        # 权限测试用例
        permission_tests = [
            {"name": "统计数据", "endpoint": "/api/v1/statistics/user", "expected_roles": ["grid_worker", "manager", "decision_maker"]},
            {"name": "管理面板", "endpoint": "/api/v1/admin/tasks/status", "expected_roles": ["manager", "decision_maker"]},
        ]
        
        for test in permission_tests:
            try:
                response = self.session.get(
                    f"{BACKEND_URL}{test['endpoint']}", 
                    headers=headers,
                    timeout=10
                )
                
                should_have_access = role in test["expected_roles"]
                has_access = response.status_code < 400
                
                if should_have_access == has_access:
                    status = "有权限" if has_access else "无权限(符合预期)"
                    self.log_test(f"{role}-{test['name']}", True, status)
                else:
                    expected = "应有权限" if should_have_access else "应无权限"
                    actual = "有权限" if has_access else "无权限"
                    self.log_test(f"{role}-{test['name']}", False, f"{expected}但{actual}")
                    
            except Exception as e:
                self.log_test(f"{role}-{test['name']}", False, f"请求失败: {str(e)}")
    
    def test_frontend_api_integration(self):
        """测试前端API集成"""
        print("\n🔄 测试前端API集成...")
        
        # 这里可以添加更多前端特定的测试
        # 比如检查前端是否正确配置了API地址
        
        try:
            # 模拟前端发起的登录请求
            headers = {
                "Origin": FRONTEND_URL,
                "Content-Type": "application/json",
                "Referer": FRONTEND_URL
            }
            
            login_data = {
                "phone": "13800138001",
                "password": "citizen123"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/login", 
                json=login_data, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("前端API集成", True, "前端可以成功调用后端API")
                return True
            else:
                self.log_test("前端API集成", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("前端API集成", False, f"集成测试失败: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """运行全面的前后端联调测试"""
        print("🚀 开始前端后端联调测试")
        print("=" * 60)
        
        # 1. 基础服务测试
        backend_ok = self.test_backend_health()
        frontend_ok = self.test_frontend_accessibility()
        cors_ok = self.test_cors_configuration()
        
        if not backend_ok:
            print("\n❌ 后端服务不可用，停止测试")
            return
        
        # 2. API功能测试
        for role in TEST_ACCOUNTS.keys():
            login_ok = self.test_login_api(role)
            if login_ok:
                self.test_authenticated_api(role)
                self.test_permission_control(role)
        
        # 3. 前端集成测试
        self.test_frontend_api_integration()
        
        # 4. 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📋 前端后端联调测试报告")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results if result["success"])
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {successful_tests} ✅")
        print(f"失败: {total_tests - successful_tests} ❌")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        
        # 显示失败的测试
        failed_tests = [result for result in self.results if not result["success"]]
        if failed_tests:
            print(f"\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        # 显示访问信息
        print(f"\n🌐 服务访问信息:")
        print(f"  - 后端API: {BACKEND_URL}")
        print(f"  - 前端服务: {FRONTEND_URL}")
        print(f"  - 权限测试页面: {FRONTEND_URL}/#/permission-test")
        print(f"  - 登录测试工具: file://{__file__.replace('.py', '.html')}")
        
        print("\n🎯 联调测试完成！")

def main():
    tester = FrontendBackendTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
