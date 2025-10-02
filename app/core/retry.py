"""
重试机制工具类
提供异步重试装饰器和重试策略
"""
import asyncio
import functools
import random
from typing import Any, Callable, Optional, Type, Union, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """重试配置类"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions


def async_retry(
    config: Optional[RetryConfig] = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    异步重试装饰器
    
    Args:
        config: 重试配置对象
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
    """
    if config is None:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            exceptions=exceptions
        )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # 最后一次尝试失败，抛出异常
                        logger.error(
                            f"函数 {func.__name__} 重试 {config.max_attempts} 次后仍然失败",
                            error=str(e),
                            function=func.__name__
                        )
                        raise
                    
                    # 计算延迟时间
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # 添加随机抖动
                    if config.jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay:.2f}秒后重试",
                        error=str(e),
                        attempt=attempt + 1,
                        delay=delay,
                        function=func.__name__
                    )
                    
                    await asyncio.sleep(delay)
            
            # 理论上不会到达这里
            raise last_exception
        
        return wrapper
    return decorator


def sync_retry(
    config: Optional[RetryConfig] = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    同步重试装饰器
    
    Args:
        config: 重试配置对象
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
    """
    import time
    
    if config is None:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            exceptions=exceptions
        )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # 最后一次尝试失败，抛出异常
                        logger.error(
                            f"函数 {func.__name__} 重试 {config.max_attempts} 次后仍然失败",
                            error=str(e),
                            function=func.__name__
                        )
                        raise
                    
                    # 计算延迟时间
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # 添加随机抖动
                    if config.jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败，{delay:.2f}秒后重试",
                        error=str(e),
                        attempt=attempt + 1,
                        delay=delay,
                        function=func.__name__
                    )
                    
                    time.sleep(delay)
            
            # 理论上不会到达这里
            raise last_exception
        
        return wrapper
    return decorator


# 预定义的重试配置
DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=5.0,
    exceptions=(Exception,)
)

EXTERNAL_SERVICE_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    exceptions=(Exception,)
)

REDIS_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=0.1,
    max_delay=1.0,
    exceptions=(Exception,)
)
