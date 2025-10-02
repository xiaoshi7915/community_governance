# 阿里云百炼AI识别服务使用指南

## 概述

阿里云百炼AI识别服务是基层治理智能体后端系统的核心组件之一，提供图像识别、视频分析、事件分类等AI功能。该服务集成了阿里云百炼AI平台，能够智能识别城市治理相关问题。

## 功能特性

### 1. 图像识别
- 支持多种图像格式（JPEG、PNG、GIF、WebP）
- 智能识别城市治理问题类型
- 提供置信度评估
- 支持降级处理机制

### 2. 视频分析
- 自动提取视频关键帧
- 基于关键帧进行内容分析
- 合并多帧分析结果
- 支持多种视频格式

### 3. 事件分类
- 基于AI分析结果进行事件分类
- 支持多种事件类型：
  - 道路损坏
  - 垃圾堆积
  - 违章建筑
  - 环境污染
  - 公共设施损坏
  - 交通问题
  - 其他

### 4. 降级处理
- 当AI服务不可用时自动启用降级模式
- 基于关键词匹配的简单分类
- 确保系统稳定性

## API端点

### 图像分析
```http
POST /api/v1/ai/analyze-image
Content-Type: application/json
Authorization: Bearer <token>

{
  "image_url": "https://example.com/image.jpg"
}
```

### 视频分析
```http
POST /api/v1/ai/analyze-video
Content-Type: application/json
Authorization: Bearer <token>

{
  "video_url": "https://example.com/video.mp4",
  "max_frames": 5
}
```

### 事件分类
```http
POST /api/v1/ai/classify-event
Content-Type: application/json
Authorization: Bearer <token>

{
  "analysis_result": {
    "description": "道路表面有裂缝",
    "details": {"confidence": 0.8}
  }
}
```

### 获取事件类型列表
```http
GET /api/v1/ai/event-types
Authorization: Bearer <token>
```

### 获取服务状态
```http
GET /api/v1/ai/service-status
Authorization: Bearer <token>
```

## 配置说明

### 环境变量
```bash
# 阿里云百炼AI配置
ALIYUN_AI_API_KEY=your-api-key
ALIYUN_AI_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 事件类型配置
系统预定义了以下事件类型及其关键词：

```python
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
    # ... 其他类型
}
```

## 使用示例

### Python客户端示例
```python
import aiohttp
import asyncio

async def analyze_image(image_url, token):
    async with aiohttp.ClientSession() as session:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {'image_url': image_url}
        
        async with session.post(
            'http://localhost:8000/api/v1/ai/analyze-image',
            json=data,
            headers=headers
        ) as response:
            result = await response.json()
            return result

# 使用示例
result = asyncio.run(analyze_image(
    'https://example.com/road-damage.jpg',
    'your-jwt-token'
))
print(f"事件类型: {result['data']['event_type']}")
print(f"置信度: {result['data']['confidence']}")
```

### JavaScript客户端示例
```javascript
async function analyzeImage(imageUrl, token) {
    const response = await fetch('/api/v1/ai/analyze-image', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image_url: imageUrl
        })
    });
    
    const result = await response.json();
    return result;
}

// 使用示例
analyzeImage('https://example.com/image.jpg', 'your-token')
    .then(result => {
        console.log('事件类型:', result.data.event_type);
        console.log('置信度:', result.data.confidence);
    });
```

## 错误处理

### 常见错误码
- `400`: 请求参数验证失败
- `401`: 认证失败
- `502`: AI服务不可用
- `500`: 服务器内部错误

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "AI服务调用失败",
    "details": {
      "service": "aliyun_ai"
    }
  },
  "timestamp": "2024-12-15T10:30:00Z"
}
```

## 性能优化

### 缓存策略
- AI识别结果自动缓存
- 相同内容避免重复识别
- 缓存过期时间可配置

### 并发控制
- 支持并发请求处理
- 自动限流保护
- 请求队列管理

### 资源管理
- HTTP连接池复用
- 临时文件自动清理
- 内存使用优化

## 监控和日志

### 日志记录
- 结构化日志输出
- 请求响应跟踪
- 错误详情记录
- 性能指标统计

### 监控指标
- 请求成功率
- 平均响应时间
- AI服务可用性
- 错误率统计

## 故障排除

### 常见问题

1. **AI服务不可用**
   - 检查API密钥配置
   - 验证网络连接
   - 查看服务状态端点

2. **识别准确率低**
   - 检查图像质量
   - 验证图像内容相关性
   - 调整置信度阈值

3. **视频处理失败**
   - 检查视频格式支持
   - 验证文件大小限制
   - 查看OpenCV依赖

### 调试技巧
- 启用详细日志记录
- 使用服务状态检查
- 测试降级模式功能
- 验证配置参数

## 扩展开发

### 添加新事件类型
```python
# 在EVENT_TYPE_MAPPING中添加新类型
"新事件类型": {
    "keywords": ["关键词1", "关键词2"],
    "priority": "medium",
    "category": "new_category"
}
```

### 自定义分析逻辑
```python
class CustomAIService(AIService):
    def _parse_ai_content(self, content: str):
        # 自定义解析逻辑
        return super()._parse_ai_content(content)
```

### 集成其他AI服务
```python
async def _call_custom_ai_service(self, media_type: str, media_url: str):
    # 集成其他AI服务的实现
    pass
```

## 最佳实践

1. **图像预处理**
   - 确保图像清晰度
   - 控制文件大小
   - 选择合适格式

2. **错误处理**
   - 实现重试机制
   - 使用降级策略
   - 记录详细日志

3. **性能优化**
   - 启用结果缓存
   - 控制并发数量
   - 监控资源使用

4. **安全考虑**
   - 验证输入参数
   - 限制文件大小
   - 保护API密钥

## 版本更新

### v1.0.0 (当前版本)
- 基础图像识别功能
- 视频关键帧提取
- 事件类型分类
- 降级处理机制
- 完整的API端点

### 计划功能
- 批量处理优化
- 更多事件类型支持
- 实时视频流分析
- 自定义模型训练