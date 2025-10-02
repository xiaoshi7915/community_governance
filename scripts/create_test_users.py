#!/usr/bin/env python3
"""
创建测试用户脚本
创建不同权限级别的测试账号
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import PasswordManager

async def create_test_users():
    """创建测试用户"""
    
    # 测试用户数据
    test_users = [
        {
            "phone": "13800000001",
            "password": "123456",
            "name": "张三",
            "role": "citizen",

            "description": "普通市民 - 可以上报和查看自己的事件"
        },
        {
            "phone": "13800000002", 
            "password": "123456",
            "name": "李四",
            "role": "grid_worker",

            "description": "网格员 - 可以处理和分配事件"
        },
        {
            "phone": "13800000003",
            "password": "123456", 
            "name": "王五",
            "role": "manager",

            "description": "管理员 - 可以管理所有事件和查看统计"
        },
        {
            "phone": "13800000004",
            "password": "123456",
            "name": "赵六", 
            "role": "decision_maker",

            "description": "决策者 - 拥有所有权限"
        }
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            for user_data in test_users:
                # 检查用户是否已存在
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.phone == user_data["phone"])
                )
                existing_user = result.scalar_one_or_none()
                if existing_user:
                    print(f"用户 {user_data['phone']} 已存在，跳过创建")
                    continue
                
                # 创建新用户
                user = User(
                    phone=user_data["phone"],
                    password_hash=PasswordManager.hash_password(user_data["password"]),
                    name=user_data["name"],
                    role=user_data["role"],
                    is_active=True
                )
                
                session.add(user)
                print(f"创建用户: {user_data['name']} ({user_data['phone']}) - {user_data['description']}")
            
            await session.commit()
            print("\n测试用户创建完成！")
            print("\n登录信息:")
            print("=" * 50)
            for user_data in test_users:
                print(f"角色: {user_data['description']}")
                print(f"手机号: {user_data['phone']}")
                print(f"密码: {user_data['password']}")
                print("-" * 30)
                
        except Exception as e:
            await session.rollback()
            print(f"创建用户失败: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(create_test_users())