#!/bin/bash

# 基层治理智能体后端系统启动脚本
# 服务器: 115.190.152.96:8000

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 检查是否已有进程运行
check_existing_process() {
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        log_warning "检测到已有服务进程运行"
        echo "现有进程PID: $(pgrep -f 'uvicorn.*app.main:app')"
        read -p "是否停止现有进程并重新启动? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "停止现有进程..."
            pkill -f "uvicorn.*app.main:app"
            sleep 2
        else
            log_info "保持现有进程运行"
            exit 0
        fi
    fi
}

# 检查依赖服务
check_dependencies() {
    log_info "检查依赖服务..."
    
    # 检查Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        log_warning "Redis服务未运行，尝试启动..."
        systemctl start redis || log_error "Redis启动失败"
    fi
    
    # 检查数据库连接
    log_info "测试外部数据库连接..."
    if ! python3 -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://pgvector:pgvector@121.36.205.70:54333/governance_prod')
    await conn.close()
    print('数据库连接正常')
asyncio.run(test())
" 2>/dev/null; then
        log_error "外部数据库连接失败"
        exit 1
    fi
    
    log_success "依赖服务检查完成"
}

# 启动服务
start_service() {
    log_info "启动基层治理智能体后端服务..."
    
    # 进入项目目录
    cd /opt/community_governance
    
    # 激活虚拟环境
    source jiceng_env/bin/activate
    
    # 设置环境变量
    export ENVIRONMENT=production
    export DEBUG=false
    export SECRET_KEY=EdSdgCpnsZyS94zSU58v169kGFfyEPbN9INSo9Twz07vFtwRft
    export JWT_SECRET_KEY=vsqSiMc5aUyF7jR4Lf7LgVYV1RK4a6r5SVEqzEqDyxRkhnU9Yv
    export DATABASE_URL=postgresql://pgvector:pgvector@121.36.205.70:54333/governance_prod
    export REDIS_URL=redis://localhost:6379/3
    
    # 创建日志目录
    mkdir -p logs/app
    
    # 启动服务
    log_info "启动uvicorn服务器..."
    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --access-log \
        --log-level info > logs/app/server.log 2>&1 &
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        local pid=$(pgrep -f "uvicorn.*app.main:app")
        log_success "服务启动成功 (PID: $pid)"
        
        # 测试健康检查
        log_info "测试服务健康状态..."
        sleep 2
        if curl -s -f http://localhost:8000/health > /dev/null; then
            log_success "健康检查通过"
        else
            log_warning "健康检查失败，请检查日志"
        fi
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 显示服务信息
show_service_info() {
    echo ""
    log_info "服务信息："
    echo "  PID: $(pgrep -f 'uvicorn.*app.main:app')"
    echo "  端口: 8000"
    echo "  日志: logs/app/server.log"
    echo ""
    log_info "访问地址："
    echo "  健康检查: http://115.190.152.96:8000/health"
    echo "  API文档: http://115.190.152.96:8000/docs"
    echo "  本地测试: http://localhost:8000/health"
    echo ""
    log_info "管理命令："
    echo "  查看日志: tail -f logs/app/server.log"
    echo "  停止服务: pkill -f uvicorn"
    echo "  重启服务: $0"
}

# 主函数
main() {
    log_info "基层治理智能体后端系统启动脚本"
    log_info "服务器: 115.190.152.96:8000"
    echo ""
    
    check_existing_process
    check_dependencies
    start_service
    show_service_info
    
    log_success "🎉 系统启动完成！"
}

# 处理命令行参数
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        log_info "停止服务..."
        if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
            pkill -f "uvicorn.*app.main:app"
            log_success "服务已停止"
        else
            log_warning "没有找到运行中的服务"
        fi
        ;;
    "restart")
        log_info "重启服务..."
        if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
            pkill -f "uvicorn.*app.main:app"
            sleep 2
        fi
        main
        ;;
    "status")
        if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
            log_success "服务正在运行 (PID: $(pgrep -f 'uvicorn.*app.main:app'))"
            curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "健康检查失败"
        else
            log_warning "服务未运行"
        fi
        ;;
    "logs")
        tail -f logs/app/server.log
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo "  start   - 启动服务（默认）"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        exit 1
        ;;
esac
