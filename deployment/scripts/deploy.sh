#!/bin/bash

# 基层治理系统生产环境部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的工具
check_requirements() {
    log_info "检查部署环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_info "环境检查通过"
}

# 检查环境变量
check_env_vars() {
    log_info "检查环境变量..."
    
    required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "ALIYUN_ACCESS_KEY_ID"
        "ALIYUN_ACCESS_KEY_SECRET"
        "OSS_BUCKET_NAME"
        "OSS_ENDPOINT"
        "BAILIAN_API_KEY"
        "BAILIAN_ENDPOINT"
        "GRAFANA_PASSWORD"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必要的环境变量:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    log_info "环境变量检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    directories=(
        "logs"
        "ssl"
        "backups"
        "monitoring/rules"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
}

# 生成SSL证书（自签名，生产环境应使用真实证书）
generate_ssl_cert() {
    log_info "生成SSL证书..."
    
    if [[ ! -f "ssl/governance.crt" ]]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/governance.key \
            -out ssl/governance.crt \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Governance/CN=governance.example.com"
        log_info "SSL证书生成完成"
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 构建应用镜像
build_images() {
    log_info "构建应用镜像..."
    
    docker-compose -f docker-compose.prod.yml build --no-cache
    log_info "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 先启动基础服务
    docker-compose -f docker-compose.prod.yml up -d db redis
    log_info "数据库和缓存服务已启动"
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    sleep 30
    
    # 运行数据库迁移
    log_info "运行数据库迁移..."
    docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head
    
    # 启动应用服务
    docker-compose -f docker-compose.prod.yml up -d app
    log_info "应用服务已启动"
    
    # 等待应用就绪
    log_info "等待应用就绪..."
    sleep 20
    
    # 启动其他服务
    docker-compose -f docker-compose.prod.yml up -d
    log_info "所有服务已启动"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查应用健康状态
    max_attempts=30
    attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "应用健康检查通过"
            break
        fi
        
        log_warn "健康检查失败，重试中... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "应用健康检查失败"
        exit 1
    fi
    
    # 检查数据库连接
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres -d governance_db &> /dev/null; then
        log_info "数据库连接正常"
    else
        log_error "数据库连接失败"
        exit 1
    fi
    
    # 检查Redis连接
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping &> /dev/null; then
        log_info "Redis连接正常"
    else
        log_error "Redis连接失败"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    log_info "部署完成！"
    echo ""
    echo "服务访问地址:"
    echo "  应用服务: https://governance.example.com"
    echo "  API文档: https://governance.example.com/docs"
    echo "  Grafana: http://monitoring.governance.example.com/grafana"
    echo "  Prometheus: http://monitoring.governance.example.com/prometheus"
    echo ""
    echo "服务状态:"
    docker-compose -f docker-compose.prod.yml ps
}

# 主函数
main() {
    log_info "开始部署基层治理系统..."
    
    check_requirements
    check_env_vars
    create_directories
    generate_ssl_cert
    build_images
    start_services
    health_check
    show_deployment_info
    
    log_info "部署完成！"
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi