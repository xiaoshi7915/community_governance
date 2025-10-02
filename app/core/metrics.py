"""
性能指标收集和监控
提供详细的应用性能监控功能
"""
import time
import psutil
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from app.core.logging import get_logger
from app.core.cache import cache_manager

logger = get_logger(__name__)


@dataclass
class RequestMetric:
    """请求指标数据类"""
    method: str
    path: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SystemMetric:
    """系统指标数据类"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    timestamp: datetime


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.request_metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=1000)  # 系统指标保留较少
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'error_count': 0
        })
        self._lock = asyncio.Lock()
    
    async def record_request(self, metric: RequestMetric):
        """记录请求指标"""
        async with self._lock:
            self.request_metrics.append(metric)
            
            # 更新端点统计
            endpoint_key = f"{metric.method}:{metric.path}"
            stats = self.endpoint_stats[endpoint_key]
            stats['count'] += 1
            stats['total_time'] += metric.response_time
            stats['min_time'] = min(stats['min_time'], metric.response_time)
            stats['max_time'] = max(stats['max_time'], metric.response_time)
            
            if metric.status_code >= 400:
                stats['error_count'] += 1
                if metric.error:
                    self.error_counts[metric.error] += 1
    
    async def record_system_metric(self):
        """记录系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metric = SystemMetric(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_percent=disk.percent,
                timestamp=datetime.now(timezone.utc)
            )
            
            async with self._lock:
                self.system_metrics.append(metric)
                
        except Exception as e:
            logger.warning(f"系统指标收集失败: {e}")
    
    async def get_request_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """获取请求统计信息"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        async with self._lock:
            recent_metrics = [
                m for m in self.request_metrics 
                if m.timestamp > cutoff_time
            ]
        
        if not recent_metrics:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'requests_per_minute': 0
            }
        
        total_requests = len(recent_metrics)
        total_time = sum(m.response_time for m in recent_metrics)
        error_count = sum(1 for m in recent_metrics if m.status_code >= 400)
        
        return {
            'total_requests': total_requests,
            'avg_response_time': total_time / total_requests if total_requests > 0 else 0,
            'error_rate': error_count / total_requests if total_requests > 0 else 0,
            'requests_per_minute': total_requests / minutes,
            'status_codes': self._count_status_codes(recent_metrics),
            'slowest_endpoints': self._get_slowest_endpoints(recent_metrics)
        }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        async with self._lock:
            if not self.system_metrics:
                return {}
            
            latest = self.system_metrics[-1]
            return {
                'current': asdict(latest),
                'avg_cpu': sum(m.cpu_percent for m in self.system_metrics) / len(self.system_metrics),
                'avg_memory': sum(m.memory_percent for m in self.system_metrics) / len(self.system_metrics),
                'peak_memory': max(m.memory_used_mb for m in self.system_metrics),
            }
    
    async def get_endpoint_stats(self) -> Dict[str, Any]:
        """获取端点统计信息"""
        async with self._lock:
            stats = {}
            for endpoint, data in self.endpoint_stats.items():
                if data['count'] > 0:
                    stats[endpoint] = {
                        'count': data['count'],
                        'avg_time': data['total_time'] / data['count'],
                        'min_time': data['min_time'],
                        'max_time': data['max_time'],
                        'error_rate': data['error_count'] / data['count'],
                    }
            return stats
    
    async def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计信息"""
        async with self._lock:
            return dict(self.error_counts)
    
    def _count_status_codes(self, metrics: List[RequestMetric]) -> Dict[str, int]:
        """统计状态码分布"""
        counts = defaultdict(int)
        for metric in metrics:
            status_range = f"{metric.status_code // 100}xx"
            counts[status_range] += 1
        return dict(counts)
    
    def _get_slowest_endpoints(self, metrics: List[RequestMetric], limit: int = 5) -> List[Dict[str, Any]]:
        """获取最慢的端点"""
        endpoint_times = defaultdict(list)
        for metric in metrics:
            endpoint_key = f"{metric.method} {metric.path}"
            endpoint_times[endpoint_key].append(metric.response_time)
        
        avg_times = []
        for endpoint, times in endpoint_times.items():
            avg_time = sum(times) / len(times)
            avg_times.append({
                'endpoint': endpoint,
                'avg_time': avg_time,
                'count': len(times)
            })
        
        return sorted(avg_times, key=lambda x: x['avg_time'], reverse=True)[:limit]


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动性能监控"""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("性能监控已启动")
    
    async def stop(self):
        """停止性能监控"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("性能监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self.collector.record_system_metric()
                await asyncio.sleep(30)  # 每30秒收集一次系统指标
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(60)  # 出错后等待更长时间
    
    async def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """记录请求指标"""
        metric = RequestMetric(
            method=method,
            path=path,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            error=error
        )
        await self.collector.record_request(metric)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        request_stats = await self.collector.get_request_stats()
        system_stats = await self.collector.get_system_stats()
        endpoint_stats = await self.collector.get_endpoint_stats()
        error_stats = await self.collector.get_error_stats()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'requests': request_stats,
            'system': system_stats,
            'endpoints': endpoint_stats,
            'errors': error_stats
        }
    
    async def get_health_score(self) -> Dict[str, Any]:
        """计算健康评分"""
        request_stats = await self.collector.get_request_stats()
        system_stats = await self.collector.get_system_stats()
        
        # 计算各项评分 (0-100)
        scores = {}
        
        # 响应时间评分
        avg_response_time = request_stats.get('avg_response_time', 0)
        if avg_response_time < 0.1:
            scores['response_time'] = 100
        elif avg_response_time < 0.5:
            scores['response_time'] = 80
        elif avg_response_time < 1.0:
            scores['response_time'] = 60
        elif avg_response_time < 2.0:
            scores['response_time'] = 40
        else:
            scores['response_time'] = 20
        
        # 错误率评分
        error_rate = request_stats.get('error_rate', 0)
        if error_rate < 0.01:
            scores['error_rate'] = 100
        elif error_rate < 0.05:
            scores['error_rate'] = 80
        elif error_rate < 0.1:
            scores['error_rate'] = 60
        else:
            scores['error_rate'] = 40
        
        # 系统资源评分
        if system_stats:
            cpu_percent = system_stats.get('current', {}).get('cpu_percent', 0)
            memory_percent = system_stats.get('current', {}).get('memory_percent', 0)
            
            if cpu_percent < 50:
                scores['cpu'] = 100
            elif cpu_percent < 70:
                scores['cpu'] = 80
            elif cpu_percent < 85:
                scores['cpu'] = 60
            else:
                scores['cpu'] = 40
            
            if memory_percent < 60:
                scores['memory'] = 100
            elif memory_percent < 75:
                scores['memory'] = 80
            elif memory_percent < 90:
                scores['memory'] = 60
            else:
                scores['memory'] = 40
        else:
            scores['cpu'] = 100
            scores['memory'] = 100
        
        # 计算总体健康评分
        overall_score = sum(scores.values()) / len(scores)
        
        # 确定健康状态
        if overall_score >= 80:
            health_status = "excellent"
        elif overall_score >= 60:
            health_status = "good"
        elif overall_score >= 40:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            'overall_score': round(overall_score, 2),
            'health_status': health_status,
            'scores': scores,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# 创建全局性能监控器实例
performance_monitor = PerformanceMonitor()
