#!/bin/bash
# 开发环境启动脚本

echo "启动开发环境..."

# 检查是否存在.env文件
if [ ! -f .env ]; then
    echo "复制环境配置文件..."
    cp .env.development .env
fi

# 启动Docker服务
echo "启动数据库和Redis服务..."
docker-compose up -d db redis

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 运行数据库迁移
echo "运行数据库迁移..."
alembic upgrade head

# 启动应用
echo "启动应用..."
python run.py