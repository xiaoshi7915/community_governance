#!/bin/bash

# 日志监控脚本
# 实时监控和分析基层治理智能体后端系统日志

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# 显示实时日志
show_live_logs() {
    local service="$1"
    
    if [ -z "$service" ]; then
        log_info "显示所有服务的实时日志..."
        docker-compose -f docker-compose.prod.yml logs -f --tail=100
    else
        log_info "显示 $service 服务的实时日志..."
        docker-compose -f docker-compose.prod.yml logs -f --tail=100 "$service"
    fi
}

# 分析错误日志
analyze_errors() {
    log_info "分析最近的错误日志..."
    
    # 应用错误
    echo -e "${PURPLE}=== 应用错误 ===${NC}"
    if docker-compose -f docker-compose.prod.yml logs --tail=1000 app 2>/dev/null | grep -i "error\|exception\|traceback" | tail -20; then
        echo ""
    else
        log_success "未发现应用错误"
    fi
    
    # Nginx错误
    echo -e "${PURPLE}=== Nginx错误 ===${NC}"
    if docker-compose -f docker-compose.prod.yml logs --tail=1000 nginx 2>/dev/null | grep -i "error" | tail -10; then
        echo ""
    else
        log_success "未发现Nginx错误"
    fi
    
    # Redis错误
    echo -e "${PURPLE}=== Redis错误 ===${NC}"
    if docker-compose -f docker-compose.prod.yml logs --tail=1000 redis 2>/dev/null | grep -i "error\|warning" | tail -10; then
        echo ""
    else
        log_success "未发现Redis错误"
    fi
}

