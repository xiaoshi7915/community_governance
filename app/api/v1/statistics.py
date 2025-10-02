"""
统计分析API端点
提供用户统计、事件统计、效率分析、热点区域分析等接口
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.models.user import User
from app.services.statistics_service import statistics_service
from app.schemas.response import ResponseModel
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/user", response_model=ResponseModel)
async def get_user_statistics(
    user_id: Optional[UUID] = Query(None, description="用户ID，为空时统计所有用户"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户统计数据
    
    - **user_id**: 用户ID，如果为空则统计所有用户（需要管理员权限）
    - **start_date**: 开始日期，格式：YYYY-MM-DD
    - **end_date**: 结束日期，格式：YYYY-MM-DD
    """
    try:
        # 如果指定了user_id且不是当前用户，需要检查权限
        if user_id and user_id != current_user.id:
            # 这里可以添加管理员权限检查
            # 暂时只允许查询自己的统计数据
            raise HTTPException(status_code=403, detail="无权限查看其他用户的统计数据")
        
        # 如果没有指定user_id，使用当前用户ID
        if not user_id:
            user_id = current_user.id
        
        statistics = await statistics_service.get_user_statistics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return ResponseModel(
            success=True,
            data=statistics,
            message="用户统计数据获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取用户统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户统计数据失败: {str(e)}")


@router.get("/events", response_model=ResponseModel)
async def get_event_statistics(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取事件统计分析数据
    
    - **start_date**: 开始日期，格式：YYYY-MM-DD
    - **end_date**: 结束日期，格式：YYYY-MM-DD
    - **group_by**: 分组方式，可选值：day（按天）、week（按周）、month（按月）
    """
    try:
        if group_by not in ["day", "week", "month"]:
            raise HTTPException(status_code=400, detail="group_by参数必须是day、week或month")
        
        statistics = await statistics_service.get_event_statistics(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        return ResponseModel(
            success=True,
            data=statistics,
            message="事件统计数据获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取事件统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取事件统计数据失败: {str(e)}")


@router.get("/efficiency", response_model=ResponseModel)
async def get_processing_efficiency_analysis(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取处理效率分析数据
    
    - **start_date**: 开始日期，格式：YYYY-MM-DD
    - **end_date**: 结束日期，格式：YYYY-MM-DD
    """
    try:
        analysis = await statistics_service.get_processing_efficiency_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        return ResponseModel(
            success=True,
            data=analysis,
            message="处理效率分析数据获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取处理效率分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取处理效率分析数据失败: {str(e)}")


@router.get("/hotspots", response_model=ResponseModel)
async def get_hotspot_area_analysis(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    radius_km: float = Query(1.0, description="热点区域半径（公里）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取热点区域分析数据
    
    - **start_date**: 开始日期，格式：YYYY-MM-DD
    - **end_date**: 结束日期，格式：YYYY-MM-DD
    - **radius_km**: 热点区域半径，单位：公里
    """
    try:
        if radius_km <= 0 or radius_km > 50:
            raise HTTPException(status_code=400, detail="半径必须在0-50公里之间")
        
        analysis = await statistics_service.get_hotspot_area_analysis(
            start_date=start_date,
            end_date=end_date,
            radius_km=radius_km
        )
        
        return ResponseModel(
            success=True,
            data=analysis,
            message="热点区域分析数据获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取热点区域分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热点区域分析数据失败: {str(e)}")


@router.get("/export/excel")
async def export_statistics_excel(
    export_type: str = Query(..., description="导出类型：user_stats/event_stats/efficiency/hotspots"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user_id: Optional[UUID] = Query(None, description="用户ID（仅用于用户统计）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出统计数据为Excel格式
    
    - **export_type**: 导出类型，可选值：user_stats、event_stats、efficiency、hotspots
    - **start_date**: 开始日期，格式：YYYY-MM-DD
    - **end_date**: 结束日期，格式：YYYY-MM-DD
    - **user_id**: 用户ID（仅用于用户统计导出）
    """
    try:
        if export_type not in ["user_stats", "event_stats", "efficiency", "hotspots"]:
            raise HTTPException(status_code=400, detail="不支持的导出类型")
        
        # 权限检查
        if export_type == "user_stats" and user_id and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限导出其他用户的统计数据")
        
        if export_type == "user_stats" and not user_id:
            user_id = current_user.id
        
        excel_data = await statistics_service.export_statistics_to_excel(
            export_type=export_type,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistics_{export_type}_{timestamp}.xlsx"
        
        # 返回Excel文件
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"导出Excel失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出Excel失败: {str(e)}")


@router.get("/export/csv")
async def export_statistics_csv(
    export_type: str = Query(..., description="导出类型：user_stats/event_stats/efficiency/hotspots"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user_id: Optional[UUID] = Query(None, description="用户ID（仅用于用户统计）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出统计数据为CSV格式
    
    - **export_type**: 导出类型，可选值：user_stats、event_stats、efficiency、hotspots
    - **start_date**: 开始日期，格式：YYYY-MM-DD
    - **end_date**: 结束日期，格式：YYYY-MM-DD
    - **user_id**: 用户ID（仅用于用户统计导出）
    """
    try:
        if export_type not in ["user_stats", "event_stats", "efficiency", "hotspots"]:
            raise HTTPException(status_code=400, detail="不支持的导出类型")
        
        # 权限检查
        if export_type == "user_stats" and user_id and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限导出其他用户的统计数据")
        
        if export_type == "user_stats" and not user_id:
            user_id = current_user.id
        
        csv_data = await statistics_service.export_statistics_to_csv(
            export_type=export_type,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistics_{export_type}_{timestamp}.csv"
        
        # 返回CSV文件
        return Response(
            content=csv_data.encode('utf-8-sig'),  # 使用UTF-8 BOM以支持中文
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"导出CSV失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出CSV失败: {str(e)}")


@router.post("/cache/refresh", response_model=ResponseModel)
async def refresh_statistics_cache(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    刷新统计数据缓存
    
    清除所有统计缓存并预热常用数据
    """
    try:
        await statistics_service.refresh_all_caches()
        
        return ResponseModel(
            success=True,
            data={"message": "统计缓存刷新成功"},
            message="统计缓存刷新成功"
        )
        
    except Exception as e:
        logger.error(f"刷新统计缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刷新统计缓存失败: {str(e)}")