"""
阿里云百炼AI识别服务
提供图像识别、视频分析、事件分类等AI功能
"""
import json
import asyncio
import aiohttp
import cv2
import numpy as np
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse
import base64
import io
from PIL import Image
import tempfile
import os

from app.core.config import settings
from app.core.exceptions import (
    AIServiceError,
    ValidationError,
    ExternalServiceError
)
from app.core.logging import get_logger
from app.core.redis import redis_service

logger = get_logger(__name__)


class AIAnalysisResult:
    """AI分析结果数据类"""
    
    def __init__(
        self,
        event_type: str,
        description: str,
        confidence: float,
        details: Dict[str, Any],
        raw_response: Dict[str, Any]
    ):
        self.event_type = event_type
        self.description = description
        self.confidence = confidence
        self.details = details
        self.raw_response = raw_response
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_type": self.event_type,
            "description": self.description,
            "confidence": self.confidence,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "raw_response": self.raw_response
        }


class EventClassification:
    """事件分类结果"""
    
    def __init__(
        self,
        primary_type: str,
        secondary_type: Optional[str],
        confidence: float,
        suggested_priority: str,
        keywords: List[str]
    ):
        self.primary_type = primary_type
        self.secondary_type = secondary_type
        self.confidence = confidence
        self.suggested_priority = suggested_priority
        self.keywords = keywords
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "primary_type": self.primary_type,
            "secondary_type": self.secondary_type,
            "confidence": self.confidence,
            "suggested_priority": self.suggested_priority,
            "keywords": self.keywords
        }


