"""
性能和负载测试
测试系统在高负载下的性能表现和稳定性
"""
import pytest
import asyncio
import time
import statistics
from httpx import AsyncClient
from app.main import app
from concurrent.futures import ThreadPoolExecutor


class TestPerformanceLoad:
    """性能和负载测试类"""
    
    async def test_api_response_time(self):
        """测试API响应时间"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试健康检查端点响应时间
            response_times = []
            for _ in range(50):
                start_time = time.time()
                response = await client.get("/health")
                end_time = time.time()
                
                assert response.status_code == 200
                response_times.append(end_time - start_time)
            
            # 分析响应时间
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"健康检查API响应时间统计:")
            print(f"平均响应时间: {avg_time:.3f}s")
            print(f"最大响应时间: {max_time:.3f}s")
            print(f"最小响应时间: {min_time:.3f}s")
            
            # 断言响应时间在合理范围内
            assert avg_time < 0.1  # 平均响应时间小于100ms
            assert max_time < 0.5  # 最大响应时间小于500ms
    
    async def test_concurrent_requests(self):
        """测试并发请求处理能力"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 创建并发请求
            async def make_request():
                response = await client.get("/health")
                return response.status_code == 200
            
            # 执行100个并发请求
            tasks = [make_request() for _ in range(100)]
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # 分析结果
            successful_requests = sum(results)
            total_time = end_time - start_time
            requests_per_second = len(tasks) / total_time
            
            print(f"并发请求测试结果:")
            print(f"总请求数: {len(tasks)}")
            print(f"成功请求数: {successful_requests}")
            print(f"总耗时: {total_time:.3f}s")
            print(f"每秒请求数: {requests_per_second:.2f}")
            
            # 断言大部分请求成功
            assert successful_requests >= len(tasks) * 0.95  # 95%成功率
            assert requests_per_second > 50  # 每秒至少50个请求
    
    async def test_authentication_performance(self):
        """测试认证性能"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 先注册一个用户
            register_data = {
                "phone": "13800138100",
                "password": "test123456",
                "name": "性能测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            # 测试登录性能
            login_data = {
                "phone": "13800138100",
                "password": "test123456"
            }
            
            login_times = []
            for _ in range(20):
                start_time = time.time()
                response = await client.post("/api/v1/auth/login", json=login_data)
                end_time = time.time()
                
                assert response.status_code == 200
                login_times.append(end_time - start_time)
            
            avg_login_time = statistics.mean(login_times)
            print(f"登录平均响应时间: {avg_login_time:.3f}s")
            
            # 断言登录响应时间合理
            assert avg_login_time < 0.2  # 平均登录时间小于200ms
    
    async def test_database_query_performance(self):
        """测试数据库查询性能"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 注册并登录用户
            register_data = {
                "phone": "13800138101",
                "password": "test123456",
                "name": "数据库性能测试用户",
                "verification_code": "123456"
            }
            response = await client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 200
            
            login_data = {
                "phone": "13800138101",
                "password": "test123456"
            }
            response = await client.post("/api/v1/auth/login", json=login_data)
            token = response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 创建一些测试事件
            for i in range(10):
                event_data = {
                    "title": f"性能测试事件{i}",
                    "description": f"第{i}个性能测试事件",
                    "event_type": "infrastructure",
                    "location_lat": 39.9042 + i * 0.001,
                    "location_lng": 116.4074 + i * 0.001,
                    "location_address": f"北京市朝阳区测试地址{i}"
                }
                response = await client.post("/api/v1/events", json=event_data, headers=headers)
                assert response.status_code == 200
            
            # 测试事件列表查询性能
            query_times = []
            for _ in range(30):
                start_time = time.time()
                response = await client.get("/api/v1/events", headers=headers)
                end_time = time.time()
                
                assert response.status_code == 200
                query_times.append(end_time - start_time)
            
            avg_query_time = statistics.mean(query_times)
            print(f"事件列表查询平均响应时间: {avg_query_time:.3f}s")
            
            # 断言查询响应时间合理
            assert avg_query_time < 0.15  # 平均查询时间小于150ms
    
    async def test_memory_usage_stability(self):
        """测试内存使用稳定性"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 执行大量操作
            for i in range(100):
                # 健康检查
                await client.get("/health")
                
                # 每10次检查一次内存
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory
                    
                    print(f"第{i}次操作后内存使用: {current_memory:.2f}MB (增长: {memory_increase:.2f}MB)")
                    
                    # 断言内存增长不超过50MB
                    assert memory_increase < 50
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        print(f"测试完成后总内存增长: {total_increase:.2f}MB")
        
        # 断言总内存增长合理
        assert total_increase < 100  # 总增长不超过100MB
    
    async def test_concurrent_user_operations(self):
        """测试并发用户操作性能"""
        async def simulate_user_session(user_id):
            async with AsyncClient(app=app, base_url="http://test") as client:
                try:
                    # 注册用户
                    register_data = {
                        "phone": f"138001381{user_id:02d}",
                        "password": "test123456",
                        "name": f"并发用户{user_id}",
                        "verification_code": "123456"
                    }
                    response = await client.post("/api/v1/auth/register", json=register_data)
                    if response.status_code != 200:
                        return False
                    
                    # 登录用户
                    login_data = {
                        "phone": f"138001381{user_id:02d}",
                        "password": "test123456"
                    }
                    response = await client.post("/api/v1/auth/login", json=login_data)
                    if response.status_code != 200:
                        return False
                    
                    token = response.json()["data"]["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # 创建事件
                    event_data = {
                        "title": f"并发用户{user_id}的事件",
                        "description": f"用户{user_id}创建的测试事件",
                        "event_type": "infrastructure",
                        "location_lat": 39.9042,
                        "location_lng": 116.4074,
                        "location_address": "北京市朝阳区"
                    }
                    response = await client.post("/api/v1/events", json=event_data, headers=headers)
                    if response.status_code != 200:
                        return False
                    
                    # 查询事件列表
                    response = await client.get("/api/v1/events", headers=headers)
                    if response.status_code != 200:
                        return False
                    
                    # 查询用户统计
                    response = await client.get("/api/v1/statistics/user", headers=headers)
                    if response.status_code != 200:
                        return False
                    
                    return True
                except Exception as e:
                    print(f"用户{user_id}操作失败: {e}")
                    return False
        
        # 模拟20个并发用户
        start_time = time.time()
        tasks = [simulate_user_session(i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 分析结果
        successful_users = sum(1 for result in results if result is True)
        total_time = end_time - start_time
        
        print(f"并发用户操作测试结果:")
        print(f"总用户数: {len(tasks)}")
        print(f"成功用户数: {successful_users}")
        print(f"总耗时: {total_time:.3f}s")
        print(f"成功率: {successful_users/len(tasks)*100:.1f}%")
        
        # 断言大部分用户操作成功
        assert successful_users >= len(tasks) * 0.8  # 80%成功率
        assert total_time < 30  # 总时间不超过30秒
    
    async def test_api_rate_limiting(self):
        """测试API限流功能"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 快速发送大量请求测试限流
            responses = []
            for _ in range(200):  # 发送200个请求
                response = await client.get("/health")
                responses.append(response.status_code)
            
            # 分析响应状态码
            success_count = sum(1 for code in responses if code == 200)
            rate_limited_count = sum(1 for code in responses if code == 429)
            
            print(f"限流测试结果:")
            print(f"成功请求: {success_count}")
            print(f"被限流请求: {rate_limited_count}")
            print(f"其他状态: {len(responses) - success_count - rate_limited_count}")
            
            # 验证限流机制工作（如果配置了限流）
            # 注意：这取决于实际的限流配置
            assert success_count > 0  # 至少有一些请求成功
    
    async def test_error_handling_performance(self):
        """测试错误处理性能"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 测试404错误处理性能
            error_times = []
            for _ in range(50):
                start_time = time.time()
                response = await client.get("/api/v1/nonexistent-endpoint")
                end_time = time.time()
                
                assert response.status_code == 404
                error_times.append(end_time - start_time)
            
            avg_error_time = statistics.mean(error_times)
            print(f"404错误处理平均响应时间: {avg_error_time:.3f}s")
            
            # 断言错误处理响应时间合理
            assert avg_error_time < 0.05  # 错误处理时间小于50ms
    
    @pytest.mark.skip(reason="需要长时间运行，仅在需要时执行")
    async def test_long_running_stability(self):
        """测试长时间运行稳定性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            error_count = 0
            request_count = 0
            
            # 运行5分钟
            while time.time() - start_time < 300:  # 5分钟
                try:
                    response = await client.get("/health")
                    if response.status_code != 200:
                        error_count += 1
                    request_count += 1
                    
                    # 每100个请求休息一下
                    if request_count % 100 == 0:
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    error_count += 1
                    print(f"请求异常: {e}")
                
                request_count += 1
            
            error_rate = error_count / request_count if request_count > 0 else 1
            print(f"长时间运行测试结果:")
            print(f"总请求数: {request_count}")
            print(f"错误数: {error_count}")
            print(f"错误率: {error_rate*100:.2f}%")
            
            # 断言错误率低于1%
            assert error_rate < 0.01