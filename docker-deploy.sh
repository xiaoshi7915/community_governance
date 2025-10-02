#!/bin/bash

# 基层治理智能体系统 - Docker一键部署脚本
# 支持开发环境和生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="community_governance"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
ENV_PROD_FILE=".env.prod"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                  基层治理智能体系统                          ║"
    echo "║                 Docker一键部署脚本                           ║"
    echo "║                                                              ║"
    echo "║  支持开发环境和生产环境部署                                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查Docker环境
check_docker() {
    log_step "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查Docker服务状态
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 服务未运行，请启动 Docker 服务"
        exit 1
    fi
    
    log_success "Docker环境检查完成"
}

# 创建Docker Compose文件
create_docker_compose() {
    local env_type=$1
    
    log_step "创建Docker Compose配置文件..."
    
    # 开发环境配置
    if [ "$env_type" = "dev" ]; then
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Redis缓存服务
  redis:
    image: redis:7-alpine
    container_name: governance_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - governance_network

  # 后端API服务
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: governance_backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      - redis
    networks:
      - governance_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 前端Web服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: governance_frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    networks:
      - governance_network

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: governance_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - governance_network

volumes:
  redis_data:

networks:
  governance_network:
    driver: bridge
EOF
    else
        # 生产环境配置
        cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # Redis缓存服务
  redis:
    image: redis:7-alpine
    container_name: governance_redis_prod
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - governance_network
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # 后端API服务
  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: governance_backend_prod
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env.prod
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      - redis
    networks:
      - governance_network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 前端Web服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: governance_frontend_prod
    restart: always
    ports:
      - "3000:80"
    environment:
      - NODE_ENV=production
      - VITE_API_BASE_URL=https://115.190.152.96:8000
    depends_on:
      - backend
    networks:
      - governance_network
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: governance_nginx_prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
      - "8443:8443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - governance_network
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M

volumes:
  redis_data:

networks:
  governance_network:
    driver: bridge
EOF
    fi
    
    log_success "Docker Compose配置文件创建完成"
}

