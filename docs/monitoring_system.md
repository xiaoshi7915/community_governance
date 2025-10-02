# 系统监控和日志记录

本文档描述了基层治理智能体后端系统的监控和日志记录功能。

## 功能概述

系统监控和日志记录模块提供以下核心功能：

1. **结构化日志记录** - 包含请求跟踪和错误详情
2. **API性能监控** - 记录响应时间和资源使用
3. **系统健康检查** - 监控服务状态
4. **错误告警机制** - 及时通知运维人员
5. **日志搜索和过滤** - 便于问题排查
6. **系统指标收集** - 可视化展示

## 架构组件

### 核心模块

- `app/core/monitoring.py` - 监控核心功能
- `app/core/performance_middleware.py` - 性能监控中间件
- `app/core/monitoring_scheduler.py` - 监控任务调度器
- `app/services/log_service.py` - 日志服务
- `app/api/v1/monitoring.py` - 监控API端点
- `app/api/v1/metrics_dashboard.py` - 指标仪表板

### 数据模型

#### SystemMetrics（系统指标）
```python
@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    active_connections: int
```

#### APIMetrics（API指标）
```python
@dataclass
class APIMetrics:
    endpoint: str
    method: str
    response_time: float
    status_code: int
    timestamp: datetime
    request_id: str
```

#### HealthStatus（健康状态）
```python
@dataclass
class HealthStatus:
    service: str
    status: str  # healthy, unhealthy, degraded
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[datetime] = None
```

## API端点

### 健康检查

#### GET /api/v1/monitoring/health
完整的系统健康检查，返回所有组件的状态。

**响应示例：**
```json
{
  "code": 200,
  "message": "健康检查完成",
  "data": {
    "overall_status": "healthy",
    "check_duration": 0.125,
    "timestamp": "2024-01-01T12:00:00",
    "services": {
      "database": {
        "service": "database",
        "status": "healthy",
        "response_time": 0.045
      },
      "redis": {
        "service": "redis",
        "status": "healthy",
        "response_time": 0.012
      }
    },
    "system_metrics": {
      "cpu_percent": 45.2,
      "memory_percent": 62.1,
      "disk_percent": 78.5
    }
  }
}
```

#### GET /api/v1/monitoring/health/simple
简单健康检查，用于负载均衡器。

### 系统指标

#### GET /api/v1/monitoring/metrics/system
获取系统指标数据。

**参数：**
- `minutes` (int): 获取最近N分钟的数据，默认10分钟

#### GET /api/v1/monitoring/metrics/endpoints
获取API端点性能统计。

### 告警管理

#### GET /api/v1/monitoring/alerts
获取系统告警信息。

**参数：**
- `minutes` (int): 获取最近N分钟的告警，默认60分钟
- `level` (str): 告警级别过滤 (warning, critical)
- `alert_type` (str): 告警类型过滤 (system, api, health)

### 日志管理

#### GET /api/v1/monitoring/logs/search
搜索和过滤日志。

**参数：**
- `query` (str): 搜索关键词
- `level` (str): 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger_name` (str): 记录器名称
- `start_time` (datetime): 开始时间
- `end_time` (datetime): 结束时间
- `request_id` (str): 请求ID
- `limit` (int): 返回条数限制，默认100
- `offset` (int): 偏移量，默认0

#### GET /api/v1/monitoring/logs/statistics
获取日志统计信息。

#### POST /api/v1/monitoring/logs/export
导出日志数据。

**参数：**
- `format_type` (str): 导出格式 (json, csv)

### 仪表板

#### GET /api/v1/dashboard/dashboard
获取仪表板数据，包含系统概览、API性能、错误统计等。

#### GET /api/v1/dashboard/realtime-metrics
获取实时指标数据。

#### GET /api/v1/dashboard/performance-trends
获取性能趋势数据。

#### WebSocket /api/v1/dashboard/ws
实时推送监控数据的WebSocket连接。

## 配置说明

### 环境变量

```bash
# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 监控配置
MONITORING_ENABLED=true
METRICS_RETENTION_HOURS=24
ALERT_THRESHOLDS_CPU=80
ALERT_THRESHOLDS_MEMORY=85
ALERT_THRESHOLDS_DISK=90
```

### 告警阈值配置

默认告警阈值在 `AlertManager` 中定义：

```python
self.alert_thresholds = {
    "cpu_percent": 80.0,      # CPU使用率阈值
    "memory_percent": 85.0,   # 内存使用率阈值
    "disk_percent": 90.0,     # 磁盘使用率阈值
    "response_time": 5.0,     # API响应时间阈值（秒）
    "error_rate": 0.05        # 错误率阈值（5%）
}
```

## 使用示例

### 1. 启动监控系统

监控系统在应用启动时自动启动：

```python
# 在 app/main.py 中
await monitoring_scheduler.start()
```

### 2. 记录API性能

性能监控中间件自动记录所有API请求：

```python
# 自动记录，无需手动调用
app.add_middleware(PerformanceMonitoringMiddleware)
```

### 3. 手动收集系统指标

```python
from app.core.monitoring import metrics_collector

