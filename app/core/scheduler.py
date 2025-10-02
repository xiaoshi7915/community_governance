"""
定时任务调度器
管理统计数据缓存刷新和其他定时任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass

from app.services.statistics_service import statistics_service

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """定时任务配置"""
    name: str
    func: Callable
    interval_seconds: int
    next_run: datetime
    enabled: bool = True
    last_run: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 3


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    def add_task(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        enabled: bool = True
    ):
        """
        添加定时任务
        
        Args:
            name: 任务名称
            func: 任务函数
            interval_seconds: 执行间隔（秒）
            enabled: 是否启用
        """
        next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
        
        task = ScheduledTask(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            next_run=next_run,
            enabled=enabled
        )
        
        self.tasks[name] = task
        logger.info(f"添加定时任务: {name}, 间隔: {interval_seconds}秒")
    
    def remove_task(self, name: str):
        """移除定时任务"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"移除定时任务: {name}")
    
    def enable_task(self, name: str):
        """启用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            logger.info(f"启用任务: {name}")
    
    def disable_task(self, name: str):
        """禁用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            logger.info(f"禁用任务: {name}")
    
    async def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        logger.info("任务调度器启动")
        
        # 添加默认的统计缓存刷新任务
        self._add_default_tasks()
        
        # 启动调度循环
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        logger.info("正在停止任务调度器...")
        
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("任务调度器已停止")
    
    def _add_default_tasks(self):
        """添加默认任务"""
        # 统计缓存刷新任务 - 每小时执行一次
        self.add_task(
            name="statistics_cache_refresh",
            func=statistics_service.refresh_all_caches,
            interval_seconds=3600,  # 1小时
            enabled=True
        )
        
        # 统计缓存预热任务 - 每6小时执行一次
        self.add_task(
            name="statistics_cache_warmup",
            func=statistics_service._warm_up_caches,
            interval_seconds=21600,  # 6小时
            enabled=True
        )
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                # 检查需要执行的任务
                for task_name, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    if current_time >= task.next_run:
                        await self._execute_task(task)
                
                # 等待1分钟后再次检查
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("调度器循环被取消")
                break
            except Exception as e:
                logger.error(f"调度器循环出错: {str(e)}")
                await asyncio.sleep(60)
    
    async def _execute_task(self, task: ScheduledTask):
        """执行单个任务"""
        try:
            logger.info(f"开始执行任务: {task.name}")
            
            # 执行任务
            if asyncio.iscoroutinefunction(task.func):
                await task.func()
            else:
                task.func()
            
            # 更新任务状态
            task.last_run = datetime.utcnow()
            task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
            task.error_count = 0  # 重置错误计数
            
            logger.info(f"任务执行成功: {task.name}, 下次执行时间: {task.next_run}")
            
        except Exception as e:
            task.error_count += 1
            logger.error(f"任务执行失败: {task.name}, 错误: {str(e)}, 错误次数: {task.error_count}")
            
            # 如果错误次数超过限制，禁用任务
            if task.error_count >= task.max_errors:
                task.enabled = False
                logger.error(f"任务因错误次数过多被禁用: {task.name}")
            else:
                # 延迟下次执行时间
                delay = min(300 * task.error_count, 3600)  # 最多延迟1小时
                task.next_run = datetime.utcnow() + timedelta(seconds=delay)
                logger.info(f"任务将在 {delay} 秒后重试: {task.name}")
    
    def get_task_status(self) -> List[Dict]:
        """获取所有任务状态"""
        status_list = []
        
        for task_name, task in self.tasks.items():
            status_list.append({
                "name": task.name,
                "enabled": task.enabled,
                "interval_seconds": task.interval_seconds,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "error_count": task.error_count,
                "max_errors": task.max_errors
            })
        
        return status_list
    
    async def run_task_now(self, task_name: str):
        """立即执行指定任务"""
        if task_name not in self.tasks:
            raise ValueError(f"任务不存在: {task_name}")
        
        task = self.tasks[task_name]
        await self._execute_task(task)


# 创建全局调度器实例
scheduler = TaskScheduler()


async def start_scheduler():
    """启动调度器"""
    await scheduler.start()


async def stop_scheduler():
    """停止调度器"""
    await scheduler.stop()