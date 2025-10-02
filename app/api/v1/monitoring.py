"""
监控相关API端点
提供健康检查、系统指标、性能统计等接口
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from app.core.monitoring import health_checker, metrics_collector, alert_manager
from app.core.logging import get_logger
from app.core.response import ResponseFormatter
from app.core.auth_middleware import get_current_user
from app.models.user import User
from app.services.log_service import log_service, LogSearchFilter

logger = get_logger(__name__)
router = APIRouter()


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    overall_status: str
    check_duration: float
    timestamp: str
    services: Dict[str, Any]
    system_metrics: Dict[str, Any]


class SystemMetricsResponse(BaseModel):
    """系统指标响应模型"""
    system_metrics: List[Dict[str, Any]]
    api_metrics: List[Dict[str, Any]]
    error_counts: Dict[str, int]
    time_range: Dict[str, str]


class EndpointStatsResponse(BaseModel):
    """端点统计响应模型"""
    endpoint: str
    method: str
    request_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float


class AlertResponse(BaseModel):
    """告警响应模型"""
    alerts: List[Dict[str, Any]]
    total_count: int
    time_range: Dict[str, str]


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    系统健康检查端点
    返回系统各组件的健康状态和基本指标
    """
    try:
        health_data = await health_checker.perform_full_health_check()
        
        return ResponseFormatter.success(
            data=health_data,
            message="健康检查完成"
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=503,
            detail="健康检查服务不可用"
        )


@router.get("/health/simple")
async def simple_health_check():
    """
    简单健康检查端点
    快速返回服务状态，用于负载均衡器检查
    """
    return ResponseFormatter.success(
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "governance-backend"
        },
        message="服务运行正常"
    )


