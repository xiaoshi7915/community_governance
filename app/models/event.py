"""
事件相关模型
包含事件核心信息、时间线和媒体文件
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base


class EventPriority(str, Enum):
    """事件优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EventStatus(str, Enum):
    """事件状态枚举"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    REJECTED = "rejected"        # 已拒绝
    CANCELLED = "cancelled"      # 已取消


class MediaType(str, Enum):
    """媒体类型枚举"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class Event(Base):
    """事件模型"""
    
    __tablename__ = "events"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外键
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 事件基本信息
    event_type = Column(String(100), nullable=False, index=True, comment="事件类型")
    title = Column(String(200), nullable=False, comment="事件标题")
    description = Column(Text, nullable=True, comment="事件描述")
    
    # 地理位置信息
    location_lat = Column(Float, nullable=False, comment="纬度")
    location_lng = Column(Float, nullable=False, comment="经度")
    location_address = Column(String(500), nullable=True, comment="详细地址")
    
    # 事件状态和优先级
    priority = Column(
        SQLEnum(EventPriority), 
        default=EventPriority.MEDIUM, 
        nullable=False,
        comment="优先级"
    )
    status = Column(
        SQLEnum(EventStatus), 
        default=EventStatus.PENDING, 
        nullable=False,
        index=True,
        comment="状态"
    )
    
    # AI识别相关
    confidence = Column(Float, default=0.0, comment="AI识别置信度")
    ai_analysis = Column(JSON, nullable=True, comment="AI分析结果")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    # 关系
    user = relationship("User", back_populates="events")
    timelines = relationship("EventTimeline", back_populates="event", cascade="all, delete-orphan")
    media_files = relationship("EventMedia", back_populates="event", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "location_lat": self.location_lat,
            "location_lng": self.location_lng,
            "location_address": self.location_address,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "confidence": self.confidence,
            "ai_analysis": self.ai_analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EventTimeline(Base):
    """事件时间线模型 - 记录事件状态变化历史"""
    
    __tablename__ = "event_timelines"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外键
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # 时间线信息
    status = Column(
        SQLEnum(EventStatus), 
        nullable=False,
        comment="变更后的状态"
    )
    description = Column(Text, nullable=True, comment="状态变更描述")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True,
        comment="创建时间"
    )
    
    # 关系
    event = relationship("Event", back_populates="timelines")
    operator = relationship("User", back_populates="event_timelines")
    
    def __repr__(self):
        return f"<EventTimeline(id={self.id}, event_id={self.event_id}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "operator_id": str(self.operator_id) if self.operator_id else None,
            "status": self.status.value if self.status else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EventMedia(Base):
    """事件媒体文件模型"""
    
    __tablename__ = "event_media"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外键
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    
    # 媒体文件信息
    media_type = Column(
        SQLEnum(MediaType), 
        nullable=False,
        comment="媒体类型"
    )
    file_url = Column(String(500), nullable=False, comment="文件URL")
    thumbnail_url = Column(String(500), nullable=True, comment="缩略图URL")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_name = Column(String(255), nullable=True, comment="原始文件名")
    
    # 元数据
    file_metadata = Column(JSON, nullable=True, comment="文件元数据")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="创建时间"
    )
    
    # 关系
    event = relationship("Event", back_populates="media_files")
    
    def __repr__(self):
        return f"<EventMedia(id={self.id}, event_id={self.event_id}, type={self.media_type})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "media_type": self.media_type.value if self.media_type else None,
            "file_url": self.file_url,
            "thumbnail_url": self.thumbnail_url,
            "file_size": self.file_size,
            "file_name": self.file_name,
            "file_metadata": self.file_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }