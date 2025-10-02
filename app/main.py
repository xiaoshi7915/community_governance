"""
基层治理智能体后端系统主应用入口
"""
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, init_db
from app.core.redis import init_redis, close_redis
from app.core.logging import configure_logging, get_logger
from app.core.middleware import ExceptionHandlerMiddleware, RequestLoggingMiddleware
from app.core.performance_middleware import PerformanceMonitoringMiddleware
from app.core.monitoring_scheduler import monitoring_scheduler
from app.models import Base
from app.api.v1.api import api_router
from app.api.health import router as health_router

# 配置日志
configure_logging()
logger = get_logger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="基层治理智能体后端API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加中间件（注意顺序很重要）
# 1. 异常处理中间件（最外层）
app.add_middleware(ExceptionHandlerMiddleware)

# 2. 性能监控中间件
app.add_middleware(PerformanceMonitoringMiddleware)

# 3. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 3. CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    logger.info("正在启动基层治理智能体后端系统...")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")
        
        # 初始化Redis
        await init_redis()
        logger.info("Redis连接初始化完成")
        
        # 启动AI异步任务处理器
        from app.services.ai_service import ai_service
        await ai_service.start_async_processor()
        logger.info("AI异步任务处理器启动完成")
        
        # 启动监控调度器
        await monitoring_scheduler.start()
        logger.info("监控调度器启动完成")
        
        # 启动性能监控
        from app.core.metrics import performance_monitor
        await performance_monitor.start()
        logger.info("性能监控启动完成")
        
        logger.info("系统启动完成")
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("正在关闭系统...")
    
    try:
        # 停止性能监控
        from app.core.metrics import performance_monitor
        await performance_monitor.stop()
        logger.info("性能监控已停止")
        
        # 停止监控调度器
        await monitoring_scheduler.stop()
        logger.info("监控调度器已停止")
        
        # 关闭Redis连接
        await close_redis()
        logger.info("Redis连接已关闭")
        
        logger.info("系统关闭完成")
    except Exception as e:
        logger.error(f"系统关闭时发生错误: {e}")

@app.get("/")
async def root():
    """根路径健康检查"""
    return {"message": "基层治理智能体后端系统运行正常"}

# 包含健康检查路由（无前缀，直接访问）
app.include_router(health_router)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """详细健康检查端点"""
    from app.core.redis import redis_client
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 检查数据库连接
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # 检查Redis连接
    try:
        if redis_client:
            await redis_client.ping()
            health_status["checks"]["redis"] = {"status": "healthy"}
        else:
            health_status["checks"]["redis"] = {"status": "unavailable", "message": "Redis未配置"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    return health_status