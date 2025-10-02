#!/usr/bin/env python3
"""
应用启动入口
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # 检查是否启用SSL
    ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
    ssl_cert_path = os.getenv("SSL_CERT_PATH")
    ssl_key_path = os.getenv("SSL_KEY_PATH")
    https_port = int(os.getenv("HTTPS_PORT", "8443"))
    
    # SSL配置
    ssl_keyfile = None
    ssl_certfile = None
    
    if ssl_enabled and ssl_cert_path and ssl_key_path:
        if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
            ssl_certfile = ssl_cert_path
            ssl_keyfile = ssl_key_path
            print(f"SSL已启用，HTTPS端口: {https_port}")
        else:
            print("SSL证书文件不存在，使用HTTP模式")
    
    # 启动HTTP服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )