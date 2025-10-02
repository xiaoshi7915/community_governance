-- 数据库初始化脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- 创建数据库（如果不存在）
SELECT 'CREATE DATABASE governance_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'governance_dev')\gexec

SELECT 'CREATE DATABASE governance_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'governance_test')\gexec