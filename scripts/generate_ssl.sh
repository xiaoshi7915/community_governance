#!/bin/bash

# SSL证书生成脚本
# 为基层治理智能体后端系统生成自签名SSL证书

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

# 服务器IP和域名
SERVER_IP="115.190.152.96"
DOMAIN_NAME="governance.local"

# SSL目录
SSL_DIR="./ssl"
NGINX_SSL_DIR="./deployment/ssl"

# 创建SSL目录
create_ssl_directories() {
    log_info "创建SSL证书目录..."
    mkdir -p "$SSL_DIR"
    mkdir -p "$NGINX_SSL_DIR"
    log_success "SSL目录创建完成"
}

# 生成自签名证书
generate_self_signed_cert() {
    log_info "生成自签名SSL证书..."
    
    # 创建配置文件
    cat > "$SSL_DIR/openssl.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = CN
ST = Beijing
L = Beijing
O = Community Governance
OU = IT Department
CN = $SERVER_IP

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = $DOMAIN_NAME
DNS.3 = *.governance.local
IP.1 = 127.0.0.1
IP.2 = $SERVER_IP
EOF

    # 生成私钥
    log_info "生成私钥..."
    openssl genrsa -out "$SSL_DIR/key.pem" 2048
    
    # 生成证书签名请求
    log_info "生成证书签名请求..."
    openssl req -new -key "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.csr" -config "$SSL_DIR/openssl.conf"
    
    # 生成自签名证书
    log_info "生成自签名证书..."
    openssl x509 -req -in "$SSL_DIR/cert.csr" -signkey "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" -days 365 -extensions v3_req -extfile "$SSL_DIR/openssl.conf"
    
    # 复制到Nginx目录
    cp "$SSL_DIR/cert.pem" "$NGINX_SSL_DIR/"
    cp "$SSL_DIR/key.pem" "$NGINX_SSL_DIR/"
    
    # 设置权限
    chmod 600 "$SSL_DIR/key.pem" "$NGINX_SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem" "$NGINX_SSL_DIR/cert.pem"
    
    # 清理临时文件
    rm -f "$SSL_DIR/cert.csr" "$SSL_DIR/openssl.conf"
    
    log_success "自签名SSL证书生成完成"
}

# 验证证书
verify_certificate() {
    log_info "验证SSL证书..."
    
    # 检查证书文件
    if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
        log_error "SSL证书文件不存在"
        return 1
    fi
    
    # 验证证书内容
    log_info "证书信息："
    openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -E "(Subject:|DNS:|IP Address:)"
    
    # 验证证书和私钥匹配
    cert_hash=$(openssl x509 -noout -modulus -in "$SSL_DIR/cert.pem" | openssl md5)
    key_hash=$(openssl rsa -noout -modulus -in "$SSL_DIR/key.pem" | openssl md5)
    
    if [ "$cert_hash" = "$key_hash" ]; then
        log_success "证书和私钥匹配"
    else
        log_error "证书和私钥不匹配"
        return 1
    fi
    
    log_success "SSL证书验证完成"
}

# 显示使用说明
show_usage_info() {
    log_info "SSL证书使用说明："
    echo ""
    echo "证书文件位置："
    echo "  应用证书: $SSL_DIR/cert.pem"
    echo "  应用私钥: $SSL_DIR/key.pem"
    echo "  Nginx证书: $NGINX_SSL_DIR/cert.pem"
    echo "  Nginx私钥: $NGINX_SSL_DIR/key.pem"
    echo ""
    echo "HTTPS访问地址："
    echo "  https://$SERVER_IP:8443 (应用直接访问)"
    echo "  https://$SERVER_IP:443 (通过Nginx代理)"
    echo ""
    log_warning "注意事项："
    echo "1. 这是自签名证书，浏览器会显示安全警告"
    echo "2. 生产环境建议使用CA签发的正式证书"
    echo "3. 可以使用Let's Encrypt获取免费的正式证书"
    echo ""
    echo "获取Let's Encrypt证书的命令："
    echo "  certbot certonly --standalone -d $SERVER_IP"
}

# 主函数
main() {
    log_info "开始生成SSL证书..."
    log_info "服务器IP: $SERVER_IP"
    
    # 检查openssl命令
    if ! command -v openssl &> /dev/null; then
        log_error "openssl 命令未找到，请先安装 openssl"
        exit 1
    fi
    
    create_ssl_directories
    generate_self_signed_cert
    verify_certificate
    show_usage_info
    
    log_success "SSL证书生成完成！"
}

# 处理命令行参数
case "${1:-generate}" in
    "generate")
        main
        ;;
    "verify")
        verify_certificate
        ;;
    "clean")
        log_info "清理SSL证书文件..."
        rm -rf "$SSL_DIR" "$NGINX_SSL_DIR"
        log_success "SSL证书文件已清理"
        ;;
    *)
        echo "用法: $0 {generate|verify|clean}"
        echo "  generate - 生成SSL证书（默认）"
        echo "  verify   - 验证SSL证书"
        echo "  clean    - 清理SSL证书文件"
        exit 1
        ;;
esac
