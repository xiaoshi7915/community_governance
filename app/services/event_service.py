"""
事件管理服务
包含事件的CRUD操作、状态管理、优先级调整和基于地理位置的查询功能
"""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.models.event import Event, EventStatus, EventPriority, EventTimeline, EventMedia, MediaType
from app.models.user import User
from app.services.location_service import location_service, LocationInfo, GeocodingResult
from app.services.oss_service import oss_service
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventService:
    """事件管理服务类"""
    
    def __init__(self):
        self.location_service = location_service
        self.oss_service = oss_service
        
        # 事件类型优先级映射
        self.event_type_priority_map = {
            "安全事故": EventPriority.URGENT,
            "火灾": EventPriority.URGENT,
            "交通事故": EventPriority.HIGH,
            "设施损坏": EventPriority.MEDIUM,
            "环境污染": EventPriority.HIGH,
            "噪音扰民": EventPriority.LOW,
            "垃圾清理": EventPriority.LOW,
            "道路维修": EventPriority.MEDIUM,
            "其他": EventPriority.MEDIUM
        }
        
        # 状态流转规则
        self.status_transitions = {
            EventStatus.PENDING: [EventStatus.PROCESSING, EventStatus.REJECTED, EventStatus.CANCELLED],
            EventStatus.PROCESSING: [EventStatus.COMPLETED, EventStatus.REJECTED, EventStatus.CANCELLED],
            EventStatus.COMPLETED: [],  # 完成状态不能再变更
            EventStatus.REJECTED: [EventStatus.PENDING],  # 被拒绝的可以重新提交
            EventStatus.CANCELLED: []  # 取消状态不能再变更
        }
    
    async def create_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        address: Optional[str] = None,
        media_files: Optional[List[Dict[str, Any]]] = None,
        ai_analysis: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        创建事件 - 完整的事件信息处理
        
        Args:
            user_id: 用户ID
            event_type: 事件类型
            title: 事件标题
            description: 事件描述
            latitude: 纬度
            longitude: 经度
            address: 地址（可选）
            media_files: 媒体文件列表
            ai_analysis: AI分析结果
            confidence: AI识别置信度
            db: 数据库会话
            
        Returns:
            Dict: 创建结果
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            # 如果没有提供地址，尝试逆地理编码获取地址
            final_address = address
            location_confidence = confidence or 1.0
            
            if not address:
                logger.info(f"正在为坐标 ({latitude}, {longitude}) 解析地址")
                geocode_result = await self.location_service.reverse_geocode(latitude, longitude)
                
                if geocode_result.success and geocode_result.location_info:
                    final_address = geocode_result.location_info.formatted_address
                    location_confidence = min(location_confidence, geocode_result.location_info.confidence)
                    logger.info(f"地址解析成功: {final_address}")
                else:
                    logger.warning(f"地址解析失败: {geocode_result.error_message}")
                    final_address = f"坐标: {latitude}, {longitude}"
                    location_confidence = 0.0
            
            # 自动调整优先级
            priority = self._determine_priority(event_type, ai_analysis)
            
            # 创建事件记录
            event = Event(
                user_id=user_id,
                event_type=event_type,
                title=title,
                description=description,
                location_lat=latitude,
                location_lng=longitude,
                location_address=final_address,
                priority=priority,
                status=EventStatus.PENDING,
                confidence=location_confidence,
                ai_analysis=ai_analysis
            )
            
            db.add(event)
            await db.flush()  # 获取事件ID
            
            # 创建初始时间线记录
            timeline = EventTimeline(
                event_id=event.id,
                status=EventStatus.PENDING,
                description="事件已创建",
                operator_id=user_id
            )
            db.add(timeline)
            
            # 处理媒体文件
            media_records = []
            if media_files:
                for media_file in media_files:
                    media_record = EventMedia(
                        event_id=event.id,
                        media_type=MediaType(media_file.get("media_type", "image")),
                        file_url=media_file.get("file_url"),
                        thumbnail_url=media_file.get("thumbnail_url"),
                        file_size=media_file.get("file_size"),
                        file_name=media_file.get("file_name"),
                        file_metadata=media_file.get("metadata")
                    )
                    db.add(media_record)
                    media_records.append(media_record)
            
            await db.commit()
            
            logger.info(f"事件创建成功: {event.id}")
            
            return {
                "success": True,
                "event_id": str(event.id),
                "event": event.to_dict(),
                "location_address": final_address,
                "location_confidence": location_confidence,
                "priority": priority.value,
                "media_count": len(media_records),
                "message": "事件创建成功"
            }
            
        except Exception as e:
            await db.rollback()
            error_msg = f"创建事件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            if should_close_db:
                await db.close()    
 
    async def get_events_list(
        self,
        user_id: Optional[uuid.UUID] = None,
        event_types: Optional[List[str]] = None,
        statuses: Optional[List[EventStatus]] = None,
        priorities: Optional[List[EventPriority]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location_filter: Optional[Dict[str, Any]] = None,
        search_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        获取事件列表 - 支持分页、筛选和排序
        
        Args:
            user_id: 用户ID（可选，如果提供则只返回该用户的事件）
            event_types: 事件类型过滤
            statuses: 状态过滤
            priorities: 优先级过滤
            start_date: 开始日期
            end_date: 结束日期
            location_filter: 地理位置过滤
            search_query: 搜索关键词
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            page: 页码
            page_size: 每页大小
            db: 数据库会话
            
        Returns:
            Dict: 事件列表和分页信息
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            # 构建查询条件
            conditions = []
            
            # 用户过滤
            if user_id:
                conditions.append(Event.user_id == user_id)
            
            # 事件类型过滤
            if event_types:
                conditions.append(Event.event_type.in_(event_types))
            
            # 状态过滤
            if statuses:
                conditions.append(Event.status.in_(statuses))
            
            # 优先级过滤
            if priorities:
                conditions.append(Event.priority.in_(priorities))
            
            # 日期范围过滤
            if start_date:
                conditions.append(Event.created_at >= start_date)
            if end_date:
                conditions.append(Event.created_at <= end_date)
            
            # 搜索关键词
            if search_query:
                search_conditions = [
                    Event.title.ilike(f"%{search_query}%"),
                    Event.description.ilike(f"%{search_query}%"),
                    Event.location_address.ilike(f"%{search_query}%")
                ]
                conditions.append(or_(*search_conditions))
            
            # 地理位置过滤
            if location_filter:
                if "latitude" in location_filter and "longitude" in location_filter:
                    lat = location_filter["latitude"]
                    lng = location_filter["longitude"]
                    radius = location_filter.get("radius_meters", 1000)
                    
                    boundaries = await self.location_service.find_nearby_coordinates(lat, lng, radius)
                    conditions.extend([
                        Event.location_lat >= boundaries["min_lat"],
                        Event.location_lat <= boundaries["max_lat"],
                        Event.location_lng >= boundaries["min_lng"],
                        Event.location_lng <= boundaries["max_lng"]
                    ])
            
            # 构建排序
            sort_column = getattr(Event, sort_by, Event.created_at)
            if sort_order.lower() == "asc":
                order_by = asc(sort_column)
            else:
                order_by = desc(sort_column)
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 执行查询
            query = (
                select(Event)
                .options(
                    selectinload(Event.user),
                    selectinload(Event.media_files)
                )
                .where(and_(*conditions) if conditions else True)
                .order_by(order_by)
                .limit(page_size)
                .offset(offset)
            )
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            # 统计总数
            count_query = (
                select(func.count(Event.id))
                .where(and_(*conditions) if conditions else True)
            )
            count_result = await db.execute(count_query)
            total_count = count_result.scalar()
            
            # 转换为字典格式
            events_data = []
            for event in events:
                event_dict = event.to_dict()
                event_dict["user_name"] = event.user.name if event.user else "未知用户"
                event_dict["media_count"] = len(event.media_files)
                
                # 如果有地理位置过滤，计算距离
                if location_filter and "latitude" in location_filter:
                    distance = await self.location_service.calculate_distance(
                        location_filter["latitude"], location_filter["longitude"],
                        event.location_lat, event.location_lng
                    )
                    event_dict["distance_meters"] = round(distance, 2)
                
                events_data.append(event_dict)
            
            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            logger.info(f"获取事件列表成功: 页码{page}, 每页{page_size}, 总数{total_count}")
            
            return {
                "success": True,
                "events": events_data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                },
                "filters": {
                    "user_id": str(user_id) if user_id else None,
                    "event_types": event_types,
                    "statuses": [s.value for s in statuses] if statuses else None,
                    "priorities": [p.value for p in priorities] if priorities else None,
                    "search_query": search_query,
                    "location_filter": location_filter
                }
            }
            
        except Exception as e:
            error_msg = f"获取事件列表失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "events": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
        finally:
            if should_close_db:
                await db.close()
    
    async def get_event_detail(
        self,
        event_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        获取事件详情 - 返回完整事件信息和处理历史
        
        Args:
            event_id: 事件ID
            user_id: 用户ID（可选，用于权限检查）
            db: 数据库会话
            
        Returns:
            Dict: 事件详情
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            # 查询事件
            query = (
                select(Event)
                .options(
                    selectinload(Event.user),
                    selectinload(Event.timelines).selectinload(EventTimeline.operator),
                    selectinload(Event.media_files)
                )
                .where(Event.id == event_id)
            )
            
            result = await db.execute(query)
            event = result.scalar_one_or_none()
            
            if not event:
                return {
                    "success": False,
                    "error": "事件不存在"
                }
            
            # 权限检查（如果提供了user_id）
            if user_id and event.user_id != user_id:
                # 这里可以根据业务需求决定是否允许查看其他用户的事件
                # 目前允许查看，但可以在后续添加权限控制
                pass
            
            # 获取事件基本信息
            event_dict = event.to_dict()
            event_dict["user_name"] = event.user.name if event.user else "未知用户"
            event_dict["user_phone"] = event.user.phone if event.user else None
            
            # 获取时间线（按时间排序）
            timelines = sorted(event.timelines, key=lambda x: x.created_at)
            event_dict["timelines"] = []
            for timeline in timelines:
                timeline_dict = timeline.to_dict()
                timeline_dict["operator_name"] = timeline.operator.name if timeline.operator else "系统"
                event_dict["timelines"].append(timeline_dict)
            
            # 获取媒体文件
            event_dict["media_files"] = [media.to_dict() for media in event.media_files]
            
            # 尝试获取更详细的地理位置信息
            if event.location_lat and event.location_lng:
                geocode_result = await self.location_service.reverse_geocode(
                    event.location_lat, event.location_lng
                )
                
                if geocode_result.success and geocode_result.location_info:
                    location_info = geocode_result.location_info
                    event_dict["location_details"] = {
                        "province": location_info.province,
                        "city": location_info.city,
                        "district": location_info.district,
                        "street": location_info.street,
                        "street_number": location_info.street_number,
                        "formatted_address": location_info.formatted_address,
                        "confidence": location_info.confidence
                    }
                else:
                    event_dict["location_details"] = {
                        "error": "无法获取详细地址信息"
                    }
            
            # 添加状态统计信息
            event_dict["status_history"] = self._get_status_history_summary(event.timelines)
            
            logger.info(f"获取事件详情成功: {event_id}")
            
            return {
                "success": True,
                "event": event_dict
            }
            
        except Exception as e:
            error_msg = f"获取事件详情失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            if should_close_db:
                await db.close()    
 
    async def update_event_status(
        self,
        event_id: uuid.UUID,
        new_status: EventStatus,
        operator_id: uuid.UUID,
        description: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        更新事件状态 - 支持状态流转和时间线记录
        
        Args:
            event_id: 事件ID
            new_status: 新状态
            operator_id: 操作者ID
            description: 状态变更描述
            db: 数据库会话
            
        Returns:
            Dict: 更新结果
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            # 查询事件
            query = select(Event).where(Event.id == event_id)
            result = await db.execute(query)
            event = result.scalar_one_or_none()
            
            if not event:
                return {
                    "success": False,
                    "error": "事件不存在"
                }
            
            # 检查状态流转是否合法
            if not self._is_valid_status_transition(event.status, new_status):
                return {
                    "success": False,
                    "error": f"不能从状态 {event.status.value} 转换到 {new_status.value}"
                }
            
            old_status = event.status
            
            # 更新事件状态
            event.status = new_status
            event.updated_at = datetime.utcnow()
            
            # 根据状态变化自动调整优先级
            if new_status == EventStatus.PROCESSING and event.priority == EventPriority.LOW:
                event.priority = EventPriority.MEDIUM
            
            # 创建时间线记录
            timeline_description = description or f"状态从 {old_status.value} 变更为 {new_status.value}"
            timeline = EventTimeline(
                event_id=event.id,
                status=new_status,
                description=timeline_description,
                operator_id=operator_id
            )
            
            db.add(timeline)
            await db.commit()
            
            logger.info(f"事件状态更新成功: {event_id}, {old_status.value} -> {new_status.value}")
            
            return {
                "success": True,
                "event_id": str(event.id),
                "old_status": old_status.value,
                "new_status": new_status.value,
                "timeline_id": str(timeline.id),
                "message": "事件状态更新成功"
            }
            
        except Exception as e:
            await db.rollback()
            error_msg = f"更新事件状态失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            if should_close_db:
                await db.close()
    
    async def delete_event(
        self,
        event_id: uuid.UUID,
        user_id: uuid.UUID,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        删除事件 - 包含相关文件的清理
        
        Args:
            event_id: 事件ID
            user_id: 用户ID（权限检查）
            db: 数据库会话
            
        Returns:
            Dict: 删除结果
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            # 查询事件
            query = (
                select(Event)
                .options(selectinload(Event.media_files))
                .where(Event.id == event_id)
            )
            result = await db.execute(query)
            event = result.scalar_one_or_none()
            
            if not event:
                return {
                    "success": False,
                    "error": "事件不存在"
                }
            
            # 权限检查 - 只有事件创建者可以删除
            if event.user_id != user_id:
                return {
                    "success": False,
                    "error": "无权限删除此事件"
                }
            
            # 检查事件状态 - 已完成的事件不能删除
            if event.status == EventStatus.COMPLETED:
                return {
                    "success": False,
                    "error": "已完成的事件不能删除"
                }
            
            # 收集需要删除的文件
            file_keys_to_delete = []
            for media in event.media_files:
                if media.file_url:
                    # 从URL中提取文件键
                    file_key = self._extract_file_key_from_url(media.file_url)
                    if file_key:
                        file_keys_to_delete.append(file_key)
                
                if media.thumbnail_url:
                    thumbnail_key = self._extract_file_key_from_url(media.thumbnail_url)
                    if thumbnail_key:
                        file_keys_to_delete.append(thumbnail_key)
            
            # 删除数据库记录（级联删除会自动删除相关的timeline和media记录）
            await db.delete(event)
            await db.commit()
            
            # 删除OSS文件
            deleted_files = []
            failed_files = []
            
            if file_keys_to_delete:
                try:
                    delete_result = self.oss_service.delete_multiple_files(file_keys_to_delete)
                    deleted_files = delete_result.get("success", [])
                    failed_files = delete_result.get("failed", [])
                except Exception as e:
                    logger.warning(f"删除OSS文件失败: {str(e)}")
                    failed_files = file_keys_to_delete
            
            logger.info(f"事件删除成功: {event_id}, 删除文件数: {len(deleted_files)}")
            
            return {
                "success": True,
                "event_id": str(event.id),
                "deleted_files_count": len(deleted_files),
                "failed_files_count": len(failed_files),
                "message": "事件删除成功"
            }
            
        except Exception as e:
            await db.rollback()
            error_msg = f"删除事件失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            if should_close_db:
                await db.close()
    
    async def adjust_event_priority(
        self,
        event_id: uuid.UUID,
        operator_id: uuid.UUID,
        auto_adjust: bool = True,
        manual_priority: Optional[EventPriority] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        调整事件优先级 - 支持自动和手动调整
        
        Args:
            event_id: 事件ID
            operator_id: 操作者ID
            auto_adjust: 是否自动调整
            manual_priority: 手动指定的优先级
            db: 数据库会话
            
        Returns:
            Dict: 调整结果
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            # 查询事件
            query = select(Event).where(Event.id == event_id)
            result = await db.execute(query)
            event = result.scalar_one_or_none()
            
            if not event:
                return {
                    "success": False,
                    "error": "事件不存在"
                }
            
            old_priority = event.priority
            
            if auto_adjust:
                # 自动调整优先级
                new_priority = self._determine_priority(event.event_type, event.ai_analysis)
                
                # 考虑事件创建时间，越久的事件优先级越高
                days_since_created = (datetime.utcnow() - event.created_at).days
                if days_since_created > 7 and new_priority != EventPriority.URGENT:
                    if new_priority == EventPriority.LOW:
                        new_priority = EventPriority.MEDIUM
                    elif new_priority == EventPriority.MEDIUM:
                        new_priority = EventPriority.HIGH
                
            else:
                # 手动调整优先级
                if not manual_priority:
                    return {
                        "success": False,
                        "error": "手动调整时必须指定优先级"
                    }
                new_priority = manual_priority
            
            # 更新优先级
            event.priority = new_priority
            event.updated_at = datetime.utcnow()
            
            # 创建时间线记录
            adjustment_type = "自动" if auto_adjust else "手动"
            timeline = EventTimeline(
                event_id=event.id,
                status=event.status,
                description=f"{adjustment_type}调整优先级: {old_priority.value} -> {new_priority.value}",
                operator_id=operator_id
            )
            
            db.add(timeline)
            await db.commit()
            
            logger.info(f"事件优先级调整成功: {event_id}, {old_priority.value} -> {new_priority.value}")
            
            return {
                "success": True,
                "event_id": str(event.id),
                "old_priority": old_priority.value,
                "new_priority": new_priority.value,
                "adjustment_type": adjustment_type,
                "timeline_id": str(timeline.id),
                "message": "事件优先级调整成功"
            }
            
        except Exception as e:
            await db.rollback()
            error_msg = f"调整事件优先级失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            if should_close_db:
                await db.close()    
    
    def _determine_priority(self, event_type: str, ai_analysis: Optional[Dict[str, Any]] = None) -> EventPriority:
        """
        根据事件类型和AI分析结果确定优先级
        
        Args:
            event_type: 事件类型
            ai_analysis: AI分析结果
            
        Returns:
            EventPriority: 优先级
        """
        # 基础优先级
        base_priority = self.event_type_priority_map.get(event_type, EventPriority.MEDIUM)
        
        # 根据AI分析结果调整优先级
        if ai_analysis:
            confidence = ai_analysis.get("confidence", 0.0)
            detected_objects = ai_analysis.get("detected_objects", [])
            
            # 高置信度的危险物品检测
            dangerous_objects = ["火灾", "爆炸", "危险品", "事故", "伤亡"]
            for obj in detected_objects:
                if any(danger in obj.get("name", "").lower() for danger in dangerous_objects):
                    if confidence > 0.8:
                        return EventPriority.URGENT
                    elif confidence > 0.6:
                        return EventPriority.HIGH
        
        return base_priority
    
    def _is_valid_status_transition(self, current_status: EventStatus, new_status: EventStatus) -> bool:
        """
        检查状态流转是否合法
        
        Args:
            current_status: 当前状态
            new_status: 新状态
            
        Returns:
            bool: 是否合法
        """
        if current_status == new_status:
            return False  # 不能转换到相同状态
        
        allowed_transitions = self.status_transitions.get(current_status, [])
        return new_status in allowed_transitions
    
    def _get_status_history_summary(self, timelines: List[EventTimeline]) -> Dict[str, Any]:
        """
        获取状态历史摘要
        
        Args:
            timelines: 时间线列表
            
        Returns:
            Dict: 状态历史摘要
        """
        status_counts = {}
        status_durations = {}
        
        sorted_timelines = sorted(timelines, key=lambda x: x.created_at)
        
        for i, timeline in enumerate(sorted_timelines):
            status = timeline.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 计算状态持续时间
            if i < len(sorted_timelines) - 1:
                next_timeline = sorted_timelines[i + 1]
                duration = (next_timeline.created_at - timeline.created_at).total_seconds()
                status_durations[status] = status_durations.get(status, 0) + duration
            else:
                # 最后一个状态到现在的时间
                duration = (datetime.utcnow() - timeline.created_at).total_seconds()
                status_durations[status] = status_durations.get(status, 0) + duration
        
        return {
            "status_counts": status_counts,
            "status_durations": {k: round(v / 3600, 2) for k, v in status_durations.items()},  # 转换为小时
            "total_timeline_entries": len(timelines)
        }
    
    def _extract_file_key_from_url(self, file_url: str) -> Optional[str]:
        """
        从文件URL中提取文件键
        
        Args:
            file_url: 文件URL
            
        Returns:
            Optional[str]: 文件键
        """
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(file_url)
            # 移除开头的斜杠
            file_key = parsed_url.path.lstrip('/')
            return file_key if file_key else None
        except Exception as e:
            logger.warning(f"提取文件键失败: {str(e)}")
            return None
    
    # 保留原有的地理位置相关方法以保持兼容性
    async def create_event_with_location(
        self,
        user_id: uuid.UUID,
        event_type: str,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        address: Optional[str] = None,
        priority: EventPriority = EventPriority.MEDIUM,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        创建事件并处理地理位置信息（兼容性方法）
        """
        return await self.create_event(
            user_id=user_id,
            event_type=event_type,
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            address=address,
            db=db
        )
    
    async def find_events_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 1000,
        limit: int = 50,
        offset: int = 0,
        event_types: Optional[List[str]] = None,
        statuses: Optional[List[EventStatus]] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        基于地理位置查询附近的事件（兼容性方法）
        """
        page = (offset // limit) + 1
        page_size = limit
        
        location_filter = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_meters": radius_meters
        }
        
        return await self.get_events_list(
            event_types=event_types,
            statuses=statuses,
            location_filter=location_filter,
            page=page,
            page_size=page_size,
            db=db
        )
    
    async def find_events_by_address(
        self,
        address: str,
        radius_meters: float = 1000,
        limit: int = 50,
        offset: int = 0,
        event_types: Optional[List[str]] = None,
        statuses: Optional[List[EventStatus]] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        基于地址查询附近的事件（兼容性方法）
        """
        # 先将地址转换为坐标
        geocode_result = await self.location_service.geocode(address)
        
        if not geocode_result.success:
            return {
                "success": False,
                "error": f"地址解析失败: {geocode_result.error_message}",
                "events": [],
                "total_count": 0
            }
        
        location_info = geocode_result.location_info
        
        # 使用坐标查询
        result = await self.find_events_by_location(
            location_info.latitude,
            location_info.longitude,
            radius_meters,
            limit,
            offset,
            event_types,
            statuses,
            db
        )
        
        if result["success"]:
            # 添加地址解析信息
            if "search_params" not in result:
                result["search_params"] = {}
            result["search_params"]["search_address"] = address
            result["search_params"]["resolved_coordinates"] = {
                "latitude": location_info.latitude,
                "longitude": location_info.longitude
            }
        
        return result
    
    async def get_event_with_location_details(
        self,
        event_id: uuid.UUID,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        获取事件详情，包含详细的地理位置信息（兼容性方法）
        """
        return await self.get_event_detail(event_id=event_id, db=db)


# 创建全局事件服务实例
event_service = EventService()