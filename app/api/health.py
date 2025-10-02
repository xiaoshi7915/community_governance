"""
健康检查API端点
用于检测服务器状态和连接性
"""
from fastapi import APIRouter
from app.core.response import create_response

router = APIRouter(tags=["健康检查"])


@router.get(
    "/health",
    summary="健康检查",
    description="检查服务器运行状态"
)
async def health_check():
    """
    健康检查端点
    返回服务器基本状态信息
    """
    return create_response(
        data={
            "status": "healthy",
            "service": "基层治理智能体",
            "version": "1.0.0"
        },
        message="服务器运行正常"
    )


@router.get(
    "/api/v1/health", 
    summary="API健康检查",
    description="检查API服务状态"
)
async def api_health_check():
    """
    API健康检查端点
    返回API服务状态信息
    """
    return create_response(
        data={
            "status": "healthy",
            "api_version": "v1",
            "service": "基层治理智能体API",
            "endpoints": [
                "/api/v1/auth",
                "/api/v1/events", 
                "/api/v1/users",
                "/api/v1/files",
                "/api/v1/ai"
            ]
        },
        message="API服务运行正常"
    )