# 基层治理智能体后端系统部署指南

## 📋 概述

本指南详细说明如何在服务器 `115.190.152.96` 上部署基层治理智能体后端系统。

### 🎯 部署特性

- **外部数据库**: 使用外部PostgreSQL数据库 (121.36.205.70:54333)
- **SSL/HTTPS**: 完整的SSL安全配置
- **虚拟环境**: 在jiceng_env虚拟环境中运行
- **容器化**: Docker容器化部署
- **反向代理**: Nginx反向代理和负载均衡
- **监控日志**: 实时日志监控和分析

### 🌐 访问地址

- **HTTPS API**: https://115.190.152.96:443
- **HTTP重定向**: http://115.190.152.96:80 → HTTPS
- **API文档**: https://115.190.152.96/docs
- **健康检查**: https://115.190.152.96/health
- **直接访问**: https://115.190.152.96:8443

## 🚀 快速部署

### 方法一：一键部署（推荐）

```bash
# 进入项目目录
cd /opt/community_governance

# 运行一键部署脚本
./quick_deploy.sh
```

### 方法二：手动部署

```bash
# 1. 生成SSL证书
./scripts/generate_ssl.sh

# 2. 检查配置
vim .env.prod

# 3. 执行部署
./deploy.sh deploy

# 4. 测试API
./scripts/test_api.sh
```

## 📁 项目结构

```
/opt/community_governance/
├── app/                          # 应用源码
├── deployment/                   # 部署配置
│   ├── nginx.conf               # Nginx配置
│   └── ssl/                     # SSL证书（Nginx用）
├── logs/                        # 日志目录
│   ├── app/                     # 应用日志
│   ├── nginx/                   # Nginx日志
│   └── redis/                   # Redis日志
├── scripts/                     # 脚本目录
│   ├── generate_ssl.sh          # SSL证书生成
│   ├── test_api.sh             # API测试
│   └── monitor_logs.sh         # 日志监控
├── ssl/                        # SSL证书（应用用）
├── docker-compose.prod.yml     # 生产环境Docker配置
├── Dockerfile.prod            # 生产环境Dockerfile
├── .env.prod                  # 生产环境配置
├── deploy.sh                  # 部署脚本
└── quick_deploy.sh           # 一键部署脚本
```

## ⚙️ 配置说明

### 环境配置 (.env.prod)

```bash
# 基础配置
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-32-chars-min
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-32-chars

# 外部数据库配置
DATABASE_URL=postgresql+asyncpg://pgvector:pgvector@121.36.205.70:54333/governance_db

# Redis配置
REDIS_URL=redis://redis:6379/0

# SSL配置
SSL_ENABLED=true
SSL_CERT_PATH=/app/ssl/cert.pem
SSL_KEY_PATH=/app/ssl/key.pem
HTTPS_PORT=8443

# CORS配置
BACKEND_CORS_ORIGINS=http://115.190.152.96:3000,https://115.190.152.96:3000

# 阿里云配置（请填入真实密钥）
ALIYUN_OSS_ACCESS_KEY_ID=your-real-access-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-real-access-key-secret
ALIYUN_AI_API_KEY=your-real-ai-api-key
AMAP_API_KEY=your-real-amap-api-key
```

### Docker配置

#### 生产环境服务

- **app**: 后端应用服务 (端口: 8000, 8443)
- **redis**: Redis缓存服务 (端口: 6379)
- **nginx**: 反向代理服务 (端口: 80, 443)

#### 特殊配置

- 使用 `Dockerfile.prod` 构建生产镜像
- 在 `jiceng_env` 虚拟环境中运行
- 连接外部PostgreSQL数据库
- 支持SSL/HTTPS

## 🔧 部署步骤详解

### 1. 系统要求检查

```bash
# 检查Docker
docker --version

# 检查Docker Compose
docker-compose --version

# 检查必要工具
curl --version
openssl version
```

### 2. SSL证书生成

```bash
# 生成自签名证书
./scripts/generate_ssl.sh generate

# 验证证书
./scripts/generate_ssl.sh verify

# 证书文件位置
ls -la ssl/
ls -la deployment/ssl/
```

### 3. 配置文件准备

```bash
# 复制配置模板
cp .env.prod .env.prod.backup

# 编辑配置文件
vim .env.prod

# 生成安全密钥
openssl rand -hex 32  # 用于SECRET_KEY
openssl rand -hex 32  # 用于JWT_SECRET_KEY
```

### 4. 服务部署

```bash
# 构建和启动服务
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. 服务验证

```bash
# 健康检查
curl -k https://115.190.152.96/health

# API文档
curl -k https://115.190.152.96/docs

# 运行完整测试
./scripts/test_api.sh all
```

## 📊 监控和管理

### 日志监控

```bash
# 实时日志
./scripts/monitor_logs.sh live

# 应用日志
./scripts/monitor_logs.sh live app

# 错误分析
./scripts/monitor_logs.sh errors

# 性能分析
./scripts/monitor_logs.sh performance

# 健康检查
./scripts/monitor_logs.sh health
```

### 服务管理

```bash
# 查看状态
./deploy.sh status

