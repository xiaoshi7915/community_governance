"""
监控系统测试
测试系统监控、日志记录、性能监控等功能
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.core.monitoring import (
    MetricsCollector, 
    HealthChecker, 
    AlertManager,
    SystemMetrics,
    APIMetrics,
    HealthStatus
)
from app.services.log_service import LogService, LogSearchFilter, LogEntry
from app.core.performance_middleware import PerformanceMonitoringMiddleware


class TestMetricsCollector:
    """指标收集器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.collector = MetricsCollector(max_metrics=100)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_connections')
    def test_collect_system_metrics(self, mock_connections, mock_disk, mock_memory, mock_cpu):
        """测试系统指标收集"""
        # 模拟系统指标
        mock_cpu.return_value = 45.5
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.2
        mock_memory_obj.used = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory_obj.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.total = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk_obj.used = 50 * 1024 * 1024 * 1024   # 50GB
        mock_disk_obj.free = 50 * 1024 * 1024 * 1024   # 50GB
        mock_disk.return_value = mock_disk_obj
        
        mock_connections.return_value = [Mock() for _ in range(25)]
        
        # 收集指标
        metrics = self.collector.collect_system_metrics()
        
        # 验证结果
        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 60.2
        assert metrics.memory_used_mb == 8192.0
        assert metrics.memory_available_mb == 4096.0
        assert metrics.disk_percent == 50.0
        assert metrics.active_connections == 25
        
        # 验证指标被存储
        assert len(self.collector.system_metrics) == 1
    
    def test_record_api_metrics(self):
        """测试API指标记录"""
        # 记录API指标
        self.collector.record_api_metrics(
            endpoint="/api/v1/users",
            method="GET",
            response_time=0.125,
            status_code=200,
            request_id="test-request-123"
        )
        
        # 验证指标被记录
        assert len(self.collector.api_metrics) == 1
        
        api_metric = self.collector.api_metrics[0]
        assert api_metric.endpoint == "/api/v1/users"
        assert api_metric.method == "GET"
        assert api_metric.response_time == 0.125
        assert api_metric.status_code == 200
        assert api_metric.request_id == "test-request-123"
        
        # 验证端点统计
        endpoint_key = "GET /api/v1/users"
        assert endpoint_key in self.collector.endpoint_stats
        assert len(self.collector.endpoint_stats[endpoint_key]) == 1
    
    def test_get_endpoint_statistics(self):
        """测试端点统计获取"""
        # 记录多个请求
        response_times = [0.1, 0.2, 0.15, 0.3, 0.12]
        for i, rt in enumerate(response_times):
            self.collector.record_api_metrics(
                endpoint="/api/v1/test",
                method="POST",
                response_time=rt,
                status_code=200,
                request_id=f"req-{i}"
            )
        
        # 获取统计信息
        stats = self.collector.get_endpoint_statistics("/api/v1/test", "POST")
        
        # 验证统计结果
        assert stats["endpoint"] == "/api/v1/test"
        assert stats["method"] == "POST"
        assert stats["request_count"] == 5
        assert stats["avg_response_time"] == sum(response_times) / len(response_times)
        assert stats["min_response_time"] == min(response_times)
        assert stats["max_response_time"] == max(response_times)


class TestHealthChecker:
    """健康检查器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.health_checker = HealthChecker()
    
    @pytest.mark.asyncio
    @patch('app.core.database.engine')
    async def test_check_database_health_success(self, mock_engine):
        """测试数据库健康检查成功"""
        # 模拟数据库连接成功
        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_conn.execute.return_value = mock_result
        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        
        # 执行健康检查
        status = await self.health_checker.check_database_health()
        
        # 验证结果
        assert isinstance(status, HealthStatus)
        assert status.service == "database"
        assert status.status == "healthy"
        assert status.response_time is not None
        assert status.response_time > 0
        assert status.error_message is None
    
    @pytest.mark.asyncio
    @patch('app.core.database.engine')
    async def test_check_database_health_failure(self, mock_engine):
        """测试数据库健康检查失败"""
        # 模拟数据库连接失败
        mock_engine.begin.side_effect = Exception("Database connection failed")
        
        # 执行健康检查
        status = await self.health_checker.check_database_health()
        
        # 验证结果
        assert status.service == "database"
        assert status.status == "unhealthy"
        assert status.error_message == "Database connection failed"
    
    @pytest.mark.asyncio
    @patch('app.core.redis.get_redis')
    async def test_check_redis_health_success(self, mock_get_redis):
        """测试Redis健康检查成功"""
        # 模拟Redis连接成功
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_get_redis.return_value = mock_redis
        
        # 执行健康检查
        status = await self.health_checker.check_redis_health()
        
        # 验证结果
        assert status.service == "redis"
        assert status.status == "healthy"
        assert status.response_time is not None
        assert status.error_message is None


class TestAlertManager:
    """告警管理器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.alert_manager = AlertManager()
    
    @pytest.mark.asyncio
    async def test_check_system_alerts_cpu_warning(self):
        """测试CPU使用率告警"""
        # 创建高CPU使用率的系统指标
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # 超过阈值80%
            memory_percent=50.0,
            memory_used_mb=4096.0,
            memory_available_mb=4096.0,
            disk_percent=60.0,
            disk_used_gb=30.0,
            disk_free_gb=20.0,
            active_connections=10
        )
        
        # 检查告警
        await self.alert_manager.check_system_alerts(metrics)
        
        # 验证告警被记录
        assert len(self.alert_manager.alert_history) == 1
        
        alert = self.alert_manager.alert_history[0]
        assert alert["type"] == "system"
        assert alert["level"] == "warning"
        assert "CPU使用率过高" in alert["message"]
        assert alert["current_value"] == 85.0
    
    @pytest.mark.asyncio
    async def test_check_api_alerts_slow_response(self):
        """测试API响应时间告警"""
        # 创建慢响应的API指标
        api_metrics = APIMetrics(
            endpoint="/api/v1/slow",
            method="GET",
            response_time=6.0,  # 超过阈值5秒
            status_code=200,
            timestamp=datetime.now(),
            request_id="slow-request"
        )
        
        # 检查告警
        await self.alert_manager.check_api_alerts(api_metrics)
        
        # 验证告警被记录
        assert len(self.alert_manager.alert_history) == 1
        
        alert = self.alert_manager.alert_history[0]
        assert alert["type"] == "api"
        assert alert["level"] == "warning"
        assert "API响应时间过长" in alert["message"]
        assert alert["current_value"] == 6.0
    
    def test_get_recent_alerts(self):
        """测试获取最近告警"""
        # 添加一些测试告警
        now = datetime.now()
        
        # 最近的告警
        recent_alert = {
            "type": "system",
            "level": "warning",
            "message": "Recent alert",
            "timestamp": now.isoformat()
        }
        
        # 较早的告警
        old_alert = {
            "type": "api",
            "level": "critical",
            "message": "Old alert",
            "timestamp": (now - timedelta(hours=2)).isoformat()
        }
        
        self.alert_manager.alert_history.extend([recent_alert, old_alert])
        
        # 获取最近1小时的告警
        recent_alerts = self.alert_manager.get_recent_alerts(minutes=60)
        
        # 验证只返回最近的告警
        assert len(recent_alerts) == 1
        assert recent_alerts[0]["message"] == "Recent alert"


class TestLogService:
    """日志服务测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.log_service = LogService()
    
    def test_log_parser_json_format(self):
        """测试JSON格式日志解析"""
        json_log = '{"timestamp": "2024-01-01T12:00:00", "level": "INFO", "logger": "test", "message": "Test message", "request_id": "req-123"}'
        
        entry = self.log_service.parser.parse_log_line(json_log)
        
        assert entry is not None
        assert entry.level == "INFO"
        assert entry.logger_name == "test"
        assert entry.message == "Test message"
        assert entry.request_id == "req-123"
    
    def test_log_parser_standard_format(self):
        """测试标准格式日志解析"""
        standard_log = "2024-01-01T12:00:00.123 | INFO | test.module | Test message"
        
        entry = self.log_service.parser.parse_log_line(standard_log)
        
        assert entry is not None
        assert entry.level == "INFO"
        assert entry.logger_name == "test.module"
        assert entry.message == "Test message"
    
    def test_log_filter_matching(self):
        """测试日志过滤匹配"""
        # 创建测试日志条目
        entry = LogEntry(
            timestamp=datetime.now(),
            level="ERROR",
            logger_name="app.service",
            message="Database connection failed",
            request_id="req-456"
        )
        
        # 测试级别过滤
        filter_params = LogSearchFilter(level="ERROR")
        assert self.log_service._matches_filter(entry, filter_params)
        
        filter_params = LogSearchFilter(level="INFO")
        assert not self.log_service._matches_filter(entry, filter_params)
        
        # 测试关键词搜索
        filter_params = LogSearchFilter(query="database")
        assert self.log_service._matches_filter(entry, filter_params)
        
        filter_params = LogSearchFilter(query="network")
        assert not self.log_service._matches_filter(entry, filter_params)
        
        # 测试请求ID过滤
        filter_params = LogSearchFilter(request_id="req-456")
        assert self.log_service._matches_filter(entry, filter_params)
        
        filter_params = LogSearchFilter(request_id="req-789")
        assert not self.log_service._matches_filter(entry, filter_params)


@pytest.mark.asyncio
async def test_performance_middleware_integration():
    """测试性能监控中间件集成"""
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    
    # 创建测试应用
    app = FastAPI()
    app.add_middleware(PerformanceMonitoringMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        await asyncio.sleep(0.1)  # 模拟处理时间
        return {"message": "test"}
    
    # 创建测试客户端
    client = TestClient(app)
    
    # 发送测试请求
    response = client.get("/test")
    
    # 验证响应
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])