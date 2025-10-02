"""
监控任务调度器
定期执行系统监控、指标收集和健康检查任务
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import json
import os

from app.core.logging import get_logger
from app.core.monitoring import metrics_collector, health_checker, alert_manager
from app.core.redis import get_redis

logger = get_logger(__name__)


class MonitoringScheduler:
    """监控任务调度器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.running = False
        self.tasks = []
        
        # 任务配置
        self.task_intervals = {
            "collect_system_metrics": 60,  # 每分钟收集系统指标
            "health_check": 300,  # 每5分钟执行健康检查
            "cleanup_old_metrics": 3600,  # 每小时清理旧指标
            "export_metrics": 1800,  # 每30分钟导出指标到文件
        }
        
        self.last_run_times = {}
    
    async def start(self):
        """启动监控调度器"""
        if self.running:
            self.logger.warning("监控调度器已在运行")
            return
        
        self.running = True
        self.logger.info("启动监控调度器")
        
        # 创建后台任务
        self.tasks = [
            asyncio.create_task(self._run_scheduler()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]
        
        self.logger.info("监控调度器启动完成")
    
    async def stop(self):
        """停止监控调度器"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("停止监控调度器")
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.logger.info("监控调度器已停止")
    
    async def _run_scheduler(self):
        """主调度循环"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # 检查各个任务是否需要执行
                for task_name, interval in self.task_intervals.items():
                    last_run = self.last_run_times.get(task_name)
                    
                    if (last_run is None or 
                        (current_time - last_run).total_seconds() >= interval):
                        
                        # 执行任务
                        await self._execute_task(task_name)
                        self.last_run_times[task_name] = current_time
                
                # 等待下一次检查
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"调度器运行异常: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
    
    async def _execute_task(self, task_name: str):
        """执行指定任务"""
        try:
            self.logger.debug(f"执行监控任务: {task_name}")
            
            if task_name == "collect_system_metrics":
                await self._collect_system_metrics_task()
            elif task_name == "health_check":
                await self._health_check_task()
            elif task_name == "cleanup_old_metrics":
                await self._cleanup_old_metrics_task()
            elif task_name == "export_metrics":
                await self._export_metrics_task()
            
        except Exception as e:
            self.logger.error(f"执行监控任务失败: {task_name}, {e}")
    
    async def _collect_system_metrics_task(self):
        """收集系统指标任务"""
        try:
            # 收集系统指标
            system_metrics = metrics_collector.collect_system_metrics()
            
            # 检查系统告警
            await alert_manager.check_system_alerts(system_metrics)
            
            # 将指标存储到Redis（可选）
            try:
                redis = await get_redis()
                metrics_key = f"system_metrics:{datetime.now().strftime('%Y%m%d%H%M')}"
                await redis.setex(
                    metrics_key, 
                    3600,  # 1小时过期
                    json.dumps(system_metrics.to_dict())
                )
            except Exception as e:
                self.logger.warning(f"存储系统指标到Redis失败: {e}")
            
            self.logger.debug("系统指标收集完成")
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
    
    async def _health_check_task(self):
        """健康检查任务"""
        try:
            # 执行完整健康检查
            health_data = await health_checker.perform_full_health_check()
            
            # 记录健康状态
            self.logger.info(
                "系统健康检查完成",
                overall_status=health_data["overall_status"],
                check_duration=health_data["check_duration"]
            )
            
            # 如果系统不健康，发送告警
            if health_data["overall_status"] != "healthy":
                alert = {
                    "type": "health",
                    "level": "critical" if health_data["overall_status"] == "unhealthy" else "warning",
                    "message": f"系统健康状态异常: {health_data['overall_status']}",
                    "health_data": health_data,
                    "timestamp": datetime.now().isoformat()
                }
                await alert_manager.send_alert(alert)
            
            # 将健康状态存储到Redis
            try:
                redis = await get_redis()
                health_key = "system_health:latest"
                await redis.setex(
                    health_key,
                    600,  # 10分钟过期
                    json.dumps(health_data)
                )
            except Exception as e:
                self.logger.warning(f"存储健康状态到Redis失败: {e}")
            
        except Exception as e:
            self.logger.error(f"健康检查任务失败: {e}")
    
    async def _cleanup_old_metrics_task(self):
        """清理旧指标数据任务"""
        try:
            # 清理内存中的旧指标（由deque自动管理，这里主要是清理Redis）
            redis = await get_redis()
            
            # 清理旧的系统指标
            cutoff_time = datetime.now() - timedelta(hours=24)
            pattern = "system_metrics:*"
            
            async for key in redis.scan_iter(match=pattern):
                key_str = key.decode('utf-8')
                # 从key中提取时间戳
                try:
                    timestamp_str = key_str.split(':')[1]
                    key_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M')
                    
                    if key_time < cutoff_time:
                        await redis.delete(key)
                        self.logger.debug(f"删除过期指标: {key_str}")
                        
                except Exception as e:
                    self.logger.warning(f"解析指标key失败: {key_str}, {e}")
            
            self.logger.debug("旧指标清理完成")
            
        except Exception as e:
            self.logger.error(f"清理旧指标失败: {e}")
    
    async def _export_metrics_task(self):
        """导出指标数据任务"""
        try:
            # 获取最近的指标数据
            metrics_data = metrics_collector.get_recent_metrics(minutes=30)
            
            # 确保导出目录存在
            export_dir = "exports/metrics"
            os.makedirs(export_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"metrics_{timestamp}.json"
            filepath = os.path.join(export_dir, filename)
            
            # 导出到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"指标数据导出完成: {filepath}")
            
            # 清理旧的导出文件（保留最近7天）
            await self._cleanup_old_exports(export_dir)
            
        except Exception as e:
            self.logger.error(f"导出指标数据失败: {e}")
    
    async def _cleanup_old_exports(self, export_dir: str):
        """清理旧的导出文件"""
        try:
            cutoff_time = datetime.now() - timedelta(days=7)
            
            for filename in os.listdir(export_dir):
                if filename.startswith('metrics_') and filename.endswith('.json'):
                    filepath = os.path.join(export_dir, filename)
                    
                    # 获取文件修改时间
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
                        self.logger.debug(f"删除过期导出文件: {filename}")
                        
        except Exception as e:
            self.logger.warning(f"清理导出文件失败: {e}")
    
    async def _metrics_collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await asyncio.sleep(60)  # 每分钟执行一次
                
                if not self.running:
                    break
                
                # 这里可以添加额外的指标收集逻辑
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"指标收集循环异常: {e}")
                await asyncio.sleep(60)
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 每5分钟执行一次
                
                if not self.running:
                    break
                
                # 这里可以添加额外的健康检查逻辑
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查循环异常: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 每小时执行一次
                
                if not self.running:
                    break
                
                # 这里可以添加额外的清理逻辑
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理循环异常: {e}")
                await asyncio.sleep(3600)


# 创建全局调度器实例
monitoring_scheduler = MonitoringScheduler()