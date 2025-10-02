"""
数据库连接配置
支持PostgreSQL异步连接
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

# 处理数据库URL，确保使用正确的异步驱动
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# 创建异步数据库引擎
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=30,
    poolclass=NullPool if "sqlite" in database_url else None,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖注入函数
    用于FastAPI的Depends
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库，创建所有表"""
    # 确保所有模型都被导入
    from app.models import Base, User, Event, EventTimeline, EventMedia
    
    async with engine.begin() as conn:
        # 在测试环境下删除所有表后重新创建
        if settings.ENVIRONMENT == "test":
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)