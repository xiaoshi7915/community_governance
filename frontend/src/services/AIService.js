import { HttpClient } from './HttpClient.js';

/**
 * AI识别服务类
 * 处理AI分析功能、图像分析、视频分析接口调用
 * 添加事件类型获取和分类功能
 */
export class AIService extends HttpClient {
  constructor() {
    super('/ai');
    
    // AI分析类型枚举
    this.ANALYSIS_TYPE = {
      IMAGE: 'image',
      VIDEO: 'video',
      TEXT: 'text'
    };

    // 置信度阈值
    this.CONFIDENCE_THRESHOLD = {
      HIGH: 0.8,
      MEDIUM: 0.6,
      LOW: 0.4
    };
    
    // 添加认证拦截器
    this.addRequestInterceptor(this.addAuthHeader.bind(this));
  }
  
  /**
   * 添加认证头
   * @param {Object} config - 请求配置
   * @returns {Object} 修改后的配置
   */
  addAuthHeader(config) {
    const token = localStorage.getItem('access_token');
    if (token) {
      // 确保headers对象存在
      if (!config.options) {
        config.options = {};
      }
      if (!config.options.headers) {
        config.options.headers = {};
      }
      
      // 添加Authorization头
      if (!config.options.headers.Authorization) {
        config.options.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  }

  /**
   * 分析图像
   * @param {string} imageUrl - 图像URL
   * @param {Object} options - 分析选项
   * @param {Array} options.detect_types - 检测类型列表
   * @param {number} options.confidence_threshold - 置信度阈值
   * @returns {Promise<Object>} 分析结果
   */
  async analyzeImage(imageUrl, options = {}) {
    try {
      const requestData = {
        image_url: imageUrl,
        detect_types: options.detect_types || [],
        confidence_threshold: options.confidence_threshold || this.CONFIDENCE_THRESHOLD.MEDIUM,
        return_details: options.return_details !== false
      };

      const response = await this.post('/analyze-image', requestData);

      if (response.success) {
        // 处理分析结果
        const processedResult = this.processAnalysisResult(response.data, this.ANALYSIS_TYPE.IMAGE);
        
        // 触发图像分析完成事件
        this.dispatchAIEvent('image-analyzed', { 
          imageUrl, 
          result: processedResult 
        });

        return {
          ...response,
          data: processedResult
        };
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '图像分析失败');
    }
  }

  /**
   * 分析视频
   * @param {string} videoUrl - 视频URL
   * @param {Object} options - 分析选项
   * @param {Array} options.detect_types - 检测类型列表
   * @param {number} options.confidence_threshold - 置信度阈值
   * @param {number} options.sample_interval - 采样间隔(秒)
   * @returns {Promise<Object>} 分析结果
   */
  async analyzeVideo(videoUrl, options = {}) {
    try {
      const requestData = {
        video_url: videoUrl,
        detect_types: options.detect_types || [],
        confidence_threshold: options.confidence_threshold || this.CONFIDENCE_THRESHOLD.MEDIUM,
        sample_interval: options.sample_interval || 5,
        return_details: options.return_details !== false
      };

      const response = await this.post('/analyze-video', requestData);

      if (response.success) {
        // 处理分析结果
        const processedResult = this.processAnalysisResult(response.data, this.ANALYSIS_TYPE.VIDEO);
        
        // 触发视频分析完成事件
        this.dispatchAIEvent('video-analyzed', { 
          videoUrl, 
          result: processedResult 
        });

        return {
          ...response,
          data: processedResult
        };
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '视频分析失败');
    }
  }

  /**
   * 批量分析媒体文件
   * @param {Array} mediaUrls - 媒体文件URL列表
   * @param {Object} options - 分析选项
   * @returns {Promise<Object>} 批量分析结果
   */
  async batchAnalyzeMedia(mediaUrls, options = {}) {
    try {
      const requestData = {
        media_urls: mediaUrls,
        detect_types: options.detect_types || [],
        confidence_threshold: options.confidence_threshold || this.CONFIDENCE_THRESHOLD.MEDIUM,
        return_details: options.return_details !== false
      };

      const response = await this.post('/batch-analyze', requestData);

      if (response.success) {
        // 处理批量分析结果
        const processedResults = response.data.map(result => 
          this.processAnalysisResult(result, result.media_type)
        );

        // 触发批量分析完成事件
        this.dispatchAIEvent('batch-analyzed', { 
          mediaUrls, 
          results: processedResults 
        });

        return {
          ...response,
          data: processedResults
        };
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '批量分析失败');
    }
  }

  /**
   * 获取事件类型列表
   * @returns {Promise<Object>} 事件类型列表
   */
  async getEventTypes() {
    try {
      const response = await this.get('/event-types');
      return response;
    } catch (error) {
      throw new Error(error.message || '获取事件类型失败');
    }
  }

  /**
   * 根据分析结果推荐事件类型
   * @param {Object} analysisResult - 分析结果
   * @returns {Promise<Object>} 推荐的事件类型
   */
  async recommendEventType(analysisResult) {
    try {
      const response = await this.post('/recommend-event-type', {
        analysis_result: analysisResult
      });

      return response;
    } catch (error) {
      throw new Error(error.message || '事件类型推荐失败');
    }
  }

  /**
   * 获取分析历史记录
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.analysis_type - 分析类型筛选
   * @returns {Promise<Object>} 分析历史
   */
  async getAnalysisHistory(params = {}) {
    try {
      const queryParams = {
        page: params.page || 1,
        page_size: params.page_size || 20,
        ...params
      };

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/history?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取分析历史失败');
    }
  }

  /**
   * 获取分析任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 任务状态
   */
  async getAnalysisTaskStatus(taskId) {
    try {
      const response = await this.get(`/task/${taskId}/status`);
      return response;
    } catch (error) {
      throw new Error(error.message || '获取任务状态失败');
    }
  }

  /**
   * 取消分析任务
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>} 取消结果
   */
  async cancelAnalysisTask(taskId) {
    try {
      const response = await this.post(`/task/${taskId}/cancel`);
      
      if (response.success) {
        // 触发任务取消事件
        this.dispatchAIEvent('task-cancelled', { taskId });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '取消任务失败');
    }
  }

  /**
   * 获取AI模型信息
   * @returns {Promise<Object>} 模型信息
   */
  async getModelInfo() {
    try {
      const response = await this.get('/models');
      return response;
    } catch (error) {
      throw new Error(error.message || '获取模型信息失败');
    }
  }

  /**
   * 提交用户反馈
   * @param {string} analysisId - 分析ID
   * @param {Object} feedback - 反馈数据
   * @param {boolean} feedback.is_correct - 分析结果是否正确
   * @param {string} feedback.correct_type - 正确的事件类型
   * @param {string} feedback.comment - 反馈评论
   * @returns {Promise<Object>} 提交结果
   */
  async submitFeedback(analysisId, feedback) {
    try {
      const response = await this.post(`/feedback/${analysisId}`, feedback);
      
      if (response.success) {
        // 触发反馈提交事件
        this.dispatchAIEvent('feedback-submitted', { 
          analysisId, 
          feedback 
        });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '提交反馈失败');
    }
  }

  /**
   * 处理分析结果
   * @param {Object} rawResult - 原始分析结果
   * @param {string} analysisType - 分析类型
   * @returns {Object} 处理后的结果
   */
  processAnalysisResult(rawResult, analysisType) {
    const processed = {
      ...rawResult,
      analysis_type: analysisType,
      processed_at: new Date().toISOString()
    };

    // 处理检测结果
    if (rawResult.detections) {
      processed.detections = rawResult.detections.map(detection => ({
        ...detection,
        confidence_level: this.getConfidenceLevel(detection.confidence),
        confidence_text: this.getConfidenceText(detection.confidence)
      }));

      // 按置信度排序
      processed.detections.sort((a, b) => b.confidence - a.confidence);
    }

    // 处理推荐的事件类型
    if (rawResult.recommended_event_types) {
      processed.recommended_event_types = rawResult.recommended_event_types.map(type => ({
        ...type,
        confidence_level: this.getConfidenceLevel(type.confidence),
        confidence_text: this.getConfidenceText(type.confidence)
      }));
    }

    // 生成摘要
    processed.summary = this.generateAnalysisSummary(processed);

    return processed;
  }

  /**
   * 获取置信度等级
   * @param {number} confidence - 置信度值
   * @returns {string} 置信度等级
   */
  getConfidenceLevel(confidence) {
    if (confidence >= this.CONFIDENCE_THRESHOLD.HIGH) {
      return 'high';
    } else if (confidence >= this.CONFIDENCE_THRESHOLD.MEDIUM) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * 获取置信度文本
   * @param {number} confidence - 置信度值
   * @returns {string} 置信度文本
   */
  getConfidenceText(confidence) {
    const level = this.getConfidenceLevel(confidence);
    const levelMap = {
      high: '高',
      medium: '中',
      low: '低'
    };
    return `${levelMap[level]} (${Math.round(confidence * 100)}%)`;
  }

  /**
   * 生成分析摘要
   * @param {Object} result - 分析结果
   * @returns {string} 分析摘要
   */
  generateAnalysisSummary(result) {
    const { detections, recommended_event_types } = result;
    
    let summary = '';

    if (detections && detections.length > 0) {
      const highConfidenceDetections = detections.filter(d => 
        d.confidence >= this.CONFIDENCE_THRESHOLD.HIGH
      );

      if (highConfidenceDetections.length > 0) {
        const topDetection = highConfidenceDetections[0];
        summary += `检测到${topDetection.label}，置信度${Math.round(topDetection.confidence * 100)}%`;
      } else {
        const topDetection = detections[0];
        summary += `可能检测到${topDetection.label}，置信度${Math.round(topDetection.confidence * 100)}%`;
      }
    }

    if (recommended_event_types && recommended_event_types.length > 0) {
      const topRecommendation = recommended_event_types[0];
      if (summary) summary += '；';
      summary += `推荐事件类型：${topRecommendation.name}`;
    }

    return summary || '未检测到明确的事件类型';
  }

  /**
   * 触发AI相关的自定义事件
   * @param {string} eventType - 事件类型
   * @param {Object} data - 事件数据
   */
  dispatchAIEvent(eventType, data = {}) {
    const event = new CustomEvent(`ai:${eventType}`, {
      detail: data
    });
    window.dispatchEvent(event);
  }

  /**
   * 检查分析结果是否可信
   * @param {Object} result - 分析结果
   * @returns {boolean} 是否可信
   */
  static isResultReliable(result) {
    if (!result.detections || result.detections.length === 0) {
      return false;
    }

    const topDetection = result.detections[0];
    return topDetection.confidence >= 0.6; // 60%以上认为可信
  }

  /**
   * 获取最佳检测结果
   * @param {Object} result - 分析结果
   * @returns {Object|null} 最佳检测结果
   */
  static getBestDetection(result) {
    if (!result.detections || result.detections.length === 0) {
      return null;
    }

    return result.detections[0]; // 已按置信度排序
  }

  /**
   * 格式化分析结果用于显示
   * @param {Object} result - 分析结果
   * @returns {Object} 格式化后的结果
   */
  static formatResultForDisplay(result) {
    return {
      ...result,
      isReliable: AIService.isResultReliable(result),
      bestDetection: AIService.getBestDetection(result),
      detectionCount: result.detections ? result.detections.length : 0,
      hasRecommendations: result.recommended_event_types && result.recommended_event_types.length > 0
    };
  }
}