"""
Redis连接配置
用于缓存和会话存储
"""
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

# Redis连接池
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """初始化Redis连接"""
    global redis_pool, redis_client
    
    try:
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # 测试连接
        await redis_client.ping()
        print("Redis连接成功")
    except Exception as e:
        print(f"Redis连接失败，将使用内存缓存: {e}")
        # 如果Redis连接失败，设置为None，应用将使用内存缓存
        redis_client = None
        redis_pool = None


async def close_redis():
    """关闭Redis连接"""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
    
    if redis_pool:
        await redis_pool.disconnect()


async def get_redis() -> redis.Redis:
    """获取Redis客户端实例"""
    if redis_client is None:
        await init_redis()
    return redis_client


class RedisService:
    """Redis服务封装类"""
    
    def __init__(self):
        self.redis = None
    
    async def get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis
    
    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """设置键值对"""
        client = await self.get_client()
        return await client.set(key, value, ex=expire)
    
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        client = await self.get_client()
        return await client.get(key)
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        client = await self.get_client()
        return await client.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        client = await self.get_client()
        return await client.exists(key) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        client = await self.get_client()
        return await client.expire(key, seconds)


# 创建全局Redis服务实例
redis_service = RedisService()