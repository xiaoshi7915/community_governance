"""
缓存管理器
提供统一的缓存接口，支持Redis和内存缓存
"""
import json
import pickle
import hashlib
from typing import Any, Dict, Optional, Union, Callable
from datetime import datetime, timedelta, timezone
from app.core.redis import redis_service
from app.core.logging import get_logger
from app.core.retry import async_retry, REDIS_RETRY_CONFIG

logger = get_logger(__name__)


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = 1000  # 最大缓存条目数
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        
        # 检查是否过期
        if item.get("expires_at") and datetime.now(timezone.utc) > item["expires_at"]:
            del self._cache[key]
            return None
        
        return item["value"]
    
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """设置缓存值"""
        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].get("created_at", datetime.min))
            del self._cache[oldest_key]
        
        expires_at = None
        if expire_seconds:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self.get(key) is not None
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        self._cache.clear()
        return True


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._memory_cache = MemoryCache()
        self._use_redis = True
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # 对复杂对象生成哈希
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # 添加关键字参数
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True, default=str)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])
        
        return ":".join(key_parts)
    
    @async_retry(config=REDIS_RETRY_CONFIG)
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            # 优先从Redis获取
            if self._use_redis:
                value = await redis_service.get(key)
                if value is not None:
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # 如果不是JSON，尝试pickle反序列化
                        try:
                            return pickle.loads(value.encode('latin1'))
                        except:
                            return value
            
            # 从内存缓存获取
            return await self._memory_cache.get(key)
            
        except Exception as e:
            logger.warning(f"缓存获取失败，使用内存缓存: {e}")
            return await self._memory_cache.get(key)
    
    @async_retry(config=REDIS_RETRY_CONFIG)
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                # 使用pickle序列化复杂对象
                serialized_value = pickle.dumps(value).decode('latin1')
            
            # 优先存储到Redis
            if self._use_redis:
                success = await redis_service.set(key, serialized_value, expire_seconds)
                if success:
                    return True
            
            # 存储到内存缓存
            return await self._memory_cache.set(key, value, expire_seconds)
            
        except Exception as e:
            logger.warning(f"缓存设置失败，使用内存缓存: {e}")
            return await self._memory_cache.set(key, value, expire_seconds)
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        redis_success = True
        memory_success = True
        
        try:
            if self._use_redis:
                redis_success = await redis_service.delete(key)
        except Exception as e:
            logger.warning(f"Redis缓存删除失败: {e}")
            redis_success = False
        
        try:
            memory_success = await self._memory_cache.delete(key)
        except Exception as e:
            logger.warning(f"内存缓存删除失败: {e}")
            memory_success = False
        
        return redis_success or memory_success
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            if self._use_redis:
                exists = await redis_service.exists(key)
                if exists:
                    return True
        except Exception as e:
            logger.warning(f"Redis缓存检查失败: {e}")
        
        return await self._memory_cache.exists(key)
    
    def cache_result(
        self,
        prefix: str,
        expire_seconds: Optional[int] = 3600,
        key_generator: Optional[Callable] = None
    ):
        """
        缓存函数结果的装饰器
        
        Args:
            prefix: 缓存键前缀
            expire_seconds: 过期时间（秒）
            key_generator: 自定义键生成函数
        """
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result
                
                # 执行函数并缓存结果
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, expire_seconds)
                logger.debug(f"缓存设置: {cache_key}")
                
                return result
            
            return wrapper
        return decorator


# 创建全局缓存管理器实例
cache_manager = CacheManager()


# 便捷函数
async def get_cache(key: str) -> Optional[Any]:
    """获取缓存值"""
    return await cache_manager.get(key)


async def set_cache(key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
    """设置缓存值"""
    return await cache_manager.set(key, value, expire_seconds)


async def delete_cache(key: str) -> bool:
    """删除缓存值"""
    return await cache_manager.delete(key)


def cache_result(prefix: str, expire_seconds: Optional[int] = 3600):
    """缓存函数结果装饰器"""
    return cache_manager.cache_result(prefix, expire_seconds)
