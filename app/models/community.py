"""
社区模型
包含社区基本信息和地理位置
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base


class Community(Base):
    """社区模型"""
    
    __tablename__ = "communities"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 基本信息
    name = Column(String(200), nullable=False, index=True, comment="社区名称")
    address = Column(String(500), nullable=True, comment="详细地址")
    description = Column(Text, nullable=True, comment="社区描述")
    
    # 地理位置信息
    latitude = Column(Float, nullable=True, comment="纬度")
    longitude = Column(Float, nullable=True, comment="经度")
    
    # 状态字段
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<Community(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "name": self.name,
            "address": self.address,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
