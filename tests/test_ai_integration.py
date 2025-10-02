"""
AI识别API端点集成测试
测试新增的缓存和异步处理功能
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.services.ai_service import ai_service, AIAnalysisResult


class TestAIIntegration:
    """AI识别API集成测试类"""
    
    @pytest.mark.asyncio
    async def test_ai_service_caching(self):
        """测试AI服务缓存功能"""
        # 测试缓存键生成
        cache_key = ai_service._generate_cache_key("https://example.com/test.jpg", "image")
        assert cache_key.startswith("ai_analysis:image:")
        assert len(cache_key) > 20  # 确保包含哈希值
    
    @pytest.mark.asyncio
    async def test_async_task_creation(self):
        """测试异步任务创建"""
        # 测试异步图像分析任务创建
        task_id = await ai_service.analyze_image_async("https://example.com/test.jpg")
        assert task_id.startswith("img_")
        assert len(task_id) == 20  # img_ + 16字符哈希
        
        # 测试异步视频分析任务创建
        task_id = await ai_service.analyze_video_async("https://example.com/test.mp4")
        assert task_id.startswith("vid_")
        assert len(task_id) == 20  # vid_ + 16字符哈希
    
    @pytest.mark.asyncio
    @patch('app.services.ai_service.AIService._call_ai_service')
    @patch('app.services.ai_service.AIService._is_ai_service_available')
    async def test_analyze_image_with_caching(self, mock_available, mock_call_ai):
        """测试图像分析缓存功能"""
        # 模拟AI服务可用
        mock_available.return_value = True
        
        # 模拟AI服务响应
        mock_response = {
            'output': {
                'choices': [{
                    'finish_reason': 'stop',
                    'message': {
                        'content': '图像中显示道路表面有明显的裂缝和坑洞，属于道路损坏问题。'
                    }
                }],
                'usage': {'input_tokens': 100, 'output_tokens': 50}
            }
        }
        mock_call_ai.return_value = mock_response
        
        test_url = "https://example.com/unique-test-image.jpg"
        
        # 第一次调用（应该调用AI服务）
        result1 = await ai_service.analyze_image(test_url, use_cache=True)
        assert isinstance(result1, AIAnalysisResult)
        assert mock_call_ai.call_count == 1
        
        # 第二次调用（应该从缓存获取）
        result2 = await ai_service.analyze_image(test_url, use_cache=True)
        assert isinstance(result2, AIAnalysisResult)
        # AI服务不应该被再次调用
        assert mock_call_ai.call_count == 1
        
        # 结果应该相同
        assert result1.event_type == result2.event_type
        assert result1.description == result2.description
    
    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(self):
        """测试缓存键的唯一性"""
        url1 = "https://example.com/image1.jpg"
        url2 = "https://example.com/image2.jpg"
        
        key1 = ai_service._generate_cache_key(url1, "image")
        key2 = ai_service._generate_cache_key(url2, "image")
        key3 = ai_service._generate_cache_key(url1, "video")
        
        # 不同URL应该生成不同的缓存键
        assert key1 != key2
        
        # 相同URL但不同媒体类型应该生成不同的缓存键
        assert key1 != key3
        
        # 相同URL和媒体类型应该生成相同的缓存键
        key4 = ai_service._generate_cache_key(url1, "image")
        assert key1 == key4
