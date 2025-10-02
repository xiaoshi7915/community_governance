"""
AI识别服务API端点
提供图像识别、视频分析、事件分类等功能
"""
from typing import Dict, List, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer

from app.core.response import APIResponse, response_formatter
from app.core.exceptions import AIServiceError, ValidationError
from app.core.auth_middleware import get_current_user
from app.core.logging import get_logger
from app.schemas.ai import (
    ImageAnalysisRequest,
    VideoAnalysisRequest,
    VideoFrameExtractionRequest,
    EventClassificationRequest,
    AIAnalysisResponse,
    EventClassificationResponse,
    VideoFrameExtractionResponse,
    EventTypesResponse,
    EventTypeInfo,
    AIServiceStatusResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    AIServiceInfoResponse,
    AsyncAnalysisRequest,
    AsyncAnalysisResponse,
    TaskStatusResponse,
    CacheStatsResponse
)
from app.schemas.auth import UserResponse
from app.services.ai_service import ai_service, AIService

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/analyze-image", response_model=APIResponse[AIAnalysisResponse])
async def analyze_image(
    request: ImageAnalysisRequest,
    use_cache: bool = True,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    分析图像内容
    
    - **image_url**: 图像URL地址
    
    返回AI分析结果，包括事件类型、描述和置信度
    """
    try:
        logger.info(f"用户 {current_user.id} 请求图像分析: {request.image_url}")
        
        # 调用AI服务进行图像分析
        result = await ai_service.analyze_image(request.image_url, use_cache=use_cache)
        
        # 转换为响应格式
        response_data = AIAnalysisResponse(
            event_type=result.event_type,
            description=result.description,
            confidence=result.confidence,
            details=result.details,
            timestamp=result.timestamp
        )
        
        logger.info(f"图像分析完成，事件类型: {result.event_type}, 置信度: {result.confidence}")
        
        return response_formatter.success(
            data=response_data,
            message="图像分析完成"
        )
        
    except ValidationError as e:
        logger.warning(f"图像分析参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except AIServiceError as e:
        logger.error(f"图像分析服务错误: {str(e)}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"图像分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail="图像分析失败")


@router.post("/analyze-video", response_model=APIResponse[AIAnalysisResponse])
async def analyze_video(
    request: VideoAnalysisRequest,
    use_cache: bool = True,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    分析视频内容
    
    - **video_url**: 视频URL地址
    - **max_frames**: 最大提取帧数（可选，默认5帧）
    
    返回基于关键帧分析的结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求视频分析: {request.video_url}")
        
        # 调用AI服务进行视频分析
        result = await ai_service.analyze_video(request.video_url, use_cache=use_cache)
        
        # 转换为响应格式
        response_data = AIAnalysisResponse(
            event_type=result.event_type,
            description=result.description,
            confidence=result.confidence,
            details=result.details,
            timestamp=result.timestamp
        )
        
        logger.info(f"视频分析完成，事件类型: {result.event_type}, 置信度: {result.confidence}")
        
        return response_formatter.success(
            data=response_data,
            message="视频分析完成"
        )
        
    except ValidationError as e:
        logger.warning(f"视频分析参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except AIServiceError as e:
        logger.error(f"视频分析服务错误: {str(e)}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"视频分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail="视频分析失败")


@router.post("/extract-frames", response_model=APIResponse[VideoFrameExtractionResponse])
async def extract_video_frames(
    request: VideoFrameExtractionRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    提取视频关键帧
    
    - **video_url**: 视频URL地址
    - **max_frames**: 最大提取帧数（可选，默认5帧）
    
    返回提取的关键帧URL列表
    """
    try:
        logger.info(f"用户 {current_user.id} 请求视频关键帧提取: {request.video_url}")
        
        # 调用AI服务提取关键帧
        frame_urls = await ai_service.extract_video_frames(
            request.video_url, 
            request.max_frames
        )
        
        # 构建响应数据
        response_data = VideoFrameExtractionResponse(
            frame_urls=frame_urls,
            frame_count=len(frame_urls),
            video_info={
                "video_url": request.video_url,
                "max_frames_requested": request.max_frames,
                "extraction_time": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"视频关键帧提取完成，提取帧数: {len(frame_urls)}")
        
        return response_formatter.success(
            data=response_data,
            message="视频关键帧提取完成"
        )
        
    except ValidationError as e:
        logger.warning(f"视频关键帧提取参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except AIServiceError as e:
        logger.error(f"视频关键帧提取服务错误: {str(e)}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"视频关键帧提取异常: {str(e)}")
        raise HTTPException(status_code=500, detail="视频关键帧提取失败")


@router.post("/classify-event", response_model=APIResponse[EventClassificationResponse])
async def classify_event_type(
    request: EventClassificationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    基于AI分析结果分类事件类型
    
    - **analysis_result**: AI分析结果字典
    
    返回事件分类结果，包括主要类型、置信度和建议优先级
    """
    try:
        logger.info(f"用户 {current_user.id} 请求事件分类")
        
        # 调用AI服务进行事件分类
        classification = await ai_service.classify_event_type(request.analysis_result)
        
        # 转换为响应格式
        response_data = EventClassificationResponse(
            primary_type=classification.primary_type,
            secondary_type=classification.secondary_type,
            confidence=classification.confidence,
            suggested_priority=classification.suggested_priority,
            keywords=classification.keywords
        )
        
        logger.info(f"事件分类完成，类型: {classification.primary_type}, 置信度: {classification.confidence}")
        
        return response_formatter.success(
            data=response_data,
            message="事件分类完成"
        )
        
    except ValidationError as e:
        logger.warning(f"事件分类参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"事件分类异常: {str(e)}")
        raise HTTPException(status_code=500, detail="事件分类失败")


@router.get("/event-types", response_model=APIResponse[EventTypesResponse])
async def get_event_types(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取支持的事件类型列表
    
    返回系统支持的所有事件类型及其相关信息
    """
    try:
        logger.info(f"用户 {current_user.id} 请求事件类型列表")
        
        # 获取事件类型映射
        event_types = []
        for type_name, config in AIService.EVENT_TYPE_MAPPING.items():
            event_type_info = EventTypeInfo(
                type_name=type_name,
                keywords=config["keywords"],
                priority=config["priority"],
                category=config["category"],
                description=f"{type_name}相关的城市治理问题"
            )
            event_types.append(event_type_info)
        
        response_data = EventTypesResponse(
            event_types=event_types,
            total_count=len(event_types)
        )
        
        logger.info(f"返回事件类型列表，总数: {len(event_types)}")
        
        return response_formatter.success(
            data=response_data,
            message="获取事件类型列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取事件类型列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取事件类型列表失败")


@router.get("/service-status", response_model=APIResponse[AIServiceStatusResponse])
async def get_ai_service_status(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取AI服务状态
    
    返回AI服务的可用性状态和相关信息
    """
    try:
        logger.info(f"用户 {current_user.id} 请求AI服务状态")
        
        # 检查AI服务状态
        service_available = ai_service._is_ai_service_available()
        
        response_data = AIServiceStatusResponse(
            service_available=service_available,
            fallback_enabled=ai_service.fallback_enabled,
            last_check_time=datetime.utcnow(),
            error_message=None if service_available else "AI服务配置不完整"
        )
        
        logger.info(f"AI服务状态检查完成，可用: {service_available}")
        
        return response_formatter.success(
            data=response_data,
            message="AI服务状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取AI服务状态异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取AI服务状态失败")


@router.post("/batch-analyze", response_model=APIResponse[BatchAnalysisResponse])
async def batch_analyze_media(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    批量分析媒体文件
    
    - **media_items**: 媒体项目列表，每个项目包含url和type字段
    
    返回批量分析结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求批量媒体分析，项目数: {len(request.media_items)}")
        
        results = []
        failed_items = []
        
        # 逐个分析媒体项目
        for item in request.media_items:
            try:
                media_url = item["url"]
                media_type = item["type"]
                
                if media_type == "image":
                    result = await ai_service.analyze_image(media_url)
                elif media_type == "video":
                    result = await ai_service.analyze_video(media_url)
                else:
                    raise ValidationError(f"不支持的媒体类型: {media_type}")
                
                # 转换为响应格式
                analysis_response = AIAnalysisResponse(
                    event_type=result.event_type,
                    description=result.description,
                    confidence=result.confidence,
                    details=result.details,
                    timestamp=result.timestamp
                )
                results.append(analysis_response)
                
            except Exception as e:
                logger.warning(f"批量分析项目失败: {item}, 错误: {str(e)}")
                failed_items.append({
                    "url": item.get("url", ""),
                    "type": item.get("type", ""),
                    "error": str(e)
                })
        
        response_data = BatchAnalysisResponse(
            results=results,
            success_count=len(results),
            failed_count=len(failed_items),
            failed_items=failed_items
        )
        
        logger.info(f"批量媒体分析完成，成功: {len(results)}, 失败: {len(failed_items)}")
        
        return response_formatter.success(
            data=response_data,
            message="批量媒体分析完成"
        )
        
    except ValidationError as e:
        logger.warning(f"批量分析参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量媒体分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail="批量媒体分析失败")


@router.post("/analyze-async", response_model=APIResponse[AsyncAnalysisResponse])
async def analyze_media_async(
    request: AsyncAnalysisRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    异步分析媒体内容
    
    - **media_url**: 媒体文件URL
    - **media_type**: 媒体类型（image或video）
    
    返回任务ID，可通过任务状态接口查询分析结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求异步{request.media_type}分析: {request.media_url}")
        
        # 创建异步分析任务
        if request.media_type == "image":
            task_id = await ai_service.analyze_image_async(request.media_url)
        elif request.media_type == "video":
            task_id = await ai_service.analyze_video_async(request.media_url)
        else:
            raise ValidationError(f"不支持的媒体类型: {request.media_type}")
        
        response_data = AsyncAnalysisResponse(
            task_id=task_id,
            status="pending",
            message="异步分析任务已创建，请使用任务ID查询分析结果"
        )
        
        logger.info(f"异步分析任务创建成功: {task_id}")
        
        return response_formatter.success(
            data=response_data,
            message="异步分析任务创建成功"
        )
        
    except ValidationError as e:
        logger.warning(f"异步分析参数验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"异步分析任务创建异常: {str(e)}")
        raise HTTPException(status_code=500, detail="异步分析任务创建失败")


@router.get("/task/{task_id}", response_model=APIResponse[TaskStatusResponse])
async def get_task_status(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取异步任务状态
    
    - **task_id**: 任务ID
    
    返回任务的详细状态信息和分析结果（如果已完成）
    """
    try:
        logger.info(f"用户 {current_user.id} 查询任务状态: {task_id}")
        
        # 获取任务状态
        task_info = await ai_service.get_task_status(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在或已过期")
        
        # 构建响应数据
        response_data = TaskStatusResponse(
            task_id=task_info["task_id"],
            status=task_info["status"],
            media_url=task_info["media_url"],
            media_type=task_info["media_type"],
            created_at=task_info["created_at"],
            started_at=task_info.get("started_at"),
            completed_at=task_info.get("completed_at"),
            failed_at=task_info.get("failed_at"),
            error=task_info.get("error")
        )
        
        # 如果任务已完成，添加分析结果
        if task_info["status"] == "completed" and task_info.get("result"):
            result_data = task_info["result"]
            response_data.result = AIAnalysisResponse(
                event_type=result_data["event_type"],
                description=result_data["description"],
                confidence=result_data["confidence"],
                details=result_data["details"],
                timestamp=datetime.fromisoformat(result_data["timestamp"])
            )
        
        logger.info(f"任务状态查询成功: {task_id}, 状态: {task_info['status']}")
        
        return response_formatter.success(
            data=response_data,
            message="任务状态获取成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.get("/cache/stats", response_model=APIResponse[CacheStatsResponse])
async def get_cache_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取AI分析缓存统计信息
    
    返回缓存的使用情况和统计数据
    """
    try:
        logger.info(f"用户 {current_user.id} 请求缓存统计信息")
        
        # 获取Redis缓存统计
        from app.core.redis import redis_service
        redis_client = await redis_service.get_client()
        
        # 统计AI分析相关的缓存键
        pattern = f"{ai_service.cache_prefix}:*"
        keys = await redis_client.keys(pattern)
        total_keys = len(keys)
        
        # 获取Redis内存信息
        info = await redis_client.info("memory")
        memory_usage = info.get("used_memory_human", "未知")
        
        response_data = CacheStatsResponse(
            cache_enabled=ai_service.cache_enabled,
            cache_ttl=ai_service.cache_ttl,
            total_keys=total_keys,
            memory_usage=memory_usage
        )
        
        logger.info(f"缓存统计信息获取成功，缓存键数: {total_keys}")
        
        return response_formatter.success(
            data=response_data,
            message="缓存统计信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取缓存统计信息异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取缓存统计信息失败")


@router.delete("/cache/clear", response_model=APIResponse[Dict[str, Any]])
async def clear_ai_cache(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    清空AI分析缓存
    
    清除所有AI分析结果的缓存数据
    """
    try:
        logger.info(f"用户 {current_user.id} 请求清空AI缓存")
        
        # 清空AI分析缓存
        from app.core.redis import redis_service
        redis_client = await redis_service.get_client()
        
        pattern = f"{ai_service.cache_prefix}:*"
        keys = await redis_client.keys(pattern)
        
        if keys:
            deleted_count = await redis_client.delete(*keys)
        else:
            deleted_count = 0
        
        response_data = {
            "cleared_keys": deleted_count,
            "cache_pattern": pattern,
            "cleared_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"AI缓存清空完成，清除键数: {deleted_count}")
        
        return response_formatter.success(
            data=response_data,
            message=f"AI缓存清空成功，清除了{deleted_count}个缓存项"
        )
        
    except Exception as e:
        logger.error(f"清空AI缓存异常: {str(e)}")
        raise HTTPException(status_code=500, detail="清空AI缓存失败")


@router.get("/service-info", response_model=APIResponse[AIServiceInfoResponse])
async def get_ai_service_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    获取AI服务详细信息
    
    返回AI服务的详细配置和能力信息
    """
    try:
        logger.info(f"用户 {current_user.id} 请求AI服务信息")
        
        # 构建服务信息
        from app.schemas.ai import AIModelInfo
        
        models = [
            AIModelInfo(
                model_name="qwen-vl-plus",
                model_version="1.0",
                capabilities=["图像识别", "多模态理解", "文本生成"],
                supported_formats=["JPEG", "PNG", "GIF", "WebP", "MP4", "AVI", "MOV"],
                max_file_size=50 * 1024 * 1024  # 50MB
            )
        ]
        
        # 获取服务状态
        service_available = ai_service._is_ai_service_available()
        status = AIServiceStatusResponse(
            service_available=service_available,
            fallback_enabled=ai_service.fallback_enabled,
            last_check_time=datetime.utcnow(),
            error_message=None if service_available else "AI服务配置不完整"
        )
        
        response_data = AIServiceInfoResponse(
            service_name="阿里云百炼AI",
            service_version="1.0.0",
            provider="阿里云",
            models=models,
            rate_limits={
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "concurrent_requests": 10
            },
            status=status
        )
        
        logger.info("AI服务信息获取成功")
        
        return response_formatter.success(
            data=response_data,
            message="AI服务信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取AI服务信息异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取AI服务信息失败")


# 在应用关闭时清理资源
@router.on_event("shutdown")
async def shutdown_ai_service():
    """应用关闭时清理AI服务资源"""
    try:
        await ai_service.close()
        logger.info("AI服务资源清理完成")
    except Exception as e:
        logger.error(f"AI服务资源清理失败: {str(e)}")