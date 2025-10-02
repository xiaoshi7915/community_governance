"""
事件相关的Pydantic模型
用于API请求和响应的数据验证
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

from app.models.event import EventStatus, EventPriority, MediaType


class MediaFileInfo(BaseModel):
    """媒体文件信息模型"""
    media_type: MediaType = Field(..., description="媒体类型")
    file_url: str = Field(..., description="文件URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    file_name: Optional[str] = Field(None, description="原始文件名")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文件元数据")


class CreateEventRequest(BaseModel):
    """创建事件请求模型"""
    event_type: str = Field(..., min_length=1, max_length=100, description="事件类型")
    title: str = Field(..., min_length=1, max_length=200, description="事件标题")
    description: Optional[str] = Field(None, max_length=2000, description="事件描述")
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    media_files: Optional[List[MediaFileInfo]] = Field(None, description="媒体文件列表")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI分析结果")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI识别置信度")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('事件标题不能为空')
        return v.strip()
    
    @validator('event_type')
    def validate_event_type(cls, v):
        if not v.strip():
            raise ValueError('事件类型不能为空')
        return v.strip()


class UpdateEventRequest(BaseModel):
    """更新事件请求模型"""
    event_type: Optional[str] = Field(None, min_length=1, max_length=100, description="事件类型")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="事件标题")
    description: Optional[str] = Field(None, max_length=2000, description="事件描述")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    address: Optional[str] = Field(None, max_length=500, description="详细地址")
    priority: Optional[EventPriority] = Field(None, description="优先级")
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('事件标题不能为空')
        return v.strip() if v else v
    
    @validator('event_type')
    def validate_event_type(cls, v):
        if v is not None and not v.strip():
            raise ValueError('事件类型不能为空')
        return v.strip() if v else v


class UpdateEventStatusRequest(BaseModel):
    """更新事件状态请求模型"""
    status: EventStatus = Field(..., description="新状态")
    description: Optional[str] = Field(None, max_length=500, description="状态变更描述")


class EventListRequest(BaseModel):
    """事件列表查询请求模型"""
    event_types: Optional[List[str]] = Field(None, description="事件类型过滤")
    statuses: Optional[List[EventStatus]] = Field(None, description="状态过滤")
    priorities: Optional[List[EventPriority]] = Field(None, description="优先级过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    search_query: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="中心点纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="中心点经度")
    radius_meters: Optional[int] = Field(None, ge=1, le=50000, description="搜索半径（米）")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


class EventTimelineResponse(BaseModel):
    """事件时间线响应模型"""
    id: str = Field(..., description="时间线ID")
    event_id: str = Field(..., description="事件ID")
    operator_id: Optional[str] = Field(None, description="操作者ID")
    operator_name: Optional[str] = Field(None, description="操作者姓名")
    status: str = Field(..., description="状态")
    description: Optional[str] = Field(None, description="描述")
    created_at: str = Field(..., description="创建时间")


class EventMediaResponse(BaseModel):
    """事件媒体响应模型"""
    id: str = Field(..., description="媒体ID")
    event_id: str = Field(..., description="事件ID")
    media_type: str = Field(..., description="媒体类型")
    file_url: str = Field(..., description="文件URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    file_size: Optional[int] = Field(None, description="文件大小")
    file_name: Optional[str] = Field(None, description="文件名")
    file_metadata: Optional[Dict[str, Any]] = Field(None, description="文件元数据")
    created_at: str = Field(..., description="创建时间")


class EventResponse(BaseModel):
    """事件响应模型"""
    id: str = Field(..., description="事件ID")
    user_id: str = Field(..., description="用户ID")
    user_name: Optional[str] = Field(None, description="用户姓名")
    event_type: str = Field(..., description="事件类型")
    title: str = Field(..., description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    location_lat: float = Field(..., description="纬度")
    location_lng: float = Field(..., description="经度")
    location_address: Optional[str] = Field(None, description="详细地址")
    priority: str = Field(..., description="优先级")
    status: str = Field(..., description="状态")
    confidence: Optional[float] = Field(None, description="AI识别置信度")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI分析结果")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    media_count: Optional[int] = Field(None, description="媒体文件数量")
    distance_meters: Optional[float] = Field(None, description="距离（米）")


class EventDetailResponse(EventResponse):
    """事件详情响应模型"""
    user_phone: Optional[str] = Field(None, description="用户手机号")
    timelines: List[EventTimelineResponse] = Field(..., description="时间线列表")
    media_files: List[EventMediaResponse] = Field(..., description="媒体文件列表")
    location_details: Optional[Dict[str, Any]] = Field(None, description="详细地理位置信息")
    status_history: Optional[Dict[str, Any]] = Field(None, description="状态历史摘要")


class EventListResponse(BaseModel):
    """事件列表响应模型"""
    events: List[EventResponse] = Field(..., description="事件列表")
    pagination: Dict[str, Any] = Field(..., description="分页信息")
    filters: Dict[str, Any] = Field(..., description="过滤条件")


class CreateEventResponse(BaseModel):
    """创建事件响应模型"""
    event_id: str = Field(..., description="事件ID")
    event: EventResponse = Field(..., description="事件信息")
    location_address: Optional[str] = Field(None, description="解析的地址")
    location_confidence: Optional[float] = Field(None, description="地址置信度")
    priority: str = Field(..., description="自动调整的优先级")
    media_count: int = Field(..., description="媒体文件数量")
    message: str = Field(..., description="创建结果消息")


class UpdateEventResponse(BaseModel):
    """更新事件响应模型"""
    event_id: str = Field(..., description="事件ID")
    updated_fields: List[str] = Field(..., description="更新的字段列表")
    event: EventResponse = Field(..., description="更新后的事件信息")
    message: str = Field(..., description="更新结果消息")


class DeleteEventResponse(BaseModel):
    """删除事件响应模型"""
    event_id: str = Field(..., description="事件ID")
    deleted_files_count: int = Field(..., description="删除的文件数量")
    failed_files_count: int = Field(..., description="删除失败的文件数量")
    message: str = Field(..., description="删除结果消息")


class EventStatusUpdateResponse(BaseModel):
    """事件状态更新响应模型"""
    event_id: str = Field(..., description="事件ID")
    old_status: str = Field(..., description="原状态")
    new_status: str = Field(..., description="新状态")
    timeline_id: str = Field(..., description="时间线记录ID")
    message: str = Field(..., description="更新结果消息")


class EventTimelineListResponse(BaseModel):
    """事件时间线列表响应模型"""
    event_id: str = Field(..., description="事件ID")
    timelines: List[EventTimelineResponse] = Field(..., description="时间线列表")
    total_count: int = Field(..., description="总记录数")