# 分析性能日志
analyze_performance() {
    log_info "分析性能日志..."
    
    echo -e "${PURPLE}=== 慢请求分析 ===${NC}"
    # 查找响应时间超过1秒的请求
    if docker-compose -f docker-compose.prod.yml logs --tail=1000 app 2>/dev/null | grep -E "process_time.*[1-9][0-9]*\." | tail -10; then
        echo ""
    else
        log_success "未发现慢请求"
    fi
    
    echo -e "${PURPLE}=== 内存使用情况 ===${NC}"
    # 查看容器内存使用
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

# 统计日志信息
show_log_stats() {
    log_info "统计日志信息..."
    
    echo -e "${PURPLE}=== 请求统计（最近1000条） ===${NC}"
    
    # HTTP状态码统计
    echo "HTTP状态码分布:"
    docker-compose -f docker-compose.prod.yml logs --tail=1000 nginx 2>/dev/null | \
        grep -oE 'HTTP/[0-9.]+ [0-9]{3}' | \
        awk '{print $2}' | \
        sort | uniq -c | sort -nr | head -10
    
    echo ""
    
    # API端点访问统计
    echo "热门API端点:"
    docker-compose -f docker-compose.prod.yml logs --tail=1000 nginx 2>/dev/null | \
        grep -oE '"[A-Z]+ /[^"]*"' | \
        sort | uniq -c | sort -nr | head -10
    
    echo ""
    
    # 错误统计
    echo "错误统计:"
    error_count=$(docker-compose -f docker-compose.prod.yml logs --tail=1000 app 2>/dev/null | grep -ci "error\|exception" || echo "0")
    warning_count=$(docker-compose -f docker-compose.prod.yml logs --tail=1000 app 2>/dev/null | grep -ci "warning" || echo "0")
    
    echo "  错误数量: $error_count"
    echo "  警告数量: $warning_count"
}

# 检查服务健康状态
check_service_health() {
    log_info "检查服务健康状态..."
    
    echo -e "${PURPLE}=== 容器状态 ===${NC}"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo -e "${PURPLE}=== 健康检查 ===${NC}"
    
    # 检查应用健康
    if curl -k -f -s https://115.190.152.96/health >/dev/null 2>&1; then
        log_success "✓ 应用健康检查通过"
    else
        log_error "✗ 应用健康检查失败"
    fi
    
    # 检查Redis连接
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "✓ Redis连接正常"
    else
        log_error "✗ Redis连接失败"
    fi
    
    # 检查外部数据库连接
    DATABASE_URL=$(grep "^DATABASE_URL=" .env.prod 2>/dev/null | cut -d'=' -f2)
    if [ -n "$DATABASE_URL" ]; then
        if timeout 5 python3 -c "
import asyncpg
import asyncio
async def test_db():
    try:
        conn = await asyncpg.connect('$DATABASE_URL')
        await conn.close()
        return True
    except:
        return False
print('success' if asyncio.run(test_db()) else 'failed')
" 2>/dev/null | grep -q "success"; then
            log_success "✓ 外部数据库连接正常"
        else
            log_error "✗ 外部数据库连接失败"
        fi
    fi
}

# 导出日志
export_logs() {
    local output_dir="./logs/export"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    log_info "导出日志到 $output_dir..."
    
    mkdir -p "$output_dir"
    
    # 导出各服务日志
    services=("app" "nginx" "redis")
    
    for service in "${services[@]}"; do
        log_info "导出 $service 日志..."
        docker-compose -f docker-compose.prod.yml logs --tail=10000 "$service" > "$output_dir/${service}_${timestamp}.log" 2>/dev/null || true
    done
    
    # 创建压缩包
    tar -czf "$output_dir/logs_${timestamp}.tar.gz" -C "$output_dir" *.log
    rm -f "$output_dir"/*.log
    
    log_success "日志已导出到: $output_dir/logs_${timestamp}.tar.gz"
}

# 清理旧日志
cleanup_logs() {
    log_info "清理旧日志..."
    
    # 清理Docker日志
    docker system prune -f --volumes
    
    # 清理导出的日志文件（保留最近7天）
    find ./logs/export -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true
    
    log_success "日志清理完成"
}

# 设置日志轮转
setup_log_rotation() {
    log_info "设置日志轮转..."
    
    # 创建logrotate配置
    cat > /tmp/docker-logs << 'EOF'
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        /bin/kill -USR1 $(cat /var/run/docker.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF

    # 检查是否有权限设置logrotate
    if [ "$EUID" -eq 0 ]; then
        mv /tmp/docker-logs /etc/logrotate.d/docker-logs
        log_success "日志轮转配置已设置"
    else
        log_warning "需要root权限设置系统日志轮转，配置文件已生成到 /tmp/docker-logs"
        log_info "请使用以下命令手动设置："
        log_info "sudo mv /tmp/docker-logs /etc/logrotate.d/docker-logs"
    fi
}

# 显示帮助信息
show_help() {
    echo "日志监控脚本使用说明："
    echo ""
    echo "用法: $0 [选项] [服务名]"
    echo ""
    echo "选项:"
    echo "  live [service]    - 显示实时日志（可指定服务：app, nginx, redis）"
    echo "  errors           - 分析错误日志"
    echo "  performance      - 分析性能日志"
    echo "  stats            - 显示日志统计"
    echo "  health           - 检查服务健康状态"
    echo "  export           - 导出日志文件"
    echo "  cleanup          - 清理旧日志"
    echo "  rotation         - 设置日志轮转"
    echo "  help             - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 live          - 显示所有服务实时日志"
    echo "  $0 live app      - 显示应用实时日志"
    echo "  $0 errors        - 分析错误日志"
    echo "  $0 health        - 检查服务健康状态"
}

# 主函数
main() {
    local command="${1:-live}"
    local service="$2"
    
    case "$command" in
        "live")
            show_live_logs "$service"
            ;;
        "errors")
            analyze_errors
            ;;
        "performance")
            analyze_performance
            ;;
        "stats")
            show_log_stats
            ;;
        "health")
            check_service_health
            ;;
        "export")
            export_logs
            ;;
        "cleanup")
            cleanup_logs
            ;;
        "rotation")
            setup_log_rotation
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 检查Docker Compose是否可用
if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose 命令未找到"
    exit 1
fi

# 检查配置文件是否存在
if [ ! -f "docker-compose.prod.yml" ]; then
    log_error "docker-compose.prod.yml 文件不存在"
    exit 1
fi

# 执行主函数
main "$@"
