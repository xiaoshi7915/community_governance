"""
配置验证器
验证应用程序配置的完整性和有效性
"""
import os
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_database_url(self, database_url: str) -> bool:
        """验证数据库URL格式"""
        try:
            parsed = urlparse(database_url)
            
            # 检查协议
            if not parsed.scheme.startswith('postgresql'):
                self.errors.append(f"数据库URL协议无效: {parsed.scheme}")
                return False
            
            # 检查主机和端口
            if not parsed.hostname:
                self.errors.append("数据库URL缺少主机名")
                return False
            
            if not parsed.port:
                self.warnings.append("数据库URL未指定端口，将使用默认端口")
            
            # 检查数据库名
            if not parsed.path or parsed.path == '/':
                self.errors.append("数据库URL缺少数据库名")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"数据库URL格式错误: {e}")
            return False
    
    def validate_redis_url(self, redis_url: str) -> bool:
        """验证Redis URL格式"""
        try:
            parsed = urlparse(redis_url)
            
            # 检查协议
            if parsed.scheme not in ['redis', 'rediss']:
                self.errors.append(f"Redis URL协议无效: {parsed.scheme}")
                return False
            
            # 检查主机
            if not parsed.hostname:
                self.errors.append("Redis URL缺少主机名")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Redis URL格式错误: {e}")
            return False
    
    def validate_secret_key(self, secret_key: str, key_name: str = "SECRET_KEY") -> bool:
        """验证密钥强度"""
        if not secret_key:
            self.errors.append(f"{key_name}不能为空")
            return False
        
        if len(secret_key) < 32:
            self.errors.append(f"{key_name}长度不能少于32位")
            return False
        
        # 检查是否使用默认值
        default_keys = [
            "your-secret-key-change-in-production",
            "jwt-secret-key-change-in-production",
            "secret-key",
            "change-me"
        ]
        
        if secret_key.lower() in [key.lower() for key in default_keys]:
            self.errors.append(f"{key_name}不能使用默认值，请更改为安全的密钥")
            return False
        
        return True
    
    def validate_cors_origins(self, cors_origins: List[str], environment: str) -> bool:
        """验证CORS配置"""
        if not cors_origins:
            if environment == "production":
                self.errors.append("生产环境必须配置CORS来源")
                return False
            else:
                self.warnings.append("未配置CORS来源")
        
        # 检查生产环境是否使用通配符
        if environment == "production" and "*" in cors_origins:
            self.errors.append("生产环境不应使用通配符(*)作为CORS来源")
            return False
        
        # 验证URL格式
        for origin in cors_origins:
            if origin != "*" and not self._is_valid_url(origin):
                self.warnings.append(f"CORS来源格式可能无效: {origin}")
        
        return True
    
    def validate_file_upload_config(self, max_file_size: int, allowed_types: List[str]) -> bool:
        """验证文件上传配置"""
        # 检查文件大小限制
        if max_file_size <= 0:
            self.errors.append("最大文件大小必须大于0")
            return False
        
        if max_file_size > 100 * 1024 * 1024:  # 100MB
            self.warnings.append("最大文件大小超过100MB，可能影响性能")
        
        # 检查允许的文件类型
        if not allowed_types:
            self.warnings.append("未配置允许的文件类型")
        
        return True
    
    def validate_environment_config(self, environment: str) -> bool:
        """验证环境配置"""
        valid_environments = ["development", "testing", "production"]
        
        if environment not in valid_environments:
            self.errors.append(f"无效的环境配置: {environment}，有效值: {valid_environments}")
            return False
        
        return True
    
    def validate_aliyun_config(self, access_key_id: str, access_key_secret: str, environment: str) -> bool:
        """验证阿里云配置"""
        if environment == "production":
            if not access_key_id:
                self.errors.append("生产环境必须配置阿里云Access Key ID")
                return False
            
            if not access_key_secret:
                self.errors.append("生产环境必须配置阿里云Access Key Secret")
                return False
        
        # 检查是否使用示例密钥
        example_keys = [
            "LTAI5t7DeLJNLc8gNqEBDfnD",
            "LTAI5tJpFaLSz5F6uQqPD9EN",
            "your-access-key-id",
            "your-access-key-secret"
        ]
        
        if access_key_id in example_keys:
            self.errors.append("不能使用示例Access Key ID")
            return False
        
        return True
    
    def _is_valid_url(self, url: str) -> bool:
        """检查URL格式是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def validate_all(self, settings) -> Dict[str, Any]:
        """验证所有配置"""
        self.errors.clear()
        self.warnings.clear()
        
        # 验证环境配置
        self.validate_environment_config(settings.ENVIRONMENT)
        
        # 验证数据库配置
        self.validate_database_url(settings.DATABASE_URL)
        
        # 验证Redis配置
        self.validate_redis_url(settings.REDIS_URL)
        
        # 验证密钥配置
        self.validate_secret_key(settings.SECRET_KEY, "SECRET_KEY")
        self.validate_secret_key(settings.JWT_SECRET_KEY, "JWT_SECRET_KEY")
        
        # 验证CORS配置
        self.validate_cors_origins(settings.BACKEND_CORS_ORIGINS, settings.ENVIRONMENT)
        
        # 验证文件上传配置
        self.validate_file_upload_config(
            settings.MAX_FILE_SIZE,
            settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES
        )
        
        # 验证阿里云配置
        self.validate_aliyun_config(
            settings.ALIYUN_OSS_ACCESS_KEY_ID,
            settings.ALIYUN_OSS_ACCESS_KEY_SECRET,
            settings.ENVIRONMENT
        )
        
        # 记录验证结果
        if self.errors:
            for error in self.errors:
                logger.error(f"配置验证错误: {error}")
        
        if self.warnings:
            for warning in self.warnings:
                logger.warning(f"配置验证警告: {warning}")
        
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy()
        }


# 创建全局配置验证器实例
config_validator = ConfigValidator()


def validate_config(settings) -> Dict[str, Any]:
    """验证配置的便捷函数"""
    return config_validator.validate_all(settings)
