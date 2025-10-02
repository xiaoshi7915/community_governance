"""
监控指标API端点
提供系统性能和健康状况的查询接口
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from app.core.metrics import performance_monitor
from app.core.response import create_response
from app.core.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/monitoring", tags=["监控指标"])


@router.get("/metrics", summary="获取系统指标", description="获取系统性能指标摘要")
async def get_metrics(
    current_user: User = Depends(get_current_user)
):
    """获取系统指标摘要"""
    # 只有管理员可以查看系统指标
    if current_user.role not in ["admin", "super_admin"]:
        return create_response(
            data=None,
            message="权限不足",
            status_code=403
        )
    
    try:
        metrics = await performance_monitor.get_metrics_summary()
        return create_response(
            data=metrics,
            message="获取系统指标成功"
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"获取系统指标失败: {str(e)}",
            status_code=500
        )


@router.get("/health-score", summary="获取健康评分", description="获取系统健康评分")
async def get_health_score(
    current_user: User = Depends(get_current_user)
):
    """获取系统健康评分"""
    # 只有管理员可以查看健康评分
    if current_user.role not in ["admin", "super_admin"]:
        return create_response(
            data=None,
            message="权限不足",
            status_code=403
        )
    
    try:
        health_score = await performance_monitor.get_health_score()
        return create_response(
            data=health_score,
            message="获取健康评分成功"
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"获取健康评分失败: {str(e)}",
            status_code=500
        )


@router.get("/requests", summary="获取请求统计", description="获取API请求统计信息")
async def get_request_stats(
    minutes: int = Query(60, ge=1, le=1440, description="统计时间范围（分钟）"),
    current_user: User = Depends(get_current_user)
):
    """获取请求统计信息"""
    # 只有管理员可以查看请求统计
    if current_user.role not in ["admin", "super_admin"]:
        return create_response(
            data=None,
            message="权限不足",
            status_code=403
        )
    
    try:
        stats = await performance_monitor.collector.get_request_stats(minutes)
        return create_response(
            data=stats,
            message="获取请求统计成功"
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"获取请求统计失败: {str(e)}",
            status_code=500
        )


@router.get("/system", summary="获取系统资源", description="获取系统资源使用情况")
async def get_system_stats(
    current_user: User = Depends(get_current_user)
):
    """获取系统资源统计"""
    # 只有管理员可以查看系统资源
    if current_user.role not in ["admin", "super_admin"]:
        return create_response(
            data=None,
            message="权限不足",
            status_code=403
        )
    
    try:
        stats = await performance_monitor.collector.get_system_stats()
        return create_response(
            data=stats,
            message="获取系统资源统计成功"
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"获取系统资源统计失败: {str(e)}",
            status_code=500
        )


@router.get("/endpoints", summary="获取端点统计", description="获取API端点性能统计")
async def get_endpoint_stats(
    current_user: User = Depends(get_current_user)
):
    """获取端点统计信息"""
    # 只有管理员可以查看端点统计
    if current_user.role not in ["admin", "super_admin"]:
        return create_response(
            data=None,
            message="权限不足",
            status_code=403
        )
    
    try:
        stats = await performance_monitor.collector.get_endpoint_stats()
        return create_response(
            data=stats,
            message="获取端点统计成功"
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"获取端点统计失败: {str(e)}",
            status_code=500
        )


@router.get("/errors", summary="获取错误统计", description="获取系统错误统计信息")
async def get_error_stats(
    current_user: User = Depends(get_current_user)
):
    """获取错误统计信息"""
    # 只有管理员可以查看错误统计
    if current_user.role not in ["admin", "super_admin"]:
        return create_response(
            data=None,
            message="权限不足",
            status_code=403
        )
    
    try:
        stats = await performance_monitor.collector.get_error_stats()
        return create_response(
            data=stats,
            message="获取错误统计成功"
        )
    except Exception as e:
        return create_response(
            data=None,
            message=f"获取错误统计失败: {str(e)}",
            status_code=500
        )
