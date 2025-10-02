"""
数据库初始化工具
用于创建数据库表和初始数据
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models import Base
from app.core.logging import get_logger

logger = get_logger(__name__)


async def create_tables():
    """创建所有数据库表"""
    try:
        # 创建异步引擎
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("数据库表创建成功")
        
        # 关闭引擎
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


async def drop_tables():
    """删除所有数据库表（谨慎使用）"""
    try:
        # 创建异步引擎
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        
        # 删除所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
        logger.info("数据库表删除成功")
        
        # 关闭引擎
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


async def reset_database():
    """重置数据库（删除后重新创建）"""
    logger.info("开始重置数据库...")
    await drop_tables()
    await create_tables()
    logger.info("数据库重置完成")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python -m app.core.database_init create  # 创建表")
        print("  python -m app.core.database_init drop    # 删除表")
        print("  python -m app.core.database_init reset   # 重置数据库")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        asyncio.run(create_tables())
    elif command == "drop":
        asyncio.run(drop_tables())
    elif command == "reset":
        asyncio.run(reset_database())
    else:
        print(f"未知命令: {command}")
        sys.exit(1)