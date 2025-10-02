"""
添加用户角色字段的迁移脚本
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def add_role_column():
    """添加role字段到users表"""
    async with AsyncSessionLocal() as db:
        try:
            # 检查role字段是否已存在
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
            """
            result = await db.execute(text(check_column_sql))
            existing_column = result.fetchone()
            
            if existing_column:
                print("✅ role字段已存在，跳过添加")
                return
            
            # 添加role字段
            add_column_sql = """
            ALTER TABLE users 
            ADD COLUMN role VARCHAR(50) DEFAULT 'citizen' NOT NULL
            """
            await db.execute(text(add_column_sql))
            await db.commit()
            
            print("✅ 成功添加role字段到users表")
            
            # 为现有用户设置默认角色
            update_existing_sql = """
            UPDATE users 
            SET role = 'citizen' 
            WHERE role IS NULL OR role = ''
            """
            await db.execute(text(update_existing_sql))
            await db.commit()
            
            print("✅ 为现有用户设置了默认角色")
            
        except Exception as e:
            print(f"❌ 添加role字段失败: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_role_column())