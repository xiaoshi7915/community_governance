#!/usr/bin/env python3
"""
监控系统功能演示脚本
展示系统监控、日志记录、性能监控等功能
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.monitoring import metrics_collector, health_checker, alert_manager
from app.core.logging import configure_logging, get_logger
from app.services.log_service import log_service, LogSearchFilter


async def demonstrate_system_monitoring():
    """演示系统监控功能"""
    print("=" * 60)
    print("系统监控功能演示")
    print("=" * 60)
    
    try:
        # 1. 收集系统指标
        print("\n1. 收集系统指标...")
        system_metrics = metrics_collector.collect_system_metrics()
        
        print(f"CPU使用率: {system_metrics.cpu_percent:.1f}%")
        print(f"内存使用率: {system_metrics.memory_percent:.1f}%")
        print(f"磁盘使用率: {system_metrics.disk_percent:.1f}%")
        print(f"活跃连接数: {system_metrics.active_connections}")
        
        # 2. 模拟API指标记录
        print("\n2. 记录API性能指标...")
        test_endpoints = [
            ("/api/v1/users", "GET", 0.125, 200),
            ("/api/v1/events", "POST", 0.250, 201),
            ("/api/v1/files", "GET", 0.089, 200),
            ("/api/v1/ai/analyze", "POST", 2.150, 200),
            ("/api/v1/invalid", "GET", 0.050, 404),
        ]
        
        for endpoint, method, response_time, status_code in test_endpoints:
            metrics_collector.record_api_metrics(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                request_id=f"demo-{datetime.now().strftime('%H%M%S')}"
            )
            print(f"记录: {method} {endpoint} - {response_time}s - {status_code}")
        
        # 3. 获取端点统计
        print("\n3. 端点性能统计...")
        for endpoint, method, _, _ in test_endpoints[:3]:
            stats = metrics_collector.get_endpoint_statistics(endpoint, method)
            print(f"{method} {endpoint}:")
            print(f"  请求数: {stats['request_count']}")
            print(f"  平均响应时间: {stats['avg_response_time']:.3f}s")
        
        # 4. 获取最近指标
        print("\n4. 最近指标汇总...")
        recent_metrics = metrics_collector.get_recent_metrics(minutes=1)
        print(f"系统指标数量: {len(recent_metrics['system_metrics'])}")
        print(f"API指标数量: {len(recent_metrics['api_metrics'])}")
        print(f"错误统计: {recent_metrics['error_counts']}")
        
    except Exception as e:
        print(f"系统监控演示失败: {e}")


async def demonstrate_health_checks():
    """演示健康检查功能"""
    print("\n" + "=" * 60)
    print("健康检查功能演示")
    print("=" * 60)
    
    try:
        # 1. 数据库健康检查
        print("\n1. 数据库健康检查...")
        db_status = await health_checker.check_database_health()
        print(f"数据库状态: {db_status.status}")
        if db_status.response_time:
            print(f"响应时间: {db_status.response_time:.3f}s")
        if db_status.error_message:
            print(f"错误信息: {db_status.error_message}")
        
        # 2. Redis健康检查
        print("\n2. Redis健康检查...")
        redis_status = await health_checker.check_redis_health()
        print(f"Redis状态: {redis_status.status}")
        if redis_status.response_time:
            print(f"响应时间: {redis_status.response_time:.3f}s")
        if redis_status.error_message:
            print(f"错误信息: {redis_status.error_message}")
        
        # 3. 外部服务健康检查
        print("\n3. 外部服务健康检查...")
        external_services = await health_checker.check_external_services_health()
        for service_name, status in external_services.items():
            print(f"{service_name}状态: {status.status}")
            if status.error_message:
                print(f"  错误: {status.error_message}")
        
        # 4. 完整健康检查
        print("\n4. 完整健康检查...")
        full_health = await health_checker.perform_full_health_check()
        print(f"整体状态: {full_health['overall_status']}")
        print(f"检查耗时: {full_health['check_duration']:.3f}s")
        
    except Exception as e:
        print(f"健康检查演示失败: {e}")


async def demonstrate_alert_system():
    """演示告警系统功能"""
    print("\n" + "=" * 60)
    print("告警系统功能演示")
    print("=" * 60)
    
    try:
        # 1. 模拟系统告警
        print("\n1. 模拟系统告警...")
        
        # 创建高CPU使用率指标
        from app.core.monitoring import SystemMetrics
        high_cpu_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # 超过阈值
            memory_percent=50.0,
            memory_used_mb=4096.0,
            memory_available_mb=4096.0,
            disk_percent=60.0,
            disk_used_gb=30.0,
            disk_free_gb=20.0,
            active_connections=10
        )
        
        await alert_manager.check_system_alerts(high_cpu_metrics)
        print("已触发CPU使用率告警")
        
        # 2. 模拟API告警
        print("\n2. 模拟API告警...")
        
        from app.core.monitoring import APIMetrics
        slow_api_metrics = APIMetrics(
            endpoint="/api/v1/slow-endpoint",
            method="POST",
            response_time=6.0,  # 超过阈值
            status_code=200,
            timestamp=datetime.now(),
            request_id="slow-demo"
        )
        
        await alert_manager.check_api_alerts(slow_api_metrics)
        print("已触发API响应时间告警")
        
        # 3. 获取告警历史
        print("\n3. 告警历史...")
        recent_alerts = alert_manager.get_recent_alerts(minutes=60)
        for i, alert in enumerate(recent_alerts, 1):
            print(f"告警 {i}:")
            print(f"  类型: {alert['type']}")
            print(f"  级别: {alert['level']}")
            print(f"  消息: {alert['message']}")
            print(f"  时间: {alert['timestamp']}")
        
    except Exception as e:
        print(f"告警系统演示失败: {e}")


async def demonstrate_log_service():
    """演示日志服务功能"""
    print("\n" + "=" * 60)
    print("日志服务功能演示")
    print("=" * 60)
    
    try:
        # 1. 创建测试日志
        print("\n1. 创建测试日志...")
        logger = get_logger("demo")
        
        # 记录不同级别的日志
        logger.info("这是一条信息日志", user_id="demo-user", action="test")
        logger.warning("这是一条警告日志", endpoint="/api/v1/test")
        logger.error("这是一条错误日志", error_code="DEMO_ERROR")
        
        print("已记录测试日志")
        
        # 2. 搜索日志
        print("\n2. 搜索日志...")
        
        # 搜索包含"测试"的日志
        filter_params = LogSearchFilter(
            query="测试",
            limit=10
        )
        
        log_entries, total_count = await log_service.search_logs(filter_params)
        print(f"搜索到 {total_count} 条包含'测试'的日志")
        
        for i, entry in enumerate(log_entries[:3], 1):
            print(f"日志 {i}:")
            print(f"  时间: {entry.timestamp}")
            print(f"  级别: {entry.level}")
            print(f"  消息: {entry.message[:50]}...")
        
        # 3. 按级别搜索
        print("\n3. 按级别搜索日志...")
        error_filter = LogSearchFilter(
            level="ERROR",
            limit=5
        )
        
        error_entries, error_count = await log_service.search_logs(error_filter)
        print(f"找到 {error_count} 条错误日志")
        
        # 4. 获取日志统计
        print("\n4. 日志统计信息...")
        stats = await log_service.get_log_statistics(hours=1)
        
        print(f"统计时间范围: {stats['time_range']['hours']} 小时")
        print(f"总日志条数: {stats['total_entries']}")
        print(f"错误率: {stats['error_rate']:.2f}%")
        print("级别分布:")
        for level, count in stats['level_distribution'].items():
            print(f"  {level}: {count}")
        
    except Exception as e:
        print(f"日志服务演示失败: {e}")


async def main():
    """主函数"""
    print("基层治理智能体后端 - 监控系统功能演示")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 配置日志
    configure_logging()
    
    try:
        # 依次演示各个功能
        await demonstrate_system_monitoring()
        await demonstrate_health_checks()
        await demonstrate_alert_system()
        await demonstrate_log_service()
        
        print("\n" + "=" * 60)
        print("监控系统功能演示完成")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())