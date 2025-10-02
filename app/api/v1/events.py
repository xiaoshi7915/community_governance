"""
事件管理API端点
包含事件的CRUD操作、状态管理和时间线查询功能
"""
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.core.response import ResponseFormatter
from app.models.user import User
from app.models.event import EventStatus, EventPriority
from app.services.event_service import event_service
from app.schemas.event import (
    CreateEventRequest, UpdateEventRequest, UpdateEventStatusRequest,
    EventListRequest, CreateEventResponse, EventDetailResponse,
    EventListResponse, UpdateEventResponse, DeleteEventResponse,
    EventStatusUpdateResponse, EventTimelineListResponse
)

router = APIRouter()

# 使用全局事件服务实例


@router.post("/events", 
             response_model=CreateEventResponse,
             summary="创建事件", 
             description="创建新事件并处理地理位置信息和媒体文件")
async def create_event(
    request: CreateEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建事件 - 处理事件创建请求"""
    try:
        # 转换媒体文件格式
        media_files = None
        if request.media_files:
            media_files = []
            for media in request.media_files:
                media_files.append({
                    "media_type": media.media_type.value,
                    "file_url": media.file_url,
                    "thumbnail_url": media.thumbnail_url,
                    "file_size": media.file_size,
                    "file_name": media.file_name,
                    "metadata": media.metadata
                })
        
        result = await event_service.create_event(
            user_id=current_user.id,
            event_type=request.event_type,
            title=request.title,
            description=request.description,
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address,
            media_files=media_files,
            ai_analysis=request.ai_analysis,
            confidence=request.confidence,
            db=db
        )
        
        if result["success"]:
            return ResponseFormatter.success(
                data=result,
                message="事件创建成功"
            )
        else:
            return ResponseFormatter.error(
                message=result["error"],
                error_code="EVENT_CREATE_FAILED"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建事件失败: {str(e)}")


@router.get("/events",
            response_model=EventListResponse,
            summary="获取事件列表",
            description="返回用户事件列表，支持分页、筛选和排序")
async def get_events_list(
    event_types: Optional[str] = Query(None, description="事件类型过滤，多个用逗号分隔"),
    statuses: Optional[str] = Query(None, description="状态过滤，多个用逗号分隔"),
    priorities: Optional[str] = Query(None, description="优先级过滤，多个用逗号分隔"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    search_query: Optional[str] = Query(None, description="搜索关键词"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="中心点纬度"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="中心点经度"),
    radius_meters: Optional[int] = Query(None, ge=1, le=50000, description="搜索半径（米）"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取事件列表 - 返回用户事件列表"""
    try:
        # 验证排序方向
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="排序方向必须是 'asc' 或 'desc'")
        
        # 处理过滤参数
        event_types_list = event_types.split(',') if event_types else None
        statuses_list = None
        if statuses:
            try:
                statuses_list = [EventStatus(s.strip()) for s in statuses.split(',')]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"无效的状态值: {str(e)}")
        
        priorities_list = None
        if priorities:
            try:
                priorities_list = [EventPriority(p.strip()) for p in priorities.split(',')]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"无效的优先级值: {str(e)}")
        
        # 构建地理位置过滤
        location_filter = None
        if latitude is not None and longitude is not None:
            location_filter = {
                "latitude": latitude,
                "longitude": longitude,
                "radius_meters": radius_meters or 1000
            }
        
        result = await event_service.get_events_list(
            user_id=current_user.id,
            event_types=event_types_list,
            statuses=statuses_list,
            priorities=priorities_list,
            start_date=start_date,
            end_date=end_date,
            location_filter=location_filter,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            db=db
        )
        
        if result["success"]:
            return ResponseFormatter.success(
                data=result,
                message="获取事件列表成功"
            )
        else:
            return ResponseFormatter.error(
                message=result["error"],
                error_code="EVENT_LIST_FAILED"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取事件列表失败: {str(e)}")


@router.get("/events/{event_id}",
            response_model=EventDetailResponse,
            summary="获取事件详情",
            description="返回事件详情，包含完整事件信息和处理历史")
async def get_event_detail(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取事件详情 - 返回事件详情"""
    try:
        result = await event_service.get_event_detail(
            event_id=event_id,
            user_id=None,  # 不进行严格的用户权限检查
            db=db
        )
        
        if result["success"]:
            return ResponseFormatter.success(
                data=result["event"],
                message="获取事件详情成功"
            )
        else:
            if "不存在" in result["error"]:
                raise HTTPException(status_code=404, detail=result["error"])
            return ResponseFormatter.error(
                message=result["error"],
                error_code="EVENT_DETAIL_FAILED"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取事件详情失败: {str(e)}")


@router.put("/events/{event_id}",
            response_model=UpdateEventResponse,
            summary="更新事件信息",
            description="支持事件信息更新")
async def update_event(
    event_id: uuid.UUID,
    request: UpdateEventRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新事件信息 - 支持事件信息更新"""
    try:
        # 首先检查事件是否存在以及用户权限
        event_detail = await event_service.get_event_detail(
            event_id=event_id,
            user_id=current_user.id,
            db=db
        )
        
        if not event_detail["success"]:
            if "不存在" in event_detail["error"]:
                raise HTTPException(status_code=404, detail="事件不存在")
            raise HTTPException(status_code=403, detail="无权限访问此事件")
        
        # 检查事件所有权
        if event_detail["event"]["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="只能更新自己创建的事件")
        
        # 检查事件状态 - 已完成的事件不能更新
        if event_detail["event"]["status"] == EventStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="已完成的事件不能更新")
        
        # 构建更新数据
        update_data = {}
        updated_fields = []
        
        if request.event_type is not None:
            update_data["event_type"] = request.event_type
            updated_fields.append("event_type")
        
        if request.title is not None:
            update_data["title"] = request.title
            updated_fields.append("title")
        
        if request.description is not None:
            update_data["description"] = request.description
            updated_fields.append("description")
        
        if request.latitude is not None:
            update_data["location_lat"] = request.latitude
            updated_fields.append("location_lat")
        
        if request.longitude is not None:
            update_data["location_lng"] = request.longitude
            updated_fields.append("location_lng")
        
        if request.address is not None:
            update_data["location_address"] = request.address
            updated_fields.append("location_address")
        
        if request.priority is not None:
            update_data["priority"] = request.priority
            updated_fields.append("priority")
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")
        
        # 执行更新
        from sqlalchemy.future import select
        from app.models.event import Event
        
        query = select(Event).where(Event.id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            raise HTTPException(status_code=404, detail="事件不存在")
        
        # 更新字段
        for field, value in update_data.items():
            setattr(event, field, value)
        
        event.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # 获取更新后的事件信息
        updated_event_detail = await event_service.get_event_detail(
            event_id=event_id,
            user_id=current_user.id,
            db=db
        )
        
        response_data = {
            "event_id": str(event_id),
            "updated_fields": updated_fields,
            "event": updated_event_detail["event"],
            "message": "事件更新成功"
        }
        
        return ResponseFormatter.success(
            data=response_data,
            message="事件更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新事件失败: {str(e)}")


@router.delete("/events/{event_id}",
               response_model=DeleteEventResponse,
               summary="删除事件",
               description="处理事件删除，包含相关文件的清理")
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除事件 - 处理事件删除"""
    try:
        result = await event_service.delete_event(
            event_id=event_id,
            user_id=current_user.id,
            db=db
        )
        
        if result["success"]:
            return ResponseFormatter.success(
                data=result,
                message="事件删除成功"
            )
        else:
            if "不存在" in result["error"]:
                raise HTTPException(status_code=404, detail=result["error"])
            elif "无权限" in result["error"]:
                raise HTTPException(status_code=403, detail=result["error"])
            elif "不能删除" in result["error"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return ResponseFormatter.error(
                message=result["error"],
                error_code="EVENT_DELETE_FAILED"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除事件失败: {str(e)}")


@router.get("/events/{event_id}/timeline",
            response_model=EventTimelineListResponse,
            summary="获取事件处理历史",
            description="返回事件处理历史时间线")
async def get_event_timeline(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取事件处理历史 - 返回事件处理历史"""
    try:
        # 首先检查事件是否存在（不进行严格的用户权限检查）
        event_detail = await event_service.get_event_detail(
            event_id=event_id,
            user_id=None,  # 不进行严格的用户权限检查
            db=db
        )
        
        if not event_detail["success"]:
            if "不存在" in event_detail["error"]:
                raise HTTPException(status_code=404, detail="事件不存在")
            raise HTTPException(status_code=500, detail=event_detail["error"])
        
        # 提取时间线数据
        timelines = event_detail["event"]["timelines"]
        
        response_data = {
            "event_id": str(event_id),
            "timelines": timelines,
            "total_count": len(timelines)
        }
        
        return ResponseFormatter.success(
            data=response_data,
            message="获取事件时间线成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取事件时间线失败: {str(e)}")


@router.put("/events/{event_id}/status",
            response_model=EventStatusUpdateResponse,
            summary="更新事件状态",
            description="更新事件状态并记录时间线")
async def update_event_status(
    event_id: uuid.UUID,
    request: UpdateEventStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新事件状态 - 支持状态流转和时间线记录"""
    try:
        result = await event_service.update_event_status(
            event_id=event_id,
            new_status=request.status,
            operator_id=current_user.id,
            description=request.description,
            db=db
        )
        
        if result["success"]:
            return ResponseFormatter.success(
                data=result,
                message="事件状态更新成功"
            )
        else:
            if "不存在" in result["error"]:
                raise HTTPException(status_code=404, detail=result["error"])
            elif "不能从状态" in result["error"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return ResponseFormatter.error(
                message=result["error"],
                error_code="EVENT_STATUS_UPDATE_FAILED"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新事件状态失败: {str(e)}")


@router.get("/events/user/stats",
            summary="获取用户统计信息",
            description="获取当前用户的事件统计数据")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户统计信息
    
    基于用户角色返回不同范围的统计数据：
    - 市民：个人30天内上报事件
    - 网格员：负责区域30天内事件
    - 管理员/决策者：平台30天内所有事件
    """
    try:
        from sqlalchemy import select, func, and_
        from app.models.event import Event
        from datetime import datetime, timedelta
        
        # 计算30天前的时间
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 根据用户角色确定统计范围
        if current_user.role == "citizen":
            # 市民：只统计自己30天内的事件
            base_query = select(Event).where(
                and_(
                    Event.user_id == current_user.id,
                    Event.created_at >= thirty_days_ago
                )
            )
        elif current_user.role == "grid_officer":
            # 网格员：统计负责区域30天内的事件
            # 这里简化处理，可以根据实际需求添加地理范围过滤
            base_query = select(Event).where(Event.created_at >= thirty_days_ago)
        else:
            # 管理员和决策者：统计平台30天内所有事件
            base_query = select(Event).where(Event.created_at >= thirty_days_ago)
        
        # 获取总事件数
        total_events_result = await db.execute(
            select(func.count(Event.id)).select_from(base_query.subquery())
        )
        total_events = total_events_result.scalar() or 0
        
        # 构建状态统计查询
        if current_user.role == "citizen":
            status_query_filter = and_(
                Event.user_id == current_user.id,
                Event.created_at >= thirty_days_ago
            )
        elif current_user.role == "grid_officer":
            status_query_filter = Event.created_at >= thirty_days_ago
        else:
            status_query_filter = Event.created_at >= thirty_days_ago
        
        # 获取各状态事件数
        status_stats_result = await db.execute(
            select(Event.status, func.count(Event.id))
            .where(status_query_filter)
            .group_by(Event.status)
        )
        status_stats = {row[0]: row[1] for row in status_stats_result.fetchall()}
        
        # 获取各类型事件数
        type_stats_result = await db.execute(
            select(Event.event_type, func.count(Event.id))
            .where(status_query_filter)
            .group_by(Event.event_type)
        )
        type_stats = {row[0]: row[1] for row in type_stats_result.fetchall()}
        
        # 获取最近事件
        recent_events_result = await db.execute(
            select(Event)
            .where(status_query_filter)
            .order_by(Event.created_at.desc())
            .limit(5)
        )
        recent_events = recent_events_result.scalars().all()
        
        stats_data = {
            "total_events": total_events,
            "status_stats": {
                "pending": status_stats.get("pending", 0),
                "processing": status_stats.get("processing", 0),
                "resolved": status_stats.get("resolved", 0),
                "closed": status_stats.get("closed", 0)
            },
            "type_stats": type_stats,
            "recent_events": [
                {
                    "id": str(event.id),
                    "title": event.title,
                    "status": event.status,
                    "event_type": event.event_type,
                    "created_at": event.created_at.isoformat() if event.created_at else None
                }
                for event in recent_events
            ]
        }
        
        return ResponseFormatter.success(
            data=stats_data,
            message="用户统计信息获取成功"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户统计失败: {str(e)}"
        )


@router.get("/events/history/stats",
            summary="获取历史统计数据",
            description="获取基于角色的历史统计数据")
async def get_history_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取历史统计数据
    
    基于用户角色返回不同范围的历史统计：
    - 市民：个人历史统计
    - 网格员：负责区域历史统计
    - 管理员/决策者：平台历史统计
    """
    try:
        from sqlalchemy import select, func, and_, extract
        from app.models.event import Event
        from datetime import datetime, timedelta
        
        # 根据用户角色确定统计范围
        if current_user.role == "citizen":
            base_filter = Event.user_id == current_user.id
        # elif current_user.role == "grid_officer":
        #     # 网格员：统计所有事件（简化处理）
        #     base_filter = True
        # else:
        #     base_filter = True  # 错误：不是有效的WHERE条件

        else:
            # 网格员和管理员：不添加用户过滤
            base_filter = None

        # 构建基础查询
        def build_query(additional_filter=None):
            query = select(func.count(Event.id))
            if user_filter is not None:
                query = query.where(user_filter)
            if additional_filter is not None:
                query = query.where(additional_filter)
            return query
        
        # 获取总事件数
        total_query = build_query()
        total_result = await db.execute(total_query)
        total_events = total_result.scalar() or 0
        
        # 获取已解决事件数
        resolved_query = build_query(Event.status == "resolved")
        resolved_result = await db.execute(resolved_query)
        resolved_events = resolved_result.scalar() or 0
        
        # # 获取总体统计
        # total_events_result = await db.execute(
        #     select(func.count(Event.id)).where(base_filter)
        # )
        # total_events = total_events_result.scalar() or 0
        
        # # 获取已解决事件数
        # resolved_events_result = await db.execute(
        #     select(func.count(Event.id)).where(
        #         and_(base_filter, Event.status == "resolved")
        #     )
        # )
        # resolved_events = resolved_events_result.scalar() or 0
        
        # 获取处理中事件数
        processing_events_result = await db.execute(
            select(func.count(Event.id)).where(
                and_(base_filter, Event.status == "processing")
            )
        )
        processing_events = processing_events_result.scalar() or 0
        
        # 获取超期事件数（创建超过7天且未解决）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        overdue_events_result = await db.execute(
            select(func.count(Event.id)).where(
                and_(
                    base_filter,
                    Event.created_at < seven_days_ago,
                    Event.status.in_(["pending", "processing"])
                )
            )
        )
        overdue_events = overdue_events_result.scalar() or 0
        
        # 计算解决率
        resolution_rate = (resolved_events / total_events * 100) if total_events > 0 else 0
        
        # 获取事件类型分布
        type_distribution_result = await db.execute(
            select(Event.event_type, func.count(Event.id))
            .where(base_filter)
            .group_by(Event.event_type)
        )
        type_distribution = {row[0]: row[1] for row in type_distribution_result.fetchall()}
        
        # 获取月度趋势（最近6个月）
        monthly_trends = []
        for i in range(6):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_events_result = await db.execute(
                select(func.count(Event.id)).where(
                    and_(
                        base_filter,
                        Event.created_at >= month_start,
                        Event.created_at < month_end
                    )
                )
            )
            month_events = month_events_result.scalar() or 0
            
            monthly_trends.append({
                "month": month_start.strftime("%Y-%m"),
                "events": month_events
            })
        
        monthly_trends.reverse()  # 按时间正序
        
        history_data = {
            "summary": {
                "total_events": total_events,
                "resolved_events": resolved_events,
                "processing_events": processing_events,
                "overdue_events": overdue_events,
                "resolution_rate": round(resolution_rate, 1)
            },
            "type_distribution": type_distribution,
            "monthly_trends": monthly_trends,
            "user_role": current_user.role
        }
        
        return ResponseFormatter.success(
            data=history_data,
            message="历史统计数据获取成功"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户统计信息失败: {str(e)}"
        )