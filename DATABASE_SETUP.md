# 数据库设置指南

## 概述

本项目使用PostgreSQL作为主数据库，SQLAlchemy作为ORM，Alembic进行数据库迁移管理。

## 数据库模型

### 核心模型

1. **User (用户模型)**
   - 用户认证和基本信息
   - 支持手机号登录
   - 包含头像、状态等字段

2. **Event (事件模型)**
   - 城市治理事件核心信息
   - 包含地理位置、AI分析结果
   - 支持优先级和状态管理

3. **EventTimeline (事件时间线模型)**
   - 记录事件状态变化历史
   - 跟踪处理进度和操作人员

4. **EventMedia (事件媒体模型)**
   - 管理事件相关的图片、视频文件
   - 支持缩略图和元数据存储

### 枚举类型

- `EventPriority`: 事件优先级 (LOW, MEDIUM, HIGH, URGENT)
- `EventStatus`: 事件状态 (PENDING, PROCESSING, COMPLETED, REJECTED, CANCELLED)
- `MediaType`: 媒体类型 (IMAGE, VIDEO, AUDIO)

## 数据库配置

### 环境变量

在 `.env` 文件中配置数据库连接：

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/governance_db
```

### 连接配置

数据库连接配置在 `app/core/database.py` 中：

- 使用异步连接 (asyncpg)
- 支持连接池管理
- 自动重连机制

## 数据库初始化

### 方法1: 使用Alembic迁移

```bash
# 运行迁移
alembic upgrade head
```

### 方法2: 使用初始化脚本

```bash
# 创建所有表
python -m app.core.database_init create

# 重置数据库（删除后重新创建）
python -m app.core.database_init reset
```

### 方法3: 通过应用启动

应用启动时会自动初始化数据库（在开发和测试环境）。

## 迁移管理

### Alembic配置

- 配置文件: `alembic.ini`
- 环境脚本: `alembic/env.py`
- 迁移脚本: `alembic/versions/`

### 创建新迁移

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "描述变更内容"

# 手动创建迁移脚本
alembic revision -m "描述变更内容"
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 降级到指定版本
alembic downgrade <revision_id>
```

## 索引策略

### 主要索引

- **users表**: phone (唯一索引)
- **events表**: 
  - user_id, status, created_at (复合索引)
  - location_lat, location_lng (地理位置索引)
- **event_timelines表**: event_id, created_at (复合索引)

### 查询优化

- 使用PostgreSQL的GiST索引支持地理位置查询
- 事件列表查询支持分页和游标分页
- 热点数据使用Redis缓存

## 数据库表结构

### users 表
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### events 表
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    location_lat FLOAT NOT NULL,
    location_lng FLOAT NOT NULL,
    location_address VARCHAR(500),
    priority eventpriority DEFAULT 'MEDIUM',
    status eventstatus DEFAULT 'PENDING',
    confidence FLOAT DEFAULT 0.0,
    ai_analysis JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 测试

运行模型测试：

```bash
python test_models.py
```

## 故障排除

### 常见问题

1. **连接被拒绝**: 确保PostgreSQL服务正在运行
2. **权限错误**: 检查数据库用户权限
3. **编码问题**: 确保数据库使用UTF-8编码
4. **迁移失败**: 检查模型定义和外键约束

### 日志查看

应用日志会记录数据库操作的详细信息，可以通过日志排查问题。

## 性能优化

1. **索引优化**: 根据查询模式添加合适的索引
2. **连接池**: 配置合适的连接池大小
3. **查询优化**: 使用explain分析查询计划
4. **缓存策略**: 对热点数据使用Redis缓存