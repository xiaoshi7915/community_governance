"""
AI服务相关的数据模型
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AIAnalysisRequest(BaseModel):
    """AI分析请求模型"""
    media_url: str = Field(..., description="媒体文件URL")
    media_type: str = Field(..., description="媒体类型", pattern="^(image|video)$")
    
    @validator('media_url')
    def validate_media_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('媒体URL必须是有效的HTTP/HTTPS地址')
        return v


class ImageAnalysisRequest(BaseModel):
    """图像分析请求模型"""
    image_url: str = Field(..., description="图像URL")
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('图像URL必须是有效的HTTP/HTTPS地址')
        return v


class VideoAnalysisRequest(BaseModel):
    """视频分析请求模型"""
    video_url: str = Field(..., description="视频URL")
    max_frames: Optional[int] = Field(5, description="最大提取帧数", ge=1, le=10)
    
    @validator('video_url')
    def validate_video_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('视频URL必须是有效的HTTP/HTTPS地址')
        return v


class VideoFrameExtractionRequest(BaseModel):
    """视频关键帧提取请求模型"""
    video_url: str = Field(..., description="视频URL")
    max_frames: Optional[int] = Field(5, description="最大提取帧数", ge=1, le=10)
    
    @validator('video_url')
    def validate_video_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('视频URL必须是有效的HTTP/HTTPS地址')
        return v


class EventClassificationRequest(BaseModel):
    """事件分类请求模型"""
    analysis_result: Dict[str, Any] = Field(..., description="AI分析结果")
    
    @validator('analysis_result')
    def validate_analysis_result(cls, v):
        if not isinstance(v, dict):
            raise ValueError('分析结果必须是字典格式')
        return v


class AIAnalysisResponse(BaseModel):
    """AI分析响应模型"""
    event_type: str = Field(..., description="事件类型")
    description: str = Field(..., description="事件描述")
    confidence: float = Field(..., description="置信度", ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(..., description="详细信息")
    timestamp: datetime = Field(..., description="分析时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventClassificationResponse(BaseModel):
    """事件分类响应模型"""
    primary_type: str = Field(..., description="主要事件类型")
    secondary_type: Optional[str] = Field(None, description="次要事件类型")
    confidence: float = Field(..., description="分类置信度", ge=0.0, le=1.0)
    suggested_priority: str = Field(..., description="建议优先级")
    keywords: List[str] = Field(..., description="关键词列表")


class VideoFrameExtractionResponse(BaseModel):
    """视频关键帧提取响应模型"""
    frame_urls: List[str] = Field(..., description="关键帧URL列表")
    frame_count: int = Field(..., description="提取的帧数量")
    video_info: Dict[str, Any] = Field(..., description="视频信息")


class EventTypeInfo(BaseModel):
    """事件类型信息模型"""
    type_name: str = Field(..., description="类型名称")
    keywords: List[str] = Field(..., description="关键词")
    priority: str = Field(..., description="默认优先级")
    category: str = Field(..., description="类别")
    description: Optional[str] = Field(None, description="类型描述")


class EventTypesResponse(BaseModel):
    """事件类型列表响应模型"""
    event_types: List[EventTypeInfo] = Field(..., description="事件类型列表")
    total_count: int = Field(..., description="总数量")


class AIServiceStatusResponse(BaseModel):
    """AI服务状态响应模型"""
    service_available: bool = Field(..., description="服务是否可用")
    fallback_enabled: bool = Field(..., description="是否启用降级模式")
    last_check_time: datetime = Field(..., description="最后检查时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchAnalysisRequest(BaseModel):
    """批量分析请求模型"""
    media_items: List[Dict[str, str]] = Field(..., description="媒体项目列表")
    
    @validator('media_items')
    def validate_media_items(cls, v):
        if not v:
            raise ValueError('媒体项目列表不能为空')
        
        for item in v:
            if not isinstance(item, dict):
                raise ValueError('媒体项目必须是字典格式')
            if 'url' not in item or 'type' not in item:
                raise ValueError('媒体项目必须包含url和type字段')
            if item['type'] not in ['image', 'video']:
                raise ValueError('媒体类型必须是image或video')
        
        return v


class BatchAnalysisResponse(BaseModel):
    """批量分析响应模型"""
    results: List[AIAnalysisResponse] = Field(..., description="分析结果列表")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_items: List[Dict[str, str]] = Field(..., description="失败项目列表")


class AIAnalysisHistoryResponse(BaseModel):
    """AI分析历史响应模型"""
    analysis_id: str = Field(..., description="分析ID")
    media_url: str = Field(..., description="媒体URL")
    media_type: str = Field(..., description="媒体类型")
    result: AIAnalysisResponse = Field(..., description="分析结果")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIModelInfo(BaseModel):
    """AI模型信息模型"""
    model_name: str = Field(..., description="模型名称")
    model_version: str = Field(..., description="模型版本")
    capabilities: List[str] = Field(..., description="模型能力")
    supported_formats: List[str] = Field(..., description="支持的格式")
    max_file_size: int = Field(..., description="最大文件大小（字节）")


class AIServiceInfoResponse(BaseModel):
    """AI服务信息响应模型"""
    service_name: str = Field(..., description="服务名称")
    service_version: str = Field(..., description="服务版本")
    provider: str = Field(..., description="服务提供商")
    models: List[AIModelInfo] = Field(..., description="可用模型列表")
    rate_limits: Dict[str, int] = Field(..., description="速率限制")
    status: AIServiceStatusResponse = Field(..., description="服务状态")


class AsyncAnalysisRequest(BaseModel):
    """异步分析请求模型"""
    media_url: str = Field(..., description="媒体文件URL")
    media_type: str = Field(..., description="媒体类型", pattern="^(image|video)$")
    
    @validator('media_url')
    def validate_media_url(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('媒体URL必须是有效的HTTP/HTTPS地址')
        return v


class AsyncAnalysisResponse(BaseModel):
    """异步分析响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态描述")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    media_url: str = Field(..., description="媒体URL")
    media_type: str = Field(..., description="媒体类型")
    created_at: str = Field(..., description="创建时间")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    failed_at: Optional[str] = Field(None, description="失败时间")
    result: Optional[AIAnalysisResponse] = Field(None, description="分析结果")
    error: Optional[str] = Field(None, description="错误信息")


class CacheStatsResponse(BaseModel):
    """缓存统计响应模型"""
    cache_enabled: bool = Field(..., description="缓存是否启用")
    cache_ttl: int = Field(..., description="缓存TTL（秒）")
    total_keys: int = Field(..., description="总缓存键数")
    hit_rate: Optional[float] = Field(None, description="缓存命中率")
    memory_usage: Optional[str] = Field(None, description="内存使用情况")