# 创建生产环境Dockerfile
create_production_dockerfile() {
    log_step "创建生产环境Dockerfile..."
    
    # 后端生产环境Dockerfile
    cat > Dockerfile.prod << 'EOF'
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs uploads

# 设置权限
RUN chmod +x scripts/*.sh

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
EOF

    # 前端生产环境Dockerfile
    mkdir -p frontend
    cat > frontend/Dockerfile.prod << 'EOF'
# 构建阶段
FROM node:18-alpine as build

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建结果
COPY --from=build /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

    log_success "生产环境Dockerfile创建完成"
}

# 创建Nginx配置
create_nginx_config() {
    local env_type=$1
    
    log_step "创建Nginx配置文件..."
    
    mkdir -p nginx/conf.d
    
    if [ "$env_type" = "dev" ]; then
        # 开发环境Nginx配置
        cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # 前端路由
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API路由
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 健康检查
        location /health {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
    else
        # 生产环境Nginx配置
        cat > nginx/nginx.prod.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    # HTTP服务器 - 重定向到HTTPS
    server {
        listen 80;
        server_name 115.190.152.96;
        return 301 https://$server_name$request_uri;
    }
    
    # HTTPS服务器
    server {
        listen 443 ssl http2;
        listen 8443 ssl http2;
        server_name 115.190.152.96;
        
        # SSL配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # 前端路由
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API路由
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # 健康检查
        location /health {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # 文档路由
        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
    fi
    
    log_success "Nginx配置文件创建完成"
}

# 部署应用
deploy_app() {
    local env_type=$1
    
    log_step "部署应用 ($env_type 环境)..."
    
    if [ "$env_type" = "prod" ]; then
        # 生产环境部署
        log_info "使用生产环境配置部署..."
        docker-compose -f $COMPOSE_PROD_FILE down
        docker-compose -f $COMPOSE_PROD_FILE build --no-cache
        docker-compose -f $COMPOSE_PROD_FILE up -d
    else
        # 开发环境部署
        log_info "使用开发环境配置部署..."
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE build --no-cache
        docker-compose -f $COMPOSE_FILE up -d
    fi
    
    log_success "应用部署完成"
}

# 等待服务启动
wait_for_services() {
    log_step "等待服务启动..."
    
    # 等待后端服务
    log_info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s -f http://localhost:8000/health > /dev/null; then
            log_success "后端服务启动成功"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "后端服务启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待前端服务
    log_info "等待前端服务启动..."
    for i in {1..20}; do
        if curl -s -f http://localhost:3000 > /dev/null; then
            log_success "前端服务启动成功"
            break
        fi
        if [ $i -eq 20 ]; then
            log_warning "前端服务可能还在启动中..."
            break
        fi
        sleep 3
    done
}

# 显示部署信息
show_deployment_info() {
    local env_type=$1
    
    echo ""
    log_success "🎉 Docker部署完成！"
    echo ""
    log_info "容器状态："
    docker-compose ps
    echo ""
    log_info "访问地址："
    if [ "$env_type" = "prod" ]; then
        echo "  🌐 前端应用: https://115.190.152.96"
        echo "  📚 API文档: https://115.190.152.96:8443/docs"
        echo "  ❤️  健康检查: https://115.190.152.96:8443/health"
    else
        echo "  🌐 前端应用: http://localhost:3000"
        echo "  📚 API文档: http://localhost:8000/docs"
        echo "  ❤️  健康检查: http://localhost:8000/health"
    fi
    echo ""
    log_info "管理命令："
    echo "  查看容器状态: docker-compose ps"
    echo "  查看日志: docker-compose logs -f [service_name]"
    echo "  停止服务: $0 stop"
    echo "  重启服务: $0 restart"
    echo "  清理资源: $0 clean"
}

# 停止服务
stop_services() {
    log_step "停止Docker服务..."
    
    if [ -f "$COMPOSE_PROD_FILE" ]; then
        docker-compose -f $COMPOSE_PROD_FILE down
    fi
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose -f $COMPOSE_FILE down
    fi
    
    log_success "Docker服务已停止"
}

# 清理资源
clean_resources() {
    log_step "清理Docker资源..."
    
    stop_services
    
    # 删除镜像
    docker images | grep $PROJECT_NAME | awk '{print $3}' | xargs -r docker rmi -f
    
    # 清理未使用的资源
    docker system prune -f
    
    log_success "Docker资源清理完成"
}

# 主函数
main() {
    local env_type=${2:-dev}
    
    show_banner
    check_docker
    create_docker_compose $env_type
    
    if [ "$env_type" = "prod" ]; then
        create_production_dockerfile
    fi
    
    create_nginx_config $env_type
    deploy_app $env_type
    wait_for_services
    show_deployment_info $env_type
}

# 处理命令行参数
case "${1:-deploy}" in
    "deploy")
        main deploy ${2:-dev}
        ;;
    "dev")
        main deploy dev
        ;;
    "prod")
        main deploy prod
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        log_info "重启Docker服务..."
        stop_services
        sleep 3
        main deploy ${2:-dev}
        ;;
    "clean")
        clean_resources
        ;;
    "logs")
        if [ -n "$2" ]; then
            docker-compose logs -f $2
        else
            docker-compose logs -f
        fi
        ;;
    "status")
        log_info "Docker服务状态："
        docker-compose ps
        ;;
    *)
        echo "用法: $0 {deploy|dev|prod|stop|restart|clean|logs|status} [service_name]"
        echo ""
        echo "命令说明:"
        echo "  deploy [dev|prod] - 部署应用（默认开发环境）"
        echo "  dev               - 部署开发环境"
        echo "  prod              - 部署生产环境"
        echo "  stop              - 停止所有服务"
        echo "  restart [env]     - 重启服务"
        echo "  clean             - 清理Docker资源"
        echo "  logs [service]    - 查看服务日志"
        echo "  status            - 查看服务状态"
        exit 1
        ;;
esac