class AIService:
    """阿里云百炼AI识别服务类"""
    
    # 事件类型映射
    EVENT_TYPE_MAPPING = {
        "道路损坏": {
            "keywords": ["道路", "路面", "坑洞", "裂缝", "破损", "塌陷"],
            "priority": "high",
            "category": "infrastructure"
        },
        "垃圾堆积": {
            "keywords": ["垃圾", "废物", "堆积", "污染", "清理"],
            "priority": "medium",
            "category": "sanitation"
        },
        "违章建筑": {
            "keywords": ["建筑", "违章", "搭建", "占用", "拆除"],
            "priority": "high",
            "category": "construction"
        },
        "环境污染": {
            "keywords": ["污染", "排放", "废水", "废气", "噪音"],
            "priority": "high",
            "category": "environment"
        },
        "公共设施损坏": {
            "keywords": ["设施", "损坏", "路灯", "护栏", "标识"],
            "priority": "medium",
            "category": "facilities"
        },
        "交通问题": {
            "keywords": ["交通", "拥堵", "违停", "信号灯", "标线"],
            "priority": "medium",
            "category": "traffic"
        },
        "其他": {
            "keywords": [],
            "priority": "low",
            "category": "other"
        }
    }
    
    def __init__(self):
        """初始化AI服务"""
        self._validate_config()
        self.session = None
        self.fallback_enabled = True
        # 缓存配置
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1小时缓存
        self.cache_prefix = "ai_analysis"
        # 异步任务队列
        self._task_queue = asyncio.Queue()
        self._processing_tasks = {}
        logger.info("AI服务初始化成功")
    
    def _validate_config(self) -> None:
        """验证AI服务配置"""
        if not settings.ALIYUN_AI_API_KEY:
            logger.warning("阿里云AI API密钥未配置，将启用降级模式")
        if not settings.ALIYUN_AI_ENDPOINT:
            logger.warning("阿里云AI端点未配置，将启用降级模式")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _generate_cache_key(self, media_url: str, media_type: str) -> str:
        """生成缓存键"""
        # 使用URL的MD5哈希作为缓存键的一部分
        url_hash = hashlib.md5(media_url.encode()).hexdigest()
        return f"{self.cache_prefix}:{media_type}:{url_hash}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[AIAnalysisResult]:
        """从缓存获取分析结果"""
        if not self.cache_enabled:
            return None
        
        try:
            cached_data = await redis_service.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"从缓存获取AI分析结果: {cache_key}")
                return AIAnalysisResult(
                    event_type=data["event_type"],
                    description=data["description"],
                    confidence=data["confidence"],
                    details=data["details"],
                    raw_response=data["raw_response"]
                )
        except Exception as e:
            logger.warning(f"缓存读取失败: {str(e)}")
        
        return None
    
    async def _cache_result(self, cache_key: str, result: AIAnalysisResult) -> None:
        """缓存分析结果"""
        if not self.cache_enabled:
            return
        
        try:
            cache_data = {
                "event_type": result.event_type,
                "description": result.description,
                "confidence": result.confidence,
                "details": result.details,
                "raw_response": result.raw_response,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            await redis_service.set(
                cache_key, 
                json.dumps(cache_data, ensure_ascii=False),
                expire=self.cache_ttl
            )
            logger.info(f"AI分析结果已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"缓存写入失败: {str(e)}")
    
    async def _create_async_task(self, task_id: str, media_url: str, media_type: str) -> str:
        """创建异步分析任务"""
        task_info = {
            "task_id": task_id,
            "media_url": media_url,
            "media_type": media_type,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }
        
        # 将任务信息存储到Redis
        task_key = f"ai_task:{task_id}"
        await redis_service.set(
            task_key,
            json.dumps(task_info, ensure_ascii=False),
            expire=3600  # 任务信息保存1小时
        )
        
        # 将任务添加到队列
        await self._task_queue.put(task_info)
        
        logger.info(f"创建异步AI分析任务: {task_id}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取异步任务状态"""
        try:
            task_key = f"ai_task:{task_id}"
            task_data = await redis_service.get(task_key)
            if task_data:
                return json.loads(task_data)
        except Exception as e:
            logger.error(f"获取任务状态失败: {str(e)}")
        
        return None
    
    async def _process_async_tasks(self):
        """处理异步任务队列"""
        while True:
            try:
                # 从队列获取任务
                task_info = await self._task_queue.get()
                task_id = task_info["task_id"]
                
                logger.info(f"开始处理异步任务: {task_id}")
                
                # 更新任务状态为处理中
                task_info["status"] = "processing"
                task_info["started_at"] = datetime.utcnow().isoformat()
                
                task_key = f"ai_task:{task_id}"
                await redis_service.set(
                    task_key,
                    json.dumps(task_info, ensure_ascii=False),
                    expire=3600
                )
                
                try:
                    # 执行分析
                    if task_info["media_type"] == "image":
                        result = await self._analyze_image_internal(task_info["media_url"])
                    else:
                        result = await self._analyze_video_internal(task_info["media_url"])
                    
                    # 更新任务状态为完成
                    task_info["status"] = "completed"
                    task_info["completed_at"] = datetime.utcnow().isoformat()
                    task_info["result"] = result.to_dict()
                    
                except Exception as e:
                    # 更新任务状态为失败
                    task_info["status"] = "failed"
                    task_info["error"] = str(e)
                    task_info["failed_at"] = datetime.utcnow().isoformat()
                    logger.error(f"异步任务处理失败: {task_id}, 错误: {str(e)}")
                
                # 保存最终状态
                await redis_service.set(
                    task_key,
                    json.dumps(task_info, ensure_ascii=False),
                    expire=3600
                )
                
                logger.info(f"异步任务处理完成: {task_id}, 状态: {task_info['status']}")
                
            except Exception as e:
                logger.error(f"异步任务处理异常: {str(e)}")
                await asyncio.sleep(1)  # 避免快速循环
    
    async def analyze_image(self, image_url: str, use_cache: bool = True) -> AIAnalysisResult:
        """
        分析图像内容
        
        Args:
            image_url: 图像URL
            use_cache: 是否使用缓存
            
        Returns:
            AIAnalysisResult: 分析结果
            
        Raises:
            AIServiceError: AI服务调用失败
            ValidationError: 输入参数验证失败
        """
        try:
            # 验证输入
            if not image_url:
                raise ValidationError("图像URL不能为空")
            
            # 检查缓存
            cache_key = self._generate_cache_key(image_url, "image")
            if use_cache:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    return cached_result
            
            # 执行分析
            result = await self._analyze_image_internal(image_url)
            
            # 缓存结果
            if use_cache:
                await self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            if isinstance(e, (AIServiceError, ValidationError)):
                raise
            logger.error(f"图像分析异常: {str(e)}")
            # 尝试降级处理
            if self.fallback_enabled:
                return await self._fallback_image_analysis(image_url)
            raise AIServiceError(f"图像分析失败: {str(e)}")
    
    async def _analyze_image_internal(self, image_url: str) -> AIAnalysisResult:
        """内部图像分析方法"""
        # 检查AI服务是否可用
        if not self._is_ai_service_available():
            logger.warning("AI服务不可用，使用降级处理")
            return await self._fallback_image_analysis(image_url)
        
        # 调用阿里云百炼AI
        result = await self._call_ai_service("image", image_url)
        
        # 处理AI响应
        analysis_result = self._process_ai_response(result, "image")
        
        logger.info(f"图像分析完成，置信度: {analysis_result.confidence}")
        return analysis_result
    
    async def analyze_video(self, video_url: str, use_cache: bool = True) -> AIAnalysisResult:
        """
        分析视频内容
        
        Args:
            video_url: 视频URL
            use_cache: 是否使用缓存
            
        Returns:
            AIAnalysisResult: 分析结果
            
        Raises:
            AIServiceError: AI服务调用失败
            ValidationError: 输入参数验证失败
        """
        try:
            # 验证输入
            if not video_url:
                raise ValidationError("视频URL不能为空")
            
            # 检查缓存
            cache_key = self._generate_cache_key(video_url, "video")
            if use_cache:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    return cached_result
            
            # 执行分析
            result = await self._analyze_video_internal(video_url)
            
            # 缓存结果
            if use_cache:
                await self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            if isinstance(e, (AIServiceError, ValidationError)):
                raise
            logger.error(f"视频分析异常: {str(e)}")
            # 尝试降级处理
            if self.fallback_enabled:
                return await self._fallback_video_analysis(video_url)
            raise AIServiceError(f"视频分析失败: {str(e)}")
    
    async def _analyze_video_internal(self, video_url: str) -> AIAnalysisResult:
        """内部视频分析方法"""
        # 提取视频关键帧
        key_frames = await self.extract_video_frames(video_url)
        
        if not key_frames:
            raise AIServiceError("无法提取视频关键帧")
        
        # 分析关键帧
        frame_results = []
        for frame_url in key_frames[:3]:  # 最多分析3帧
            try:
                frame_result = await self._analyze_image_internal(frame_url)
                frame_results.append(frame_result)
            except Exception as e:
                logger.warning(f"关键帧分析失败: {str(e)}")
                continue
        
        if not frame_results:
            raise AIServiceError("所有关键帧分析失败")
        
        # 合并分析结果
        merged_result = self._merge_frame_results(frame_results)
        
        logger.info(f"视频分析完成，分析帧数: {len(frame_results)}")
        return merged_result
    
    async def extract_video_frames(self, video_url: str, max_frames: int = 5) -> List[str]:
        """
        提取视频关键帧
        
        Args:
            video_url: 视频URL
            max_frames: 最大提取帧数
            
        Returns:
            List[str]: 关键帧URL列表
            
        Raises:
            AIServiceError: 视频处理失败
        """
        try:
            # 下载视频文件到临时目录
            temp_video_path = await self._download_video(video_url)
            
            # 使用OpenCV提取关键帧
            frames = self._extract_frames_with_opencv(temp_video_path, max_frames)
            
            # 上传帧图像并获取URL
            frame_urls = []
            for i, frame in enumerate(frames):
                frame_url = await self._upload_frame_image(frame, f"frame_{i}")
                frame_urls.append(frame_url)
            
            # 清理临时文件
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            logger.info(f"视频关键帧提取完成，提取帧数: {len(frame_urls)}")
            return frame_urls
            
        except Exception as e:
            logger.error(f"视频关键帧提取失败: {str(e)}")
            raise AIServiceError(f"视频关键帧提取失败: {str(e)}")
    
    async def analyze_image_async(self, image_url: str) -> str:
        """
        异步分析图像内容
        
        Args:
            image_url: 图像URL
            
        Returns:
            str: 任务ID
        """
        task_id = f"img_{hashlib.md5(f'{image_url}_{datetime.utcnow().timestamp()}'.encode()).hexdigest()[:16]}"
        await self._create_async_task(task_id, image_url, "image")
        return task_id
    
    async def analyze_video_async(self, video_url: str) -> str:
        """
        异步分析视频内容
        
        Args:
            video_url: 视频URL
            
        Returns:
            str: 任务ID
        """
        task_id = f"vid_{hashlib.md5(f'{video_url}_{datetime.utcnow().timestamp()}'.encode()).hexdigest()[:16]}"
        await self._create_async_task(task_id, video_url, "video")
        return task_id
    
    async def start_async_processor(self):
        """启动异步任务处理器"""
        asyncio.create_task(self._process_async_tasks())
        logger.info("异步AI任务处理器已启动")
    
    async def classify_event_type(self, analysis: Dict[str, Any]) -> EventClassification:
        """
        基于AI分析结果分类事件类型
        
        Args:
            analysis: AI分析结果
            
        Returns:
            EventClassification: 事件分类结果
        """
        try:
            # 提取关键信息
            description = analysis.get("description", "").lower()
            details = analysis.get("details", {})
            
            # 计算各类型的匹配分数
            type_scores = {}
            for event_type, config in self.EVENT_TYPE_MAPPING.items():
                score = self._calculate_type_score(description, config["keywords"])
                if score > 0:
                    type_scores[event_type] = score
            
            # 确定主要类型
            if type_scores:
                primary_type = max(type_scores, key=type_scores.get)
                confidence = min(type_scores[primary_type] / 10.0, 1.0)  # 归一化到0-1
            else:
                primary_type = "其他"
                confidence = 0.3
            
            # 确定优先级
            priority_config = self.EVENT_TYPE_MAPPING.get(primary_type, {})
            suggested_priority = priority_config.get("priority", "low")
            
            # 提取关键词
            keywords = self._extract_keywords(description)
            
            classification = EventClassification(
                primary_type=primary_type,
                secondary_type=None,
                confidence=confidence,
                suggested_priority=suggested_priority,
                keywords=keywords
            )
            
            logger.info(f"事件分类完成: {primary_type}, 置信度: {confidence}")
            return classification
            
        except Exception as e:
            logger.error(f"事件分类失败: {str(e)}")
            # 返回默认分类
            return EventClassification(
                primary_type="其他",
                secondary_type=None,
                confidence=0.1,
                suggested_priority="low",
                keywords=[]
            )
    
    def _is_ai_service_available(self) -> bool:
        """检查AI服务是否可用"""
        return bool(settings.ALIYUN_AI_API_KEY and settings.ALIYUN_AI_ENDPOINT)
    
    async def _call_ai_service(self, media_type: str, media_url: str) -> Dict[str, Any]:
        """
        调用阿里云百炼AI服务
        
        Args:
            media_type: 媒体类型 (image/video)
            media_url: 媒体URL
            
        Returns:
            Dict[str, Any]: AI服务响应
        """
        try:
            session = await self._get_session()
            
            # 构建请求数据 - 使用OpenAI兼容格式
            if media_type == "image":
                request_data = {
                    "model": "qwen-vl-plus",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": media_url}
                                },
                                {
                                    "type": "text",
                                    "text": "请分析这张图片中的内容，识别可能存在的城市治理问题，如道路损坏、垃圾堆积、违章建筑、环境污染、公共设施损坏、交通问题等。请详细描述发现的问题，并评估问题的严重程度。"
                                }
                            ]
                        }
                    ]
                }
            else:  # video
                request_data = {
                    "model": "qwen-vl-max-latest",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "video",
                                    "video": [media_url]
                                },
                                {
                                    "type": "text",
                                    "text": "请分析这个视频中的内容，识别可能存在的城市治理问题，如道路损坏、垃圾堆积、违章建筑、环境污染、公共设施损坏、交通问题等。请详细描述发现的问题，并评估问题的严重程度。"
                                }
                            ]
                        }
                    ]
                }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {settings.ALIYUN_AI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # 发送请求到OpenAI兼容端点
            endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            async with session.post(
                endpoint,
                json=request_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise AIServiceError(f"AI服务调用失败: {response.status}, {error_text}")
                
                result = await response.json()
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"AI服务网络请求失败: {str(e)}")
            raise AIServiceError(f"AI服务网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"AI服务调用异常: {str(e)}")
            raise AIServiceError(f"AI服务调用失败: {str(e)}")
    
    def _process_ai_response(self, response: Dict[str, Any], media_type: str) -> AIAnalysisResult:
        """
        处理AI服务响应
        
        Args:
            response: AI服务原始响应
            media_type: 媒体类型
            
        Returns:
            AIAnalysisResult: 处理后的分析结果
        """
        try:
            # 处理OpenAI兼容格式的响应
            choices = response.get("choices", [])
            
            if not choices:
                raise AIServiceError("AI响应格式错误：缺少choices")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            # 解析内容并分类
            event_type, description, confidence = self._parse_ai_content(content)
            
            # 构建详细信息
            details = {
                "media_type": media_type,
                "analysis_method": "aliyun_ai",
                "model": "qwen-vl-plus",
                "usage": output.get("usage", {}),
                "finish_reason": choices[0].get("finish_reason", "")
            }
            
            return AIAnalysisResult(
                event_type=event_type,
                description=description,
                confidence=confidence,
                details=details,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"AI响应处理失败: {str(e)}")
            raise AIServiceError(f"AI响应处理失败: {str(e)}")
    
    def _parse_ai_content(self, content: str) -> Tuple[str, str, float]:
        """
        解析AI返回的内容
        
        Args:
            content: AI返回的文本内容
            
        Returns:
            Tuple[str, str, float]: (事件类型, 描述, 置信度)
        """
        # 基于关键词匹配确定事件类型
        content_lower = content.lower()
        best_match = "其他"
        best_score = 0
        
        for event_type, config in self.EVENT_TYPE_MAPPING.items():
            score = self._calculate_type_score(content_lower, config["keywords"])
            if score > best_score:
                best_score = score
                best_match = event_type
        
        # 计算置信度
        confidence = min(best_score / 5.0, 1.0) if best_score > 0 else 0.3
        
        # 清理和格式化描述
        description = content.strip()
        if len(description) > 500:
            description = description[:500] + "..."
        
        return best_match, description, confidence
    
    def _calculate_type_score(self, text: str, keywords: List[str]) -> int:
        """
        计算文本与关键词的匹配分数
        
        Args:
            text: 待匹配文本
            keywords: 关键词列表
            
        Returns:
            int: 匹配分数
        """
        if not keywords:
            return 0
        
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        
        return score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        keywords = []
        
        # 遍历所有事件类型的关键词
        for event_type, config in self.EVENT_TYPE_MAPPING.items():
            for keyword in config["keywords"]:
                if keyword in text and keyword not in keywords:
                    keywords.append(keyword)
        
        return keywords[:10]  # 最多返回10个关键词
    
    async def _fallback_image_analysis(self, image_url: str) -> AIAnalysisResult:
        """
        图像分析降级处理
        
        Args:
            image_url: 图像URL
            
        Returns:
            AIAnalysisResult: 降级分析结果
        """
        logger.info("使用降级模式进行图像分析")
        
        # 基于URL或文件名进行简单推断
        url_lower = image_url.lower()
        event_type = "其他问题"
        description = "已接收您上传的图片，AI智能分析服务暂时不可用。请在事件描述中详细说明具体问题，工作人员会根据图片和描述及时处理。"
        confidence = 0.4
        
        # 简单的关键词匹配
        if any(keyword in url_lower for keyword in ["road", "路", "道路", "street"]):
            event_type = "道路交通"
            description = "检测到可能的道路交通相关问题。请在描述中说明具体情况，如路面损坏、交通设施故障等。"
            confidence = 0.5
        elif any(keyword in url_lower for keyword in ["garbage", "trash", "垃圾", "waste"]):
            event_type = "环境卫生"
            description = "检测到可能的环境卫生问题。请说明垃圾类型、堆积程度等具体情况。"
            confidence = 0.5
        elif any(keyword in url_lower for keyword in ["building", "construction", "建筑", "施工"]):
            event_type = "违章建筑"
            description = "检测到可能的建筑相关问题。请描述具体的违章情况或建筑安全隐患。"
            confidence = 0.5
        elif any(keyword in url_lower for keyword in ["water", "flood", "积水", "排水"]):
            event_type = "市政设施"
            description = "检测到可能的水务或排水问题。请说明积水位置、程度等详细信息。"
            confidence = 0.5
        
        details = {
            "media_type": "image",
            "analysis_method": "fallback",
            "fallback_reason": "AI服务不可用"
        }
        
        return AIAnalysisResult(
            event_type=event_type,
            description=description,
            confidence=confidence,
            details=details,
            raw_response={"fallback": True}
        )
    
    async def _fallback_video_analysis(self, video_url: str) -> AIAnalysisResult:
        """
        视频分析降级处理
        
        Args:
            video_url: 视频URL
            
        Returns:
            AIAnalysisResult: 降级分析结果
        """
        logger.info("使用降级模式进行视频分析")
        
        details = {
            "media_type": "video",
            "analysis_method": "fallback",
            "fallback_reason": "AI服务不可用或视频处理失败"
        }
        
        return AIAnalysisResult(
            event_type="其他",
            description="视频内容分析（降级模式）",
            confidence=0.1,
            details=details,
            raw_response={"fallback": True}
        )
    
    def _merge_frame_results(self, frame_results: List[AIAnalysisResult]) -> AIAnalysisResult:
        """
        合并多个关键帧的分析结果
        
        Args:
            frame_results: 关键帧分析结果列表
            
        Returns:
            AIAnalysisResult: 合并后的分析结果
        """
        if not frame_results:
            raise AIServiceError("没有可合并的分析结果")
        
        # 统计事件类型
        type_counts = {}
        total_confidence = 0
        descriptions = []
        
        for result in frame_results:
            event_type = result.event_type
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
            total_confidence += result.confidence
            descriptions.append(result.description)
        
        # 确定最终事件类型
        final_event_type = max(type_counts, key=type_counts.get)
        
        # 计算平均置信度
        avg_confidence = total_confidence / len(frame_results)
        
        # 合并描述
        final_description = f"视频分析结果（基于{len(frame_results)}个关键帧）：" + "; ".join(descriptions[:2])
        
        # 构建详细信息
        details = {
            "media_type": "video",
            "analysis_method": "multi_frame",
            "frame_count": len(frame_results),
            "type_distribution": type_counts,
            "frame_results": [result.to_dict() for result in frame_results]
        }
        
        return AIAnalysisResult(
            event_type=final_event_type,
            description=final_description,
            confidence=avg_confidence,
            details=details,
            raw_response={"merged": True}
        )
    
    async def _download_video(self, video_url: str) -> str:
        """
        下载视频文件到临时目录
        
        Args:
            video_url: 视频URL
            
        Returns:
            str: 临时文件路径
        """
        try:
            session = await self._get_session()
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            # 下载视频
            async with session.get(video_url) as response:
                if response.status != 200:
                    raise AIServiceError(f"视频下载失败: {response.status}")
                
                with open(temp_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"视频下载失败: {str(e)}")
            raise AIServiceError(f"视频下载失败: {str(e)}")
    
    def _extract_frames_with_opencv(self, video_path: str, max_frames: int) -> List[np.ndarray]:
        """
        使用OpenCV提取视频关键帧
        
        Args:
            video_path: 视频文件路径
            max_frames: 最大提取帧数
            
        Returns:
            List[np.ndarray]: 关键帧列表
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise AIServiceError("无法打开视频文件")
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames == 0:
                raise AIServiceError("视频文件为空")
            
            # 计算提取间隔
            if total_frames <= max_frames:
                frame_indices = list(range(total_frames))
            else:
                step = total_frames // max_frames
                frame_indices = [i * step for i in range(max_frames)]
            
            frames = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    frames.append(frame)
                else:
                    logger.warning(f"无法读取第{frame_idx}帧")
            
            cap.release()
            
            if not frames:
                raise AIServiceError("未能提取到任何视频帧")
            
            return frames
            
        except Exception as e:
            logger.error(f"OpenCV视频帧提取失败: {str(e)}")
            raise AIServiceError(f"视频帧提取失败: {str(e)}")
    
    async def _upload_frame_image(self, frame: np.ndarray, frame_name: str) -> str:
        """
        上传帧图像并返回URL
        
        Args:
            frame: 图像帧数据
            frame_name: 帧名称
            
        Returns:
            str: 图像URL
        """
        try:
            # 将OpenCV图像转换为PIL图像
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # 保存到内存缓冲区
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(buffer.getvalue())
            temp_file.close()
            
            # 这里应该调用OSS服务上传文件
            # 由于需要避免循环导入，这里返回一个模拟URL
            # 在实际实现中，应该注入OSS服务或使用其他方式
            frame_url = f"temp://frame_{frame_name}_{datetime.now().timestamp()}.jpg"
            
            # 清理临时文件
            os.remove(temp_file.name)
            
            return frame_url
            
        except Exception as e:
            logger.error(f"帧图像上传失败: {str(e)}")
            raise AIServiceError(f"帧图像上传失败: {str(e)}")


# 创建全局AI服务实例
ai_service = AIService()