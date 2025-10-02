"""
Redis客户端配置
提供缓存和会话存储功能
"""
import json
import logging
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis异步客户端封装"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """获取Redis客户端实例"""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # 测试连接
                await self._client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.error(f"Redis连接失败: {str(e)}")
                # 如果Redis不可用，使用内存缓存作为降级方案
                self._client = None
                raise
        
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET操作失败: {str(e)}")
            return None
    
    async def set(self, key: str, value: Union[str, int, float], ex: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            client = await self.get_client()
            return await client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET操作失败: {str(e)}")
            return False
    
    async def setex(self, key: str, time: int, value: Union[str, int, float]) -> bool:
        """设置带过期时间的缓存值"""
        try:
            client = await self.get_client()
            return await client.setex(key, time, value)
        except Exception as e:
            logger.error(f"Redis SETEX操作失败: {str(e)}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """删除缓存键"""
        try:
            client = await self.get_client()
            return await client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE操作失败: {str(e)}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS操作失败: {str(e)}")
            return False
    
    async def keys(self, pattern: str) -> list:
        """获取匹配模式的所有键"""
        try:
            client = await self.get_client()
            return await client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS操作失败: {str(e)}")
            return []
    
    async def expire(self, key: str, time: int) -> bool:
        """设置键的过期时间"""
        try:
            client = await self.get_client()
            return await client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis EXPIRE操作失败: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        try:
            client = await self.get_client()
            return await client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL操作失败: {str(e)}")
            return -1
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段值"""
        try:
            client = await self.get_client()
            return await client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET操作失败: {str(e)}")
            return None
    
    async def hset(self, name: str, key: str, value: Union[str, int, float]) -> bool:
        """设置哈希表字段值"""
        try:
            client = await self.get_client()
            return await client.hset(name, key, value) >= 0
        except Exception as e:
            logger.error(f"Redis HSET操作失败: {str(e)}")
            return False
    
    async def hgetall(self, name: str) -> dict:
        """获取哈希表所有字段和值"""
        try:
            client = await self.get_client()
            return await client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL操作失败: {str(e)}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表字段"""
        try:
            client = await self.get_client()
            return await client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis HDEL操作失败: {str(e)}")
            return 0
    
    async def close(self):
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis连接已关闭")


# 创建全局Redis客户端实例
redis_client = RedisClient()


# 便捷函数，用于向后兼容
async def get_redis() -> RedisClient:
    """获取Redis客户端实例"""
    return redis_client