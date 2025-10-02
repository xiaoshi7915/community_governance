#!/bin/bash

# 基层治理智能体系统 - 前后端统一启动脚本
# 服务器: 115.190.152.96
# 后端端口: 8000, 前端端口: 3000

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/opt/community_governance"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

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
    echo "║                 前后端统一启动脚本                           ║"
    echo "║                                                              ║"
    echo "║  后端API: http://115.190.152.96:8000                        ║"
    echo "║  前端Web: http://115.190.152.96:3000                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查依赖服务
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    # 检查Python虚拟环境
    if [ ! -d "$BACKEND_DIR/jiceng_env" ]; then
        log_error "Python虚拟环境不存在，请先创建虚拟环境"
        exit 1
    fi
    
    # 检查Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        log_warning "Redis服务未运行，尝试启动..."
        systemctl start redis || {
            log_error "Redis启动失败"
            exit 1
        }
    fi
    
    # 检查数据库连接
    log_info "测试外部数据库连接..."
    cd "$BACKEND_DIR"
    source jiceng_env/bin/activate
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
    
    log_success "依赖检查完成"
}

# 停止现有进程
stop_existing_processes() {
    log_step "停止现有进程..."
    
    # 停止后端进程
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        log_info "停止后端进程..."
        pkill -f "uvicorn.*app.main:app"
        sleep 2
    fi
    
    # 停止前端进程
    if pgrep -f "npm.*run.*dev" > /dev/null; then
        log_info "停止前端进程..."
        pkill -f "npm.*run.*dev"
        sleep 2
    fi
    
    # 停止Vite进程
    if pgrep -f "vite" > /dev/null; then
        log_info "停止Vite进程..."
        pkill -f "vite"
        sleep 2
    fi
    
    log_success "现有进程已停止"
}

# 启动后端服务
start_backend() {
    log_step "启动后端服务..."
    
    cd "$BACKEND_DIR"
    
    # 激活虚拟环境
    source jiceng_env/bin/activate
    
    # 加载环境配置文件
    if [ -f ".env.prod" ]; then
        log_info "加载生产环境配置文件 .env.prod"
        set -a  # 自动导出变量
        source .env.prod
        set +a  # 关闭自动导出
    elif [ -f ".env" ]; then
        log_info "加载环境配置文件 .env"
        set -a
        source .env
        set +a
    else
        log_warning "未找到环境配置文件，使用默认配置"
        # 设置基本环境变量
        export ENVIRONMENT=production
        export DEBUG=false
        export SECRET_KEY=EdSdgCpnsZyS94zSU58v169kGFfyEPbN9INSo9Twz07vFtwRft
        export JWT_SECRET_KEY=vsqSiMc5aUyF7jR4Lf7LgVYV1RK4a6r5SVEqzEqDyxRkhnU9Yv
        export DATABASE_URL=postgresql://pgvector:pgvector@121.36.205.70:54333/governance_prod
        export REDIS_URL=redis://localhost:6379/3
    fi
    
    # 创建日志目录
    mkdir -p logs/app
    
    # 启动后端服务
    log_info "启动uvicorn服务器..."
    nohup uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --access-log \
        --log-level info > logs/app/server.log 2>&1 &
    
    # 等待服务启动
    sleep 3
    
    # 检查后端服务状态
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        local pid=$(pgrep -f "uvicorn.*app.main:app")
        log_success "后端服务启动成功 (PID: $pid)"
        
        # 测试健康检查
        log_info "测试后端健康状态..."
        sleep 2
        if curl -s -f http://localhost:8000/health > /dev/null; then
            log_success "后端健康检查通过"
        else
            log_warning "后端健康检查失败，请检查日志"
        fi
    else
        log_error "后端服务启动失败"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    log_step "启动前端服务..."
    
    # 检查前端目录是否存在
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "前端目录不存在: $FRONTEND_DIR"
        exit 1
    fi
    
    cd "$FRONTEND_DIR"
    
    # 检查package.json是否存在
    if [ ! -f "package.json" ]; then
        log_error "package.json 不存在，请确保前端项目已正确设置"
        exit 1
    fi
    
    # 安装依赖（如果node_modules不存在）
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi
    
    # 创建前端日志目录
    mkdir -p "$PROJECT_ROOT/logs/frontend"
    
    # 启动前端开发服务器
    log_info "启动前端开发服务器..."
    nohup "$PROJECT_ROOT/start_frontend.sh" > /dev/null 2>&1 &
    
    # 等待服务启动
    sleep 5
    
    # 检查前端服务状态
    if pgrep -f "vite" > /dev/null; then
        local pid=$(pgrep -f "vite")
        log_success "前端服务启动成功 (PID: $pid)"
        
        # 测试前端服务
        log_info "测试前端服务状态..."
        sleep 3
        if curl -s -f http://localhost:3000 > /dev/null; then
            log_success "前端服务访问正常"
        else
            log_warning "前端服务可能还在启动中..."
        fi
    else
        log_error "前端服务启动失败"
        exit 1
    fi
}

