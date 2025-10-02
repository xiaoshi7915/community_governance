#!/usr/bin/env python3
"""
权限测试脚本
测试不同角色的权限控制
"""
import requests
import json
from typing import Dict, List

BASE_URL = "http://localhost:8000"

# 测试账号
TEST_ACCOUNTS = {
    "citizen": {"phone": "13800138001", "password": "citizen123", "name": "张小民"},
    "grid_worker": {"phone": "13800138002", "password": "grid123", "name": "李网格"},
    "manager": {"phone": "13800138003", "password": "manager123", "name": "王管理"},
    "decision_maker": {"phone": "13800138004", "password": "decision123", "name": "赵决策"}
}

class PermissionTester:
    def __init__(self):
        self.tokens = {}
        self.results = []
    
    def login(self, role: str) -> bool:
        """登录获取token"""
        account = TEST_ACCOUNTS[role]
        login_data = {
            "phone": account["phone"],
            "password": account["password"]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data["access_token"]
                print(f"✅ {role} ({account['name']}) 登录成功")
                return True
            else:
                print(f"❌ {role} 登录失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {role} 登录异常: {e}")
            return False
    
    def test_api_access(self, role: str, endpoint: str, method: str = "GET", data: dict = None) -> Dict:
        """测试API访问权限"""
        if role not in self.tokens:
            return {"success": False, "error": "未登录"}
        
        headers = {"Authorization": f"Bearer {self.tokens[role]}"}
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_role_permissions(self, role: str):
        """测试角色权限"""
        print(f"\n🔍 测试 {role.upper()} 角色权限")
        print("=" * 50)
        
        # 定义测试用例
        test_cases = [
            # 基础功能
            {"name": "个人信息", "endpoint": "/api/v1/users/profile", "method": "GET"},
            {"name": "事件列表", "endpoint": "/api/v1/events/", "method": "GET"},
            {"name": "通知列表", "endpoint": "/api/v1/notifications/", "method": "GET"},
            
            # 文件上传
            {"name": "文件上传", "endpoint": "/api/v1/files/upload", "method": "POST", "skip": True},  # 需要特殊处理
            
            # 统计功能
            {"name": "统计数据", "endpoint": "/api/v1/statistics/user", "method": "GET"},
            
            # 管理功能
            {"name": "管理面板", "endpoint": "/api/v1/admin/tasks/status", "method": "GET"},
        ]
        
        results = []
        for test_case in test_cases:
            if test_case.get("skip"):
                continue
                
            result = self.test_api_access(
                role, 
                test_case["endpoint"], 
                test_case["method"], 
                test_case.get("data")
            )
            
            status = "✅" if result["success"] else "❌"
            status_code = result.get("status_code", "N/A")
            
            print(f"{status} {test_case['name']}: {status_code}")
            
            if not result["success"] and status_code == 403:
                print(f"   权限不足 (符合预期)")
            elif not result["success"] and status_code != 403:
                print(f"   错误: {result.get('error', 'Unknown')}")
            
            results.append({
                "role": role,
                "test": test_case["name"],
                "success": result["success"],
                "status_code": status_code
            })
        
        return results
    
    def run_comprehensive_test(self):
        """运行全面权限测试"""
        print("🚀 开始权限控制测试")
        print("=" * 60)
        
        all_results = []
        
        for role in TEST_ACCOUNTS.keys():
            if self.login(role):
                results = self.test_role_permissions(role)
                all_results.extend(results)
        
        # 生成测试报告
        self.generate_report(all_results)
    
    def generate_report(self, results: List[Dict]):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📋 权限测试报告")
        print("=" * 60)
        
        # 按角色分组
        by_role = {}
        for result in results:
            role = result["role"]
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(result)
        
        # 显示每个角色的测试结果
        for role, role_results in by_role.items():
            account = TEST_ACCOUNTS[role]
            success_count = sum(1 for r in role_results if r["success"])
            total_count = len(role_results)
            
            print(f"\n🔐 {role.upper()} ({account['name']})")
            print(f"   成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
            
            for result in role_results:
                status = "✅" if result["success"] else "❌"
                print(f"   {status} {result['test']}: {result['status_code']}")
        
        # 总体统计
        total_tests = len(results)
        total_success = sum(1 for r in results if r["success"])
        
        print(f"\n📊 总体统计")
        print(f"   总测试数: {total_tests}")
        print(f"   成功数: {total_success}")
        print(f"   成功率: {total_success/total_tests*100:.1f}%")
        
        print("\n🎯 权限测试完成！")

def main():
    tester = PermissionTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
