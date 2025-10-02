"""
管理员API端点
提供系统管理功能，包括任务调度、缓存管理等
"""
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.core.permissions import require_permission, Permission
from app.core.scheduler import scheduler
from app.models.user import User
from app.schemas.response import ResponseModel
from app.services.statistics_service import statistics_service
from app.services.background_tasks import background_task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# 这里可以添加管理员权限检查装饰器
async def require_admin_permission(current_user: User = Depends(require_permission(Permission.VIEW_ADMIN_PANEL))):
    """检查管理员权限"""
    return current_user


@router.get("/tasks/status", response_model=ResponseModel)
async def get_task_status(
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有定时任务状态
    """
    try:
        task_status = scheduler.get_task_status()
        
        return ResponseModel(
            success=True,
            data={
                "tasks": task_status,
                "scheduler_running": scheduler._running,
                "total_tasks": len(task_status)
            },
            message="任务状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.post("/tasks/{task_name}/run", response_model=ResponseModel)
async def run_task_now(
    task_name: str,
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    立即执行指定任务
    
    - **task_name**: 任务名称
    """
    try:
        await scheduler.run_task_now(task_name)
        
        return ResponseModel(
            success=True,
            data={"task_name": task_name},
            message=f"任务 {task_name} 执行成功"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"执行任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行任务失败: {str(e)}")


@router.post("/tasks/{task_name}/enable", response_model=ResponseModel)
async def enable_task(
    task_name: str,
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    启用指定任务
    
    - **task_name**: 任务名称
    """
    try:
        scheduler.enable_task(task_name)
        
        return ResponseModel(
            success=True,
            data={"task_name": task_name, "enabled": True},
            message=f"任务 {task_name} 已启用"
        )
        
    except Exception as e:
        logger.error(f"启用任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启用任务失败: {str(e)}")


@router.post("/tasks/{task_name}/disable", response_model=ResponseModel)
async def disable_task(
    task_name: str,
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    禁用指定任务
    
    - **task_name**: 任务名称
    """
    try:
        scheduler.disable_task(task_name)
        
        return ResponseModel(
            success=True,
            data={"task_name": task_name, "enabled": False},
            message=f"任务 {task_name} 已禁用"
        )
        
    except Exception as e:
        logger.error(f"禁用任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"禁用任务失败: {str(e)}")


@router.post("/cache/statistics/refresh", response_model=ResponseModel)
async def refresh_statistics_cache(
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    手动刷新统计数据缓存
    """
    try:
        await statistics_service.refresh_all_caches()
        
        return ResponseModel(
            success=True,
            data={"message": "统计缓存刷新成功"},
            message="统计缓存刷新成功"
        )
        
    except Exception as e:
        logger.error(f"刷新统计缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刷新统计缓存失败: {str(e)}")


@router.get("/system/health", response_model=ResponseModel)
async def get_system_health(
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    获取系统健康状态
    """
    try:
        # 检查数据库连接
        try:
            await db.execute("SELECT 1")
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # 检查Redis连接
        try:
            from app.core.redis_client import redis_client
            await redis_client.get("health_check")
            redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"
        
        # 检查调度器状态
        scheduler_status = "running" if scheduler._running else "stopped"
        
        # 检查后台任务状态
        background_tasks_status = "running" if background_task_service._running else "stopped"
        
        health_data = {
            "database": database_status,
            "redis": redis_status,
            "scheduler": scheduler_status,
            "background_tasks": background_tasks_status,
            "overall": "healthy" if all([
                database_status == "healthy",
                redis_status == "healthy",
                scheduler_status == "running"
            ]) else "unhealthy"
        }
        
        return ResponseModel(
            success=True,
            data=health_data,
            message="系统健康状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统健康状态失败: {str(e)}")


@router.get("/statistics/summary", response_model=ResponseModel)
async def get_statistics_summary(
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    获取统计数据概览
    """
    try:
        # 获取基础统计数据
        user_stats = await statistics_service.get_user_statistics()
        event_stats = await statistics_service.get_event_statistics()
        efficiency_stats = await statistics_service.get_processing_efficiency_analysis()
        
        summary = {
            "user_statistics": {
                "total_events": user_stats.get("total_events", 0),
                "completion_rate": user_stats.get("completion_rate", 0),
                "avg_confidence": user_stats.get("avg_confidence", 0)
            },
            "event_statistics": {
                "total_types": len(event_stats.get("type_statistics", [])),
                "time_series_points": len(event_stats.get("time_series", []))
            },
            "efficiency_statistics": {
                "avg_processing_time": efficiency_stats.get("processing_efficiency", {}).get("avg_processing_time_hours", 0),
                "avg_response_time": efficiency_stats.get("response_efficiency", {}).get("avg_response_time_hours", 0)
            }
        }
        
        return ResponseModel(
            success=True,
            data=summary,
            message="统计数据概览获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取统计数据概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计数据概览失败: {str(e)}")


@router.post("/scheduler/start", response_model=ResponseModel)
async def start_scheduler(
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    启动任务调度器
    """
    try:
        await scheduler.start()
        
        return ResponseModel(
            success=True,
            data={"status": "started"},
            message="任务调度器启动成功"
        )
        
    except Exception as e:
        logger.error(f"启动调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")


@router.post("/scheduler/stop", response_model=ResponseModel)
async def stop_scheduler(
    admin_user: User = Depends(require_admin_permission),
    db: AsyncSession = Depends(get_db)
):
    """
    停止任务调度器
    """
    try:
        await scheduler.stop()
        
        return ResponseModel(
            success=True,
            data={"status": "stopped"},
            message="任务调度器停止成功"
        )
        
    except Exception as e:
        logger.error(f"停止调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")