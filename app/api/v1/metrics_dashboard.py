"""
指标仪表板API
提供系统指标可视化和实时监控数据
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json
import asyncio

from app.core.monitoring import metrics_collector, health_checker, alert_manager
from app.core.logging import get_logger
from app.core.response import ResponseFormatter
from app.core.auth_middleware import get_current_user
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


class DashboardData(BaseModel):
    """仪表板数据模型"""
    system_overview: Dict[str, Any]
    api_performance: Dict[str, Any]
    error_statistics: Dict[str, Any]
    health_status: Dict[str, Any]
    recent_alerts: List[Dict[str, Any]]
    timestamp: str


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = get_logger(self.__class__.__name__)
    
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
    
    async def broadcast(self, data: dict):
        """广播数据到所有连接"""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.warning(f"发送WebSocket消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)


# 创建连接管理器实例
connection_manager = ConnectionManager()


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user)
):
    """
    获取仪表板数据
    包含系统概览、API性能、错误统计等信息
    """
    try:
        # 获取系统指标
        recent_metrics = metrics_collector.get_recent_metrics(minutes=10)
        
        # 获取健康状态
        health_data = await health_checker.perform_full_health_check()
        
        # 获取最近告警
        recent_alerts = alert_manager.get_recent_alerts(minutes=60)
        
        # 构建系统概览
        system_overview = await _build_system_overview(recent_metrics)
        
        # 构建API性能数据
        api_performance = _build_api_performance_data(recent_metrics)
        
        # 构建错误统计
        error_statistics = _build_error_statistics(recent_metrics, recent_alerts)
        
        dashboard_data = {
            "system_overview": system_overview,
            "api_performance": api_performance,
            "error_statistics": error_statistics,
            "health_status": health_data,
            "recent_alerts": recent_alerts,
            "timestamp": datetime.now().isoformat()
        }
        
        return ResponseFormatter.success(
            data=dashboard_data,
            message="获取仪表板数据成功"
        )
        
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取仪表板数据失败"
        )


@router.get("/dashboard/realtime-metrics")
async def get_realtime_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    获取实时指标数据
    用于仪表板实时更新
    """
    try:
        # 收集当前系统指标
        current_metrics = metrics_collector.collect_system_metrics()
        
        # 获取最近API指标
        recent_api_metrics = list(metrics_collector.api_metrics)[-10:]  # 最近10个请求
        
        # 构建实时数据
        realtime_data = {
            "system_metrics": current_metrics.to_dict(),
            "recent_api_calls": [m.to_dict() for m in recent_api_metrics],
            "active_connections": len(connection_manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }
        
        return ResponseFormatter.success(
            data=realtime_data,
            message="获取实时指标成功"
        )
        
    except Exception as e:
        logger.error(f"获取实时指标失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取实时指标失败"
        )


@router.get("/dashboard/performance-trends")
async def get_performance_trends(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(get_current_user)
):
    """
    获取性能趋势数据
    用于绘制性能趋势图表
    """
    try:
        # 获取指定时间范围的指标
        recent_metrics = metrics_collector.get_recent_metrics(minutes=hours * 60)
        
        # 按小时聚合数据
        hourly_data = _aggregate_metrics_by_hour(recent_metrics, hours)
        
        return ResponseFormatter.success(
            data=hourly_data,
            message=f"获取{hours}小时性能趋势数据"
        )
        
    except Exception as e:
        logger.error(f"获取性能趋势失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取性能趋势失败"
        )


@router.websocket("/dashboard/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点，用于实时推送监控数据
    """
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # 等待客户端消息（心跳检测）
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # 处理客户端请求
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "get_metrics":
                    # 发送当前指标
                    current_metrics = metrics_collector.collect_system_metrics()
                    await websocket.send_text(json.dumps({
                        "type": "metrics",
                        "data": current_metrics.to_dict()
                    }))
                    
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
        connection_manager.disconnect(websocket)


async def _build_system_overview(recent_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """构建系统概览数据"""
    system_metrics = recent_metrics.get("system_metrics", [])
    
    if not system_metrics:
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "active_connections": 0,
            "uptime": "0h 0m",
            "status": "unknown"
        }
    
    # 获取最新的系统指标
    latest_metrics = system_metrics[-1]
    
    # 计算系统运行时间（简化实现）
    uptime = "运行中"
    
    # 确定系统状态
    cpu_percent = latest_metrics.get("cpu_percent", 0)
    memory_percent = latest_metrics.get("memory_percent", 0)
    disk_percent = latest_metrics.get("disk_percent", 0)
    
    if cpu_percent > 80 or memory_percent > 85 or disk_percent > 90:
        status = "warning"
    elif cpu_percent > 90 or memory_percent > 95 or disk_percent > 95:
        status = "critical"
    else:
        status = "healthy"
    
    return {
        "cpu_usage": round(cpu_percent, 1),
        "memory_usage": round(memory_percent, 1),
        "disk_usage": round(disk_percent, 1),
        "active_connections": latest_metrics.get("active_connections", 0),
        "uptime": uptime,
        "status": status,
        "memory_used_mb": round(latest_metrics.get("memory_used_mb", 0), 1),
        "memory_available_mb": round(latest_metrics.get("memory_available_mb", 0), 1),
        "disk_used_gb": round(latest_metrics.get("disk_used_gb", 0), 1),
        "disk_free_gb": round(latest_metrics.get("disk_free_gb", 0), 1)
    }


def _build_api_performance_data(recent_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """构建API性能数据"""
    api_metrics = recent_metrics.get("api_metrics", [])
    
    if not api_metrics:
        return {
            "total_requests": 0,
            "avg_response_time": 0,
            "requests_per_minute": 0,
            "success_rate": 100,
            "top_endpoints": []
        }
    
    # 计算总请求数
    total_requests = len(api_metrics)
    
    # 计算平均响应时间
    response_times = [m.get("response_time", 0) for m in api_metrics]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # 计算每分钟请求数
    time_range_minutes = recent_metrics.get("time_range", {})
    start_time = time_range_minutes.get("start")
    end_time = time_range_minutes.get("end")
    
    if start_time and end_time:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration_minutes = (end_dt - start_dt).total_seconds() / 60
        requests_per_minute = total_requests / max(duration_minutes, 1)
    else:
        requests_per_minute = 0
    
    # 计算成功率
    success_count = sum(1 for m in api_metrics if m.get("status_code", 500) < 400)
    success_rate = (success_count / total_requests * 100) if total_requests > 0 else 100
    
    # 统计热门端点
    endpoint_counts = {}
    for metric in api_metrics:
        endpoint = f"{metric.get('method', 'GET')} {metric.get('endpoint', '/')}"
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
    
    top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_requests": total_requests,
        "avg_response_time": round(avg_response_time, 3),
        "requests_per_minute": round(requests_per_minute, 1),
        "success_rate": round(success_rate, 1),
        "top_endpoints": [{"endpoint": ep, "count": count} for ep, count in top_endpoints]
    }


def _build_error_statistics(recent_metrics: Dict[str, Any], recent_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构建错误统计数据"""
    api_metrics = recent_metrics.get("api_metrics", [])
    error_counts = recent_metrics.get("error_counts", {})
    
    # 统计HTTP错误
    http_errors = {}
    for metric in api_metrics:
        status_code = metric.get("status_code", 200)
        if status_code >= 400:
            error_key = f"{status_code // 100}xx"
            http_errors[error_key] = http_errors.get(error_key, 0) + 1
    
    # 统计告警级别
    alert_levels = {}
    for alert in recent_alerts:
        level = alert.get("level", "unknown")
        alert_levels[level] = alert_levels.get(level, 0) + 1
    
    # 计算错误率
    total_requests = len(api_metrics)
    total_errors = sum(1 for m in api_metrics if m.get("status_code", 200) >= 400)
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "error_rate": round(error_rate, 2),
        "total_errors": total_errors,
        "http_errors": http_errors,
        "alert_levels": alert_levels,
        "recent_error_count": len([a for a in recent_alerts if a.get("level") == "critical"])
    }


def _aggregate_metrics_by_hour(recent_metrics: Dict[str, Any], hours: int) -> Dict[str, Any]:
    """按小时聚合指标数据"""
    system_metrics = recent_metrics.get("system_metrics", [])
    api_metrics = recent_metrics.get("api_metrics", [])
    
    # 创建小时桶
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    hourly_buckets = {}
    current_hour = start_time.replace(minute=0, second=0, microsecond=0)
    
    while current_hour <= end_time:
        hour_key = current_hour.strftime('%Y-%m-%d %H:00')
        hourly_buckets[hour_key] = {
            "timestamp": current_hour.isoformat(),
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "request_count": 0,
            "avg_response_time": 0,
            "error_count": 0
        }
        current_hour += timedelta(hours=1)
    
    # 聚合系统指标
    for metric in system_metrics:
        timestamp_str = metric.get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                
                if hour_key in hourly_buckets:
                    hourly_buckets[hour_key]["cpu_usage"].append(metric.get("cpu_percent", 0))
                    hourly_buckets[hour_key]["memory_usage"].append(metric.get("memory_percent", 0))
                    hourly_buckets[hour_key]["disk_usage"].append(metric.get("disk_percent", 0))
            except:
                continue
    
    # 聚合API指标
    for metric in api_metrics:
        timestamp_str = metric.get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                
                if hour_key in hourly_buckets:
                    hourly_buckets[hour_key]["request_count"] += 1
                    
                    response_time = metric.get("response_time", 0)
                    current_avg = hourly_buckets[hour_key]["avg_response_time"]
                    count = hourly_buckets[hour_key]["request_count"]
                    
                    # 计算新的平均响应时间
                    new_avg = (current_avg * (count - 1) + response_time) / count
                    hourly_buckets[hour_key]["avg_response_time"] = new_avg
                    
                    # 统计错误
                    if metric.get("status_code", 200) >= 400:
                        hourly_buckets[hour_key]["error_count"] += 1
            except:
                continue
    
    # 计算每小时的平均值
    result = []
    for hour_key in sorted(hourly_buckets.keys()):
        bucket = hourly_buckets[hour_key]
        
        cpu_values = bucket["cpu_usage"]
        memory_values = bucket["memory_usage"]
        disk_values = bucket["disk_usage"]
        
        result.append({
            "timestamp": bucket["timestamp"],
            "hour": hour_key,
            "cpu_usage": round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else 0,
            "memory_usage": round(sum(memory_values) / len(memory_values), 1) if memory_values else 0,
            "disk_usage": round(sum(disk_values) / len(disk_values), 1) if disk_values else 0,
            "request_count": bucket["request_count"],
            "avg_response_time": round(bucket["avg_response_time"], 3),
            "error_count": bucket["error_count"]
        })
    
    return {
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        },
        "hourly_data": result
    }


# 后台任务：定期推送实时数据
async def broadcast_realtime_data():
    """定期广播实时数据到WebSocket客户端"""
    while True:
        try:
            if connection_manager.active_connections:
                # 收集当前指标
                current_metrics = metrics_collector.collect_system_metrics()
                
                # 构建广播数据
                broadcast_data = {
                    "type": "realtime_update",
                    "data": current_metrics.to_dict(),
                    "timestamp": datetime.now().isoformat()
                }
                
                # 广播到所有连接
                await connection_manager.broadcast(broadcast_data)
            
            # 等待30秒
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"广播实时数据失败: {e}")
            await asyncio.sleep(60)


# 启动后台任务
asyncio.create_task(broadcast_realtime_data())