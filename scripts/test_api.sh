#!/bin/bash

# API端点测试脚本
# 测试基层治理智能体后端系统的所有API端点

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_IP="115.190.152.96"
BASE_URL="https://$SERVER_IP"
API_BASE="$BASE_URL/api/v1"

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

# 测试HTTP状态码
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local description="$4"
    local data="$5"
    
    log_info "测试: $description"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -k -s -o /dev/null -w "%{http_code}" "$endpoint")
    elif [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$endpoint")
        else
            response=$(curl -k -s -o /dev/null -w "%{http_code}" -X POST "$endpoint")
        fi
    fi
    
    if [ "$response" = "$expected_status" ]; then
        log_success "✓ $description (状态码: $response)"
        return 0
    else
        log_warning "⚠ $description (期望: $expected_status, 实际: $response)"
        return 1
    fi
}

# 测试基础端点
test_basic_endpoints() {
    log_info "=== 测试基础端点 ==="
    
    test_endpoint "GET" "$BASE_URL/health" "200" "健康检查端点"
    test_endpoint "GET" "$BASE_URL/docs" "200" "API文档端点"
    test_endpoint "GET" "$BASE_URL/openapi.json" "200" "OpenAPI规范端点"
}

# 测试认证端点
test_auth_endpoints() {
    log_info "=== 测试认证端点 ==="
    
    # 测试认证相关端点（未登录状态应返回401）
    test_endpoint "GET" "$API_BASE/auth/me" "401" "获取当前用户信息（未认证）"
    test_endpoint "POST" "$API_BASE/auth/logout" "401" "用户登出（未认证）"
    
    # 测试登录端点（无效数据应返回422）
    test_endpoint "POST" "$API_BASE/auth/login" "422" "用户登录（无效数据）" '{"username":"","password":""}'
    
    # 测试注册端点（无效数据应返回422）
    test_endpoint "POST" "$API_BASE/auth/register" "422" "用户注册（无效数据）" '{"username":"","password":"","email":""}'
}

# 测试用户端点
test_user_endpoints() {
    log_info "=== 测试用户端点 ==="
    
    # 用户相关端点（未认证应返回401）
    test_endpoint "GET" "$API_BASE/users/me" "401" "获取当前用户详情（未认证）"
    test_endpoint "PUT" "$API_BASE/users/me" "401" "更新当前用户信息（未认证）"
    test_endpoint "GET" "$API_BASE/users" "401" "获取用户列表（未认证）"
}

# 测试事件端点
test_event_endpoints() {
    log_info "=== 测试事件端点 ==="
    
    # 事件相关端点
    test_endpoint "GET" "$API_BASE/events" "401" "获取事件列表（未认证）"
    test_endpoint "POST" "$API_BASE/events" "401" "创建事件（未认证）"
    test_endpoint "GET" "$API_BASE/events/1" "401" "获取事件详情（未认证）"
}

# 测试文件端点
test_file_endpoints() {
    log_info "=== 测试文件端点 ==="
    
    # 文件相关端点
    test_endpoint "POST" "$API_BASE/files/upload" "401" "文件上传（未认证）"
    test_endpoint "GET" "$API_BASE/files" "401" "获取文件列表（未认证）"
}

# 测试AI端点
test_ai_endpoints() {
    log_info "=== 测试AI端点 ==="
    
    # AI相关端点
    test_endpoint "POST" "$API_BASE/ai/chat" "401" "AI对话（未认证）"
    test_endpoint "POST" "$API_BASE/ai/analyze" "401" "AI分析（未认证）"
}

# 测试统计端点
test_statistics_endpoints() {
    log_info "=== 测试统计端点 ==="
    
    # 统计相关端点
    test_endpoint "GET" "$API_BASE/statistics/overview" "401" "获取统计概览（未认证）"
    test_endpoint "GET" "$API_BASE/statistics/events" "401" "获取事件统计（未认证）"
}

# 测试通知端点
test_notification_endpoints() {
    log_info "=== 测试通知端点 ==="
    
    # 通知相关端点
    test_endpoint "GET" "$API_BASE/notifications" "401" "获取通知列表（未认证）"
    test_endpoint "PUT" "$API_BASE/notifications/1/read" "401" "标记通知已读（未认证）"
}

