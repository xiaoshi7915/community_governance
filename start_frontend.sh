#!/bin/bash

# 前端服务启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目路径
PROJECT_ROOT="/opt/community_governance"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 进入前端目录
cd "$FRONTEND_DIR"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs/frontend"

# 停止现有进程
if pgrep -f "vite" > /dev/null; then
    log_info "停止现有前端进程..."
    pkill -f "vite"
    sleep 2
fi

# 启动前端服务
log_info "启动前端开发服务器..."

# 使用exec启动，避免文件描述符问题
exec npm run dev -- --host 0.0.0.0 --port 3000 > "$PROJECT_ROOT/logs/frontend/dev.log" 2>&1
