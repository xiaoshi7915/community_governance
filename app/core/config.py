"""
应用程序配置管理
支持开发、测试、生产环境的配置
"""
import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序设置"""
    
    # 基础配置
    PROJECT_NAME: str = "基层治理智能体后端系统"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # 环境配置
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:password@localhost:5432/governance_db"
    )
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7天
    
    # CORS配置 - 根据环境动态配置
    BACKEND_CORS_ORIGINS: List[str] = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 根据环境设置CORS
        if self.ENVIRONMENT == "development":
            self.BACKEND_CORS_ORIGINS = [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://192.168.43.249:3000",
                "http://192.168.43.249:8080",
            ]
        elif self.ENVIRONMENT == "production":
            # 生产环境只允许特定域名
            cors_origins = os.getenv("CORS_ORIGINS", "")
            if cors_origins:
                self.BACKEND_CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
            else:
                self.BACKEND_CORS_ORIGINS = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 阿里云OSS配置 - 移除硬编码密钥
    ALIYUN_OSS_ACCESS_KEY_ID: str = os.getenv("ALIYUN_OSS_ACCESS_KEY_ID", "")
    ALIYUN_OSS_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET", "")
    ALIYUN_OSS_BUCKET_NAME: str = os.getenv("ALIYUN_OSS_BUCKET_NAME", "governance-files")
    ALIYUN_OSS_ENDPOINT: str = os.getenv("ALIYUN_OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    
    # 阿里云百炼AI配置
    ALIYUN_AI_API_KEY: str = os.getenv("ALIYUN_AI_API_KEY", "")
    ALIYUN_AI_ENDPOINT: str = os.getenv("ALIYUN_AI_ENDPOINT", "")
    
    # 阿里云短信服务配置 - 移除硬编码密钥
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    
    # 高德地图API配置
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/avi", "video/mov", "video/wmv"]
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 通知服务配置
    PUSH_SERVICE_URL: str = os.getenv("PUSH_SERVICE_URL", "")
    PUSH_SERVICE_KEY: str = os.getenv("PUSH_SERVICE_KEY", "")
    SMS_SERVICE_URL: str = os.getenv("SMS_SERVICE_URL", "")
    SMS_SERVICE_KEY: str = os.getenv("SMS_SERVICE_KEY", "")
    EMAIL_SERVICE_URL: str = os.getenv("EMAIL_SERVICE_URL", "")
    EMAIL_SERVICE_KEY: str = os.getenv("EMAIL_SERVICE_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@governance.com")
    
    # 通知重试配置
    NOTIFICATION_MAX_RETRIES: int = int(os.getenv("NOTIFICATION_MAX_RETRIES", "3"))
    NOTIFICATION_RETRY_DELAY_MINUTES: int = int(os.getenv("NOTIFICATION_RETRY_DELAY_MINUTES", "5"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()

# 验证配置
def validate_settings():
    """验证配置设置"""
    try:
        from app.core.config_validator import validate_config
        validation_result = validate_config(settings)
        
        if not validation_result["valid"]:
            print("配置验证失败:")
            for error in validation_result["errors"]:
                print(f"  错误: {error}")
            
            # 在生产环境下，配置错误应该导致应用启动失败
            if settings.ENVIRONMENT == "production":
                raise RuntimeError("生产环境配置验证失败，应用无法启动")
        
        if validation_result["warnings"]:
            print("配置验证警告:")
            for warning in validation_result["warnings"]:
                print(f"  警告: {warning}")
                
    except ImportError:
        # 如果验证器模块不存在，跳过验证
        pass

# 在模块加载时验证配置
validate_settings()