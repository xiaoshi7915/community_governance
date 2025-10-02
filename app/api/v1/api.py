"""
API v1 主路由
整合所有v1版本的API端点
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, files, ai, events, notifications, statistics, admin, monitoring, metrics_dashboard, monitoring_metrics
from app.api import health

# 创建API v1路由器
api_router = APIRouter()

# 包含所有子路由
api_router.include_router(health.router)  # 健康检查
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(events.router, tags=["events", "location"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(statistics.router, tags=["statistics"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(monitoring_metrics.router)
api_router.include_router(metrics_dashboard.router, prefix="/dashboard", tags=["dashboard"])