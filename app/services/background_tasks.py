"""
后台任务服务
处理定时任务和异步任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services.statistics_service import statistics_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """后台任务服务"""
    
    def __init__(self):
        self._running = False
        self._tasks = []
    
    async def start(self):
        """启动后台任务"""
        if self._running:
            return
        
        self._running = True
        logger.info("后台任务服务启动")
        
        # 启动统计缓存刷新任务
        cache_refresh_task = asyncio.create_task(self._statistics_cache_refresh_task())
        self._tasks.append(cache_refresh_task)
        
        # 启动其他定时任务...
        
    async def stop(self):
        """停止后台任务"""
        if not self._running:
            return
        
        self._running = False
        logger.info("正在停止后台任务服务...")
        
        # 取消所有任务
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # 等待所有任务完成
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
        logger.info("后台任务服务已停止")
    
    async def _statistics_cache_refresh_task(self):
        """统计缓存刷新定时任务"""
        refresh_interval = 3600  # 1小时刷新一次
        
        while self._running:
            try:
                logger.info("开始刷新统计缓存...")
                await statistics_service.refresh_all_caches()
                logger.info("统计缓存刷新完成")
                
                # 等待下次刷新
                await asyncio.sleep(refresh_interval)
                
            except asyncio.CancelledError:
                logger.info("统计缓存刷新任务被取消")
                break
            except Exception as e:
                logger.error(f"统计缓存刷新任务出错: {str(e)}")
                # 出错后等待较短时间再重试
                await asyncio.sleep(300)  # 5分钟后重试
    
    async def refresh_statistics_cache_now(self):
        """立即刷新统计缓存"""
        try:
            logger.info("手动触发统计缓存刷新...")
            await statistics_service.refresh_all_caches()
            logger.info("手动统计缓存刷新完成")
        except Exception as e:
            logger.error(f"手动统计缓存刷新失败: {str(e)}")
            raise


# 创建全局后台任务服务实例
background_task_service = BackgroundTaskService()


async def startup_background_tasks():
    """应用启动时启动后台任务"""
    await background_task_service.start()


async def shutdown_background_tasks():
    """应用关闭时停止后台任务"""
    await background_task_service.stop()