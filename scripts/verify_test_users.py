"""
验证测试用户脚本
检查测试用户是否正确创建
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import PasswordManager

async def verify_test_users():
    """验证测试用户"""
    async with AsyncSessionLocal() as session:
        try:
            # 查询所有测试用户
            result = await session.execute(
                select(User).where(User.phone.like('1380000000%'))
            )
            users = result.scalars().all()
            
            print("🔍 测试用户验证结果:")
            print("=" * 60)
            
            if not users:
                print("❌ 没有找到测试用户")
                return
            
            for user in users:
                print(f"✅ 用户: {user.name}")
                print(f"   手机号: {user.phone}")
                print(f"   角色: {user.role}")
                print(f"   状态: {'激活' if user.is_active else '未激活'}")
                print(f"   创建时间: {user.created_at}")
                
                # 验证密码
                password_valid = PasswordManager.verify_password("123456", user.password_hash)
                print(f"   密码验证: {'✅ 通过' if password_valid else '❌ 失败'}")
                print("-" * 40)
            
            print(f"\n📊 总计: {len(users)} 个测试用户")
            
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(verify_test_users())