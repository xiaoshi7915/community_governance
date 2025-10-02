# 基层治理智能体后端系统

基于FastAPI的现代化Web服务，为移动端应用提供完整的后端支持。

## 功能特性

- 🚀 基于FastAPI的高性能异步API
- 🔐 JWT认证和用户管理
- 📱 事件管理和AI智能识别
- 📁 阿里云OSS文件存储
- 🤖 阿里云百炼AI服务集成
- 🗄️ PostgreSQL数据库支持
- ⚡ Redis缓存和会话管理
- 📊 结构化日志和监控
- 🐳 Docker容器化部署

## 技术栈

- **后端框架**: FastAPI + Pydantic
- **数据库**: PostgreSQL + SQLAlchemy
- **缓存**: Redis
- **认证**: JWT
- **文件存储**: 阿里云OSS
- **AI服务**: 阿里云百炼
- **容器化**: Docker + Docker Compose

## 项目结构

```
governance-backend/
├── app/                    # 应用程序主目录
│   ├── api/               # API路由
│   │   └── v1/           # API v1版本
│   ├── core/             # 核心配置和工具
│   ├── models/           # 数据模型
│   ├── services/         # 业务服务层
│   └── main.py          # 应用入口
├── scripts/              # 脚本文件
├── tests/               # 测试文件
├── requirements.txt     # Python依赖
├── pyproject.toml      # 项目配置
├── Dockerfile          # Docker配置
├── docker-compose.yml  # Docker Compose配置
└── README.md           # 项目说明
```

## 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Docker (可选)

### 本地开发

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd governance-backend
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入实际配置
   ```

4. **启动数据库服务**
   ```bash
   docker-compose up -d db redis
   ```

5. **运行数据库迁移**
   ```bash
   alembic upgrade head
   ```

6. **启动应用**
   ```bash
   python run.py
   ```

### Docker部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

### 开发脚本

```bash
# 启动开发环境
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

## API文档

启动应用后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境配置

### 开发环境
- 数据库: `governance_dev`
- Redis: 数据库0
- 日志级别: DEBUG

### 测试环境
- 数据库: `governance_test`
- Redis: 数据库1
- 日志级别: WARNING

### 生产环境
- 使用环境变量配置
- 启用安全设置
- 结构化JSON日志

## 开发指南

### 代码规范

```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/

# 运行测试
pytest
```

### 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 部署说明

### 生产环境部署

1. 设置环境变量
2. 配置数据库和Redis
3. 运行数据库迁移
4. 启动应用服务

### 监控和日志

- 应用日志: 结构化JSON格式
- 健康检查: `/health`
- 指标监控: Prometheus格式

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License