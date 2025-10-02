"""
数据库连接配置
支持PostgreSQL异步连接
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 在调试模式下显示SQL语句
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    pool_pre_ping=True,  # 连接前检查连接是否有效
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