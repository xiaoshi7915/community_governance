"""
系统监控模块
提供系统健康检查、性能监控、指标收集等功能
"""
import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import os

from app.core.logging import get_logger
from app.core.config import settings
from app.core.database import engine
from app.core.redis import get_redis
from sqlalchemy import text

logger = get_logger(__name__)


@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    active_connections: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class APIMetrics:
    """API性能指标数据类"""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    timestamp: datetime
    request_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class HealthStatus:
    """健康状态数据类"""
    service: str
    status: str  # healthy, unhealthy, degraded
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        if self.last_check:
            data['last_check'] = self.last_check.isoformat()
        return data


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.api_metrics: deque = deque(maxlen=max_metrics)
        self.error_counts: defaultdict = defaultdict(int)
        self.endpoint_stats: defaultdict = defaultdict(list)
        self.logger = get_logger(self.__class__.__name__)
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # 网络连接数
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                active_connections=connections
            )
            
            self.system_metrics.append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            raise
    
    def record_api_metrics(
        self, 
        endpoint: str, 
        method: str, 
        response_time: float, 
        status_code: int,
        request_id: str
    ):
        """记录API性能指标"""
        try:
            metrics = APIMetrics(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                timestamp=datetime.now(),
                request_id=request_id
            )
            
            self.api_metrics.append(metrics)
            
            # 更新端点统计
            endpoint_key = f"{method} {endpoint}"
            self.endpoint_stats[endpoint_key].append(response_time)
            
            # 保持最近100个请求的统计
            if len(self.endpoint_stats[endpoint_key]) > 100:
                self.endpoint_stats[endpoint_key] = self.endpoint_stats[endpoint_key][-100:]
            
            # 记录错误计数
            if status_code >= 400:
                error_key = f"{status_code}"
                self.error_counts[error_key] += 1
                
        except Exception as e:
            self.logger.error(f"记录API指标失败: {e}")
    
    def get_endpoint_statistics(self, endpoint: str, method: str) -> Dict[str, Any]:
        """获取端点统计信息"""
        endpoint_key = f"{method} {endpoint}"
        response_times = self.endpoint_stats.get(endpoint_key, [])
        
        if not response_times:
            return {
                "endpoint": endpoint,
                "method": method,
                "request_count": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "p95_response_time": 0
            }
        
        response_times_sorted = sorted(response_times)
        count = len(response_times)
        
        return {
            "endpoint": endpoint,
            "method": method,
            "request_count": count,
            "avg_response_time": sum(response_times) / count,
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": response_times_sorted[int(count * 0.95)] if count > 0 else 0
        }
    
    def get_recent_metrics(self, minutes: int = 10) -> Dict[str, Any]:
        """获取最近的指标数据"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # 过滤最近的系统指标
        recent_system = [
            m for m in self.system_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        # 过滤最近的API指标
        recent_api = [
            m for m in self.api_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        return {
            "system_metrics": [m.to_dict() for m in recent_system],
            "api_metrics": [m.to_dict() for m in recent_api],
            "error_counts": dict(self.error_counts),
            "time_range": {
                "start": cutoff_time.isoformat(),
                "end": datetime.now().isoformat()
            }
        }


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.health_status: Dict[str, HealthStatus] = {}
    
    async def check_database_health(self) -> HealthStatus:
        """检查数据库健康状态"""
        start_time = time.time()
        
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()
            
            response_time = time.time() - start_time
            status = HealthStatus(
                service="database",
                status="healthy",
                response_time=response_time,
                last_check=datetime.now()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                service="database",
                status="unhealthy",
                response_time=response_time,
                error_message=str(e),
                last_check=datetime.now()
            )
            self.logger.error(f"数据库健康检查失败: {e}")
        
        self.health_status["database"] = status
        return status
    
    async def check_redis_health(self) -> HealthStatus:
        """检查Redis健康状态"""
        start_time = time.time()
        
        try:
            redis = await get_redis()
            await redis.ping()
            
            response_time = time.time() - start_time
            status = HealthStatus(
                service="redis",
                status="healthy",
                response_time=response_time,
                last_check=datetime.now()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            status = HealthStatus(
                service="redis",
                status="unhealthy",
                response_time=response_time,
                error_message=str(e),
                last_check=datetime.now()
            )
            self.logger.error(f"Redis健康检查失败: {e}")
        
        self.health_status["redis"] = status
        return status
    
    async def check_external_services_health(self) -> Dict[str, HealthStatus]:
        """检查外部服务健康状态"""
        services = {}
        
        # 检查阿里云OSS（通过简单的连接测试）
        try:
            import oss2
            auth = oss2.Auth(settings.ALIYUN_OSS_ACCESS_KEY_ID, settings.ALIYUN_OSS_ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET_NAME)
            
            start_time = time.time()
            bucket.get_bucket_info()
            response_time = time.time() - start_time
            
            services["oss"] = HealthStatus(
                service="oss",
                status="healthy",
                response_time=response_time,
                last_check=datetime.now()
            )
            
        except Exception as e:
            services["oss"] = HealthStatus(
                service="oss",
                status="unhealthy",
                error_message=str(e),
                last_check=datetime.now()
            )
        
        # 检查AI服务（模拟检查）
        services["ai_service"] = HealthStatus(
            service="ai_service",
            status="healthy" if settings.ALIYUN_AI_API_KEY else "degraded",
            last_check=datetime.now()
        )
        
        return services
    
    async def perform_full_health_check(self) -> Dict[str, Any]:
        """执行完整的健康检查"""
        start_time = time.time()
        
        # 并发执行各项健康检查
        db_task = asyncio.create_task(self.check_database_health())
        redis_task = asyncio.create_task(self.check_redis_health())
        external_task = asyncio.create_task(self.check_external_services_health())
        
        # 等待所有检查完成
        db_status = await db_task
        redis_status = await redis_task
        external_services = await external_task
        
        # 收集系统指标
        metrics_collector = MetricsCollector()
        system_metrics = metrics_collector.collect_system_metrics()
        
        total_time = time.time() - start_time
        
        # 确定整体健康状态
        all_services = [db_status, redis_status] + list(external_services.values())
        overall_status = "healthy"
        
        for service in all_services:
            if service.status == "unhealthy":
                overall_status = "unhealthy"
                break
            elif service.status == "degraded":
                overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "check_duration": total_time,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status.to_dict(),
                "redis": redis_status.to_dict(),
                **{k: v.to_dict() for k, v in external_services.items()}
            },
            "system_metrics": system_metrics.to_dict()
        }


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 5.0,  # 秒
            "error_rate": 0.05  # 5%
        }
        self.alert_history: deque = deque(maxlen=100)
    
    async def check_system_alerts(self, metrics: SystemMetrics):
        """检查系统告警"""
        alerts = []
        
        # CPU使用率告警
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "system",
                "level": "warning",
                "message": f"CPU使用率过高: {metrics.cpu_percent:.1f}%",
                "threshold": self.alert_thresholds["cpu_percent"],
                "current_value": metrics.cpu_percent,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        # 内存使用率告警
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "system",
                "level": "warning",
                "message": f"内存使用率过高: {metrics.memory_percent:.1f}%",
                "threshold": self.alert_thresholds["memory_percent"],
                "current_value": metrics.memory_percent,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        # 磁盘使用率告警
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append({
                "type": "system",
                "level": "critical",
                "message": f"磁盘使用率过高: {metrics.disk_percent:.1f}%",
                "threshold": self.alert_thresholds["disk_percent"],
                "current_value": metrics.disk_percent,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        # 发送告警
        for alert in alerts:
            await self.send_alert(alert)
    
    async def check_api_alerts(self, metrics: APIMetrics):
        """检查API告警"""
        alerts = []
        
        # 响应时间告警
        if metrics.response_time > self.alert_thresholds["response_time"]:
            alerts.append({
                "type": "api",
                "level": "warning",
                "message": f"API响应时间过长: {metrics.endpoint} {metrics.response_time:.2f}s",
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "threshold": self.alert_thresholds["response_time"],
                "current_value": metrics.response_time,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        # HTTP错误告警
        if metrics.status_code >= 500:
            alerts.append({
                "type": "api",
                "level": "critical",
                "message": f"API服务器错误: {metrics.endpoint} {metrics.status_code}",
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "status_code": metrics.status_code,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        # 发送告警
        for alert in alerts:
            await self.send_alert(alert)
    
    async def send_alert(self, alert: Dict[str, Any]):
        """发送告警通知"""
        try:
            # 记录告警历史
            self.alert_history.append(alert)
            
            # 记录告警日志
            self.logger.warning(
                "系统告警",
                alert_type=alert["type"],
                alert_level=alert["level"],
                alert_message=alert["message"],
                alert_data=alert
            )
            
            # 这里可以集成实际的告警通知服务
            # 例如：发送邮件、短信、钉钉通知等
            # await self._send_email_alert(alert)
            # await self._send_sms_alert(alert)
            
        except Exception as e:
            self.logger.error(f"发送告警失败: {e}")
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取最近的告警记录"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_alerts = []
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time >= cutoff_time:
                recent_alerts.append(alert)
        
        return recent_alerts


# 创建全局实例
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_manager = AlertManager()