# 收集当前系统指标
metrics = metrics_collector.collect_system_metrics()
print(f"CPU使用率: {metrics.cpu_percent}%")
```

### 4. 执行健康检查

```python
from app.core.monitoring import health_checker

# 执行完整健康检查
health_data = await health_checker.perform_full_health_check()
print(f"系统状态: {health_data['overall_status']}")
```

### 5. 搜索日志

```python
from app.services.log_service import log_service, LogSearchFilter

# 搜索错误日志
filter_params = LogSearchFilter(
    level="ERROR",
    start_time=datetime.now() - timedelta(hours=1),
    limit=50
)

entries, total = await log_service.search_logs(filter_params)
```

### 6. 设置自定义告警

```python
from app.core.monitoring import alert_manager

# 发送自定义告警
alert = {
    "type": "custom",
    "level": "warning",
    "message": "自定义告警消息",
    "timestamp": datetime.now().isoformat()
}

await alert_manager.send_alert(alert)
```

## 监控数据存储

### 内存存储
- 系统指标：使用 `deque` 存储最近1000条记录
- API指标：使用 `deque` 存储最近1000条记录
- 告警历史：使用 `deque` 存储最近100条记录

### Redis存储
- 系统指标：定期存储到Redis，键格式 `system_metrics:YYYYMMDDHHMM`
- 健康状态：存储最新状态，键 `system_health:latest`

### 文件导出
- 指标数据：定期导出到 `exports/metrics/` 目录
- 日志数据：按需导出到 `exports/logs/` 目录

## 性能优化

### 1. 异步处理
所有监控操作都是异步的，不会阻塞主要业务流程。

### 2. 批量处理
指标收集和告警检查使用批量处理，减少系统开销。

### 3. 数据清理
定期清理过期的监控数据，防止内存泄漏。

### 4. 缓存机制
频繁访问的监控数据使用Redis缓存。

## 故障排查

### 1. 监控系统无法启动
检查依赖项是否安装：
```bash
pip install psutil structlog prometheus-client
```

### 2. 健康检查失败
检查数据库和Redis连接配置。

### 3. 日志搜索缓慢
- 检查日志文件大小
- 考虑使用日志轮转
- 优化搜索条件

### 4. 告警过多
调整告警阈值配置。

## 扩展功能

### 1. 集成外部监控系统
可以集成Prometheus、Grafana等监控系统：

```python
# 添加Prometheus指标导出
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

### 2. 自定义告警通道
扩展告警管理器支持邮件、短信、钉钉等通知方式。

### 3. 日志聚合
集成ELK Stack或Loki进行大规模日志聚合和分析。

## 测试

运行监控系统测试：

```bash
# 运行单元测试
pytest tests/test_monitoring.py -v

# 运行功能演示
python scripts/test_monitoring_system.py
```

## 安全考虑

1. **权限控制**：监控API需要管理员权限
2. **数据脱敏**：日志中的敏感信息需要脱敏处理
3. **访问限制**：限制监控端点的访问频率
4. **数据加密**：敏感监控数据需要加密存储