# 显示服务信息
show_service_info() {
    echo ""
    log_success "🎉 系统启动完成！"
    echo ""
    log_info "服务信息："
    echo "  📱 后端API服务:"
    echo "    - PID: $(pgrep -f 'uvicorn.*app.main:app')"
    echo "    - 端口: 8000"
    echo "    - 日志: logs/app/server.log"
    echo ""
    echo "  🌐 前端Web服务:"
    echo "    - PID: $(pgrep -f 'vite')"
    echo "    - 端口: 3000"
    echo "    - 日志: logs/frontend/dev.log"
    echo ""
    log_info "访问地址："
    echo "  🔗 前端应用: http://115.190.152.96:3000"
    echo "  📚 API文档: http://115.190.152.96:8000/docs"
    echo "  ❤️  健康检查: http://115.190.152.96:8000/health"
    echo "  🏠 本地前端: http://localhost:3000"
    echo "  🏠 本地后端: http://localhost:8000"
    echo ""
    log_info "测试账号："
    echo "  👤 市民: 13800138001 / citizen123"
    echo "  👤 网格员: 13800138002 / grid123"
    echo "  👤 管理员: 13800138003 / manager123"
    echo "  👤 决策者: 13800138004 / decision123"
    echo ""
    log_info "管理命令："
    echo "  查看后端日志: tail -f logs/app/server.log"
    echo "  查看前端日志: tail -f logs/frontend/dev.log"
    echo "  停止所有服务: $0 stop"
    echo "  重启所有服务: $0 restart"
    echo "  查看服务状态: $0 status"
}

# 停止所有服务
stop_services() {
    log_step "停止所有服务..."
    
    # 停止后端
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        log_info "停止后端服务..."
        pkill -f "uvicorn.*app.main:app"
        log_success "后端服务已停止"
    else
        log_warning "后端服务未运行"
    fi
    
    # 停止前端
    if pgrep -f "vite" > /dev/null; then
        log_info "停止前端服务..."
        pkill -f "vite"
        log_success "前端服务已停止"
    else
        log_warning "前端服务未运行"
    fi
    
    # 停止npm进程
    if pgrep -f "npm.*run.*dev" > /dev/null; then
        pkill -f "npm.*run.*dev"
    fi
}

# 查看服务状态
show_status() {
    log_info "服务状态检查："
    echo ""
    
    # 后端状态
    if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
        log_success "✅ 后端服务: 运行中 (PID: $(pgrep -f 'uvicorn.*app.main:app'))"
        if curl -s -f http://localhost:8000/health > /dev/null; then
            echo "   健康检查: ✅ 正常"
        else
            echo "   健康检查: ❌ 异常"
        fi
    else
        log_warning "❌ 后端服务: 未运行"
    fi
    
    echo ""
    
    # 前端状态
    if pgrep -f "vite" > /dev/null; then
        log_success "✅ 前端服务: 运行中 (PID: $(pgrep -f 'vite'))"
        if curl -s -f http://localhost:3000 > /dev/null; then
            echo "   访问检查: ✅ 正常"
        else
            echo "   访问检查: ❌ 异常"
        fi
    else
        log_warning "❌ 前端服务: 未运行"
    fi
    
    echo ""
    
    # Redis状态
    if redis-cli ping > /dev/null 2>&1; then
        log_success "✅ Redis服务: 运行中"
    else
        log_warning "❌ Redis服务: 未运行"
    fi
}

# 主函数
main() {
    show_banner
    check_dependencies
    stop_existing_processes
    start_backend
    start_frontend
    show_service_info
}

# 处理命令行参数
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        log_info "停止基层治理智能体系统..."
        stop_services
        log_success "系统已停止"
        ;;
    "restart")
        log_info "重启基层治理智能体系统..."
        stop_services
        sleep 3
        main
        ;;
    "status")
        show_status
        ;;
    "backend")
        log_info "仅启动后端服务..."
        check_dependencies
        if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
            pkill -f "uvicorn.*app.main:app"
            sleep 2
        fi
        start_backend
        log_success "后端服务启动完成"
        ;;
    "frontend")
        log_info "仅启动前端服务..."
        if pgrep -f "vite" > /dev/null; then
            pkill -f "vite"
            sleep 2
        fi
        start_frontend
        log_success "前端服务启动完成"
        ;;
    "logs")
        echo "选择要查看的日志:"
        echo "1) 后端日志"
        echo "2) 前端日志"
        read -p "请选择 (1-2): " choice
        case $choice in
            1) tail -f logs/app/server.log ;;
            2) tail -f logs/frontend/dev.log ;;
            *) echo "无效选择" ;;
        esac
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|backend|frontend|logs}"
        echo ""
        echo "命令说明:"
        echo "  start     - 启动前后端服务（默认）"
        echo "  stop      - 停止所有服务"
        echo "  restart   - 重启所有服务"
        echo "  status    - 查看服务状态"
        echo "  backend   - 仅启动后端服务"
        echo "  frontend  - 仅启动前端服务"
        echo "  logs      - 查看服务日志"
        exit 1
        ;;
esac