# 重启服务
./deploy.sh restart

# 停止服务
./deploy.sh stop

# 查看日志
./deploy.sh logs [service]
```

### API测试

```bash
# 完整测试
./scripts/test_api.sh all

# 基础测试
./scripts/test_api.sh basic

# 认证测试
./scripts/test_api.sh auth

# SSL测试
./scripts/test_api.sh ssl

# 性能测试
./scripts/test_api.sh performance
```

## 🔍 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看错误日志
docker-compose -f docker-compose.prod.yml logs app

# 检查配置文件
cat .env.prod | grep -v "^#"
```

#### 2. 数据库连接失败

```bash
# 测试外部数据库连接
python3 -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql+asyncpg://pgvector:pgvector@121.36.205.70:54333/governance_db')
    print('数据库连接成功')
    await conn.close()
asyncio.run(test())
"
```

#### 3. SSL证书问题

```bash
# 检查证书文件
ls -la ssl/
ls -la deployment/ssl/

# 验证证书
openssl x509 -in ssl/cert.pem -text -noout

# 重新生成证书
./scripts/generate_ssl.sh clean
./scripts/generate_ssl.sh generate
```

#### 4. 端口占用

```bash
# 检查端口占用
netstat -tulpn | grep -E ":(80|443|8000|8443|6379)"

# 停止占用端口的服务
sudo systemctl stop nginx  # 如果系统nginx在运行
```

#### 5. 权限问题

```bash
# 设置文件权限
chmod +x *.sh scripts/*.sh

# 检查Docker权限
sudo usermod -aG docker $USER
newgrp docker
```

### 日志分析

#### 应用日志

```bash
# 查看最新错误
docker-compose -f docker-compose.prod.yml logs app | grep -i error | tail -20

# 查看性能日志
docker-compose -f docker-compose.prod.yml logs app | grep "process_time" | tail -10
```

#### Nginx日志

```bash
# 查看访问日志
docker-compose -f docker-compose.prod.yml logs nginx | grep -E "GET|POST" | tail -20

# 查看错误日志
docker-compose -f docker-compose.prod.yml logs nginx | grep -i error | tail -10
```

### 性能优化

#### 容器资源

```bash
# 查看资源使用
docker stats --no-stream

# 调整容器资源限制
# 在docker-compose.prod.yml中添加：
# deploy:
#   resources:
#     limits:
#       memory: 1G
#       cpus: '0.5'
```

#### 数据库优化

```bash
# 检查数据库连接池
docker-compose -f docker-compose.prod.yml logs app | grep "database"

# 监控慢查询
docker-compose -f docker-compose.prod.yml logs app | grep "slow"
```

## 🔄 更新和维护

### 应用更新

```bash
# 1. 备份当前版本
docker-compose -f docker-compose.prod.yml down
cp -r . ../community_governance_backup_$(date +%Y%m%d)

# 2. 更新代码
git pull origin main

# 3. 重新构建和部署
docker-compose -f docker-compose.prod.yml up -d --build

# 4. 验证更新
./scripts/test_api.sh all
```

### 定期维护

```bash
# 清理Docker资源
docker system prune -f

# 备份日志
./scripts/monitor_logs.sh export

# 清理旧日志
./scripts/monitor_logs.sh cleanup

# 检查系统健康
./scripts/monitor_logs.sh health
```

### 数据备份

```bash
# 导出应用数据
docker-compose -f docker-compose.prod.yml exec app python -c "
from app.core.database import engine
# 执行数据导出逻辑
"

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env.prod ssl/ deployment/
```

## 📞 技术支持

### 联系信息

- **项目仓库**: [GitHub链接]
- **文档地址**: [文档链接]
- **问题反馈**: [Issue链接]

### 调试模式

```bash
# 启用调试模式
sed -i 's/DEBUG=false/DEBUG=true/' .env.prod
docker-compose -f docker-compose.prod.yml restart app

# 查看详细日志
docker-compose -f docker-compose.prod.yml logs -f app

# 恢复生产模式
sed -i 's/DEBUG=true/DEBUG=false/' .env.prod
docker-compose -f docker-compose.prod.yml restart app
```

## 📋 检查清单

### 部署前检查

- [ ] 系统依赖已安装 (Docker, Docker Compose, curl, openssl)
- [ ] 配置文件已正确设置 (.env.prod)
- [ ] SSL证书已生成
- [ ] 外部数据库连接正常
- [ ] 防火墙端口已开放 (80, 443, 8000, 8443)

### 部署后验证

- [ ] 所有容器正常运行
- [ ] 健康检查端点响应正常
- [ ] API文档可访问
- [ ] SSL证书有效
- [ ] 日志无严重错误
- [ ] API测试通过

### 生产环境安全

- [ ] 默认密钥已更改
- [ ] 敏感信息已保护
- [ ] HTTPS强制启用
- [ ] 访问日志已启用
- [ ] 定期备份已设置

---

**部署完成时间**: 2025-10-02  
**系统版本**: v1.1.0  
**维护人员**: 系统管理员