# 测试监控端点
test_monitoring_endpoints() {
    log_info "=== 测试监控端点 ==="
    
    # 监控相关端点（需要管理员权限）
    test_endpoint "GET" "$API_BASE/monitoring/metrics" "401" "获取系统指标（未认证）"
    test_endpoint "GET" "$API_BASE/monitoring/health-score" "401" "获取健康评分（未认证）"
}

# 测试管理员端点
test_admin_endpoints() {
    log_info "=== 测试管理员端点 ==="
    
    # 管理员相关端点
    test_endpoint "GET" "$API_BASE/admin/users" "401" "管理用户列表（未认证）"
    test_endpoint "GET" "$API_BASE/admin/system-info" "401" "获取系统信息（未认证）"
}

# 测试SSL连接
test_ssl_connection() {
    log_info "=== 测试SSL连接 ==="
    
    # 测试SSL证书
    if openssl s_client -connect "$SERVER_IP:443" -servername "$SERVER_IP" </dev/null 2>/dev/null | grep -q "CONNECTED"; then
        log_success "✓ SSL连接正常"
    else
        log_warning "⚠ SSL连接可能有问题"
    fi
    
    # 测试HTTPS重定向
    http_response=$(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_IP/health")
    if [ "$http_response" = "301" ]; then
        log_success "✓ HTTP到HTTPS重定向正常"
    else
        log_warning "⚠ HTTP重定向状态码: $http_response"
    fi
}

# 性能测试
test_performance() {
    log_info "=== 性能测试 ==="
    
    # 测试响应时间
    response_time=$(curl -k -s -o /dev/null -w "%{time_total}" "$BASE_URL/health")
    response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
    
    if [ "$response_time_ms" -lt 1000 ]; then
        log_success "✓ 响应时间正常: ${response_time_ms}ms"
    elif [ "$response_time_ms" -lt 3000 ]; then
        log_warning "⚠ 响应时间较慢: ${response_time_ms}ms"
    else
        log_error "✗ 响应时间过慢: ${response_time_ms}ms"
    fi
}

# 生成测试报告
generate_report() {
    local total_tests="$1"
    local passed_tests="$2"
    local failed_tests="$3"
    
    echo ""
    log_info "=== 测试报告 ==="
    echo "总测试数: $total_tests"
    echo "通过: $passed_tests"
    echo "失败: $failed_tests"
    echo "成功率: $(echo "scale=2; $passed_tests * 100 / $total_tests" | bc -l)%"
    
    if [ "$failed_tests" -eq 0 ]; then
        log_success "所有测试通过！"
    else
        log_warning "有 $failed_tests 个测试失败，请检查相关功能"
    fi
}

# 主函数
main() {
    log_info "开始测试基层治理智能体后端API..."
    log_info "目标服务器: $SERVER_IP"
    log_info "基础URL: $BASE_URL"
    
    total_tests=0
    passed_tests=0
    
    # 执行所有测试
    test_functions=(
        "test_basic_endpoints"
        "test_auth_endpoints" 
        "test_user_endpoints"
        "test_event_endpoints"
        "test_file_endpoints"
        "test_ai_endpoints"
        "test_statistics_endpoints"
        "test_notification_endpoints"
        "test_monitoring_endpoints"
        "test_admin_endpoints"
        "test_ssl_connection"
        "test_performance"
    )
    
    for test_func in "${test_functions[@]}"; do
        echo ""
        if $test_func; then
            passed_tests=$((passed_tests + 1))
        fi
        total_tests=$((total_tests + 1))
    done
    
    # 生成报告
    failed_tests=$((total_tests - passed_tests))
    generate_report "$total_tests" "$passed_tests" "$failed_tests"
}

# 处理命令行参数
case "${1:-all}" in
    "all")
        main
        ;;
    "basic")
        test_basic_endpoints
        ;;
    "auth")
        test_auth_endpoints
        ;;
    "ssl")
        test_ssl_connection
        ;;
    "performance")
        test_performance
        ;;
    *)
        echo "用法: $0 {all|basic|auth|ssl|performance}"
        echo "  all         - 运行所有测试（默认）"
        echo "  basic       - 测试基础端点"
        echo "  auth        - 测试认证端点"
        echo "  ssl         - 测试SSL连接"
        echo "  performance - 性能测试"
        exit 1
        ;;
esac