@router.get("/metrics/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    minutes: int = Query(10, ge=1, le=60, description="获取最近N分钟的指标数据"),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统指标数据
    需要管理员权限
    """
    try:
        metrics_data = metrics_collector.get_recent_metrics(minutes=minutes)
        
        return ResponseFormatter.success(
            data=metrics_data,
            message=f"获取最近{minutes}分钟的系统指标"
        )
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取系统指标失败"
        )


@router.get("/metrics/endpoints", response_model=List[EndpointStatsResponse])
async def get_endpoint_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    获取API端点性能统计
    需要管理员权限
    """
    try:
        # 获取所有端点的统计信息
        endpoint_stats = []
        
        # 从指标收集器获取端点列表
        for endpoint_key in metrics_collector.endpoint_stats.keys():
            method, endpoint = endpoint_key.split(' ', 1)
            stats = metrics_collector.get_endpoint_statistics(endpoint, method)
            endpoint_stats.append(stats)
        
        # 按请求数量排序
        endpoint_stats.sort(key=lambda x: x['request_count'], reverse=True)
        
        return ResponseFormatter.success(
            data=endpoint_stats,
            message="获取API端点统计信息"
        )
        
    except Exception as e:
        logger.error(f"获取端点统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取端点统计失败"
        )


@router.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    minutes: int = Query(60, ge=1, le=1440, description="获取最近N分钟的告警"),
    level: Optional[str] = Query(None, description="告警级别过滤"),
    alert_type: Optional[str] = Query(None, description="告警类型过滤"),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统告警信息
    需要管理员权限
    """
    try:
        alerts = alert_manager.get_recent_alerts(minutes=minutes)
        
        # 应用过滤条件
        if level:
            alerts = [alert for alert in alerts if alert.get('level') == level]
        
        if alert_type:
            alerts = [alert for alert in alerts if alert.get('type') == alert_type]
        
        # 按时间倒序排列
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return ResponseFormatter.success(
            data={
                "alerts": alerts,
                "total_count": len(alerts),
                "time_range": {
                    "start": (datetime.now() - timedelta(minutes=minutes)).isoformat(),
                    "end": datetime.now().isoformat()
                }
            },
            message=f"获取最近{minutes}分钟的告警信息"
        )
        
    except Exception as e:
        logger.error(f"获取告警信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取告警信息失败"
        )


@router.post("/metrics/collect")
async def trigger_metrics_collection(
    current_user: User = Depends(get_current_user)
):
    """
    手动触发指标收集
    需要管理员权限
    """
    try:
        # 收集系统指标
        system_metrics = metrics_collector.collect_system_metrics()
        
        # 检查系统告警
        await alert_manager.check_system_alerts(system_metrics)
        
        return ResponseFormatter.success(
            data=system_metrics.to_dict(),
            message="指标收集完成"
        )
        
    except Exception as e:
        logger.error(f"指标收集失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="指标收集失败"
        )


@router.get("/status/database")
async def check_database_status():
    """
    检查数据库连接状态
    """
    try:
        status = await health_checker.check_database_health()
        
        return ResponseFormatter.success(
            data=status.to_dict(),
            message="数据库状态检查完成"
        )
        
    except Exception as e:
        logger.error(f"数据库状态检查失败: {e}")
        raise HTTPException(
            status_code=503,
            detail="数据库连接异常"
        )


@router.get("/status/redis")
async def check_redis_status():
    """
    检查Redis连接状态
    """
    try:
        status = await health_checker.check_redis_health()
        
        return ResponseFormatter.success(
            data=status.to_dict(),
            message="Redis状态检查完成"
        )
        
    except Exception as e:
        logger.error(f"Redis状态检查失败: {e}")
        raise HTTPException(
            status_code=503,
            detail="Redis连接异常"
        )


@router.get("/status/external-services")
async def check_external_services_status():
    """
    检查外部服务状态
    """
    try:
        services_status = await health_checker.check_external_services_health()
        
        return ResponseFormatter.success(
            data={k: v.to_dict() for k, v in services_status.items()},
            message="外部服务状态检查完成"
        )
        
    except Exception as e:
        logger.error(f"外部服务状态检查失败: {e}")
        raise HTTPException(
            status_code=503,
            detail="外部服务检查异常"
        )


@router.get("/logs/search")
async def search_logs(
    query: str = Query(..., description="搜索关键词"),
    level: Optional[str] = Query(None, description="日志级别"),
    logger_name: Optional[str] = Query(None, description="记录器名称"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    request_id: Optional[str] = Query(None, description="请求ID"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user)
):
    """
    搜索和过滤日志
    需要管理员权限
    """
    try:
        # 构建搜索过滤器
        filter_params = LogSearchFilter(
            query=query,
            level=level,
            logger_name=logger_name,
            start_time=start_time,
            end_time=end_time,
            request_id=request_id,
            limit=limit,
            offset=offset
        )
        
        # 执行日志搜索
        log_entries, total_count = await log_service.search_logs(filter_params)
        
        # 转换为字典格式
        logs = [entry.to_dict() for entry in log_entries]
        
        return ResponseFormatter.success(
            data={
                "logs": logs,
                "total_count": total_count,
                "returned_count": len(logs),
                "search_params": {
                    "query": query,
                    "level": level,
                    "logger_name": logger_name,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "request_id": request_id,
                    "limit": limit,
                    "offset": offset
                }
            },
            message=f"搜索到{total_count}条日志记录，返回{len(logs)}条"
        )
        
    except Exception as e:
        logger.error(f"日志搜索失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="日志搜索失败"
        )


@router.get("/logs/statistics")
async def get_log_statistics(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    current_user: User = Depends(get_current_user)
):
    """
    获取日志统计信息
    需要管理员权限
    """
    try:
        statistics = await log_service.get_log_statistics(hours=hours)
        
        return ResponseFormatter.success(
            data=statistics,
            message=f"获取最近{hours}小时的日志统计"
        )
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取日志统计失败"
        )


@router.post("/logs/export")
async def export_logs(
    query: Optional[str] = Query(None, description="搜索关键词"),
    level: Optional[str] = Query(None, description="日志级别"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    format_type: str = Query("json", description="导出格式 (json/csv)"),
    limit: int = Query(10000, ge=1, le=50000, description="导出条数限制"),
    current_user: User = Depends(get_current_user)
):
    """
    导出日志数据
    需要管理员权限
    """
    try:
        # 构建搜索过滤器
        filter_params = LogSearchFilter(
            query=query,
            level=level,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # 导出日志
        export_path = await log_service.export_logs(filter_params, format_type)
        
        return ResponseFormatter.success(
            data={
                "export_path": export_path,
                "format": format_type,
                "export_params": {
                    "query": query,
                    "level": level,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "limit": limit
                }
            },
            message="日志导出完成"
        )
        
    except Exception as e:
        logger.error(f"日志导出失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="日志导出失败"
        )