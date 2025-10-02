import { HttpClient } from './HttpClient.js';

/**
 * 事件管理服务类
 * 处理事件CRUD操作、列表查询、详情获取、状态更新
 * 添加事件时间线和统计数据获取
 */
export class EventService extends HttpClient {
  constructor() {
    super('/events');
    
    // 事件状态枚举
    this.EVENT_STATUS = {
      PENDING: 'pending',
      IN_PROGRESS: 'in_progress', 
      RESOLVED: 'resolved',
      CLOSED: 'closed'
    };

    // 事件优先级枚举
    this.EVENT_PRIORITY = {
      LOW: 'low',
      MEDIUM: 'medium',
      HIGH: 'high',
      URGENT: 'urgent'
    };
  }

  /**
   * 创建新事件
   * @param {Object} eventData - 事件数据
   * @param {string} eventData.title - 事件标题
   * @param {string} eventData.description - 事件描述
   * @param {string} eventData.event_type - 事件类型
   * @param {string} eventData.priority - 优先级
   * @param {Object} eventData.location - 位置信息
   * @param {Array} eventData.media_urls - 媒体文件URLs
   * @returns {Promise<Object>} 创建结果
   */
  async createEvent(eventData) {
    try {
      const response = await this.post('/', {
        title: eventData.title,
        description: eventData.description,
        event_type: eventData.event_type,
        priority: eventData.priority || this.EVENT_PRIORITY.MEDIUM,
        location: eventData.location,
        media_urls: eventData.media_urls || [],
        metadata: eventData.metadata || {}
      });

      if (response.success) {
        // 触发事件创建成功事件
        this.dispatchEventEvent('created', { event: response.data });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '事件创建失败');
    }
  }

  /**
   * 获取事件列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.status - 状态筛选
   * @param {string} params.event_type - 类型筛选
   * @param {string} params.priority - 优先级筛选
   * @param {string} params.search - 搜索关键词
   * @param {string} params.sort_by - 排序字段
   * @param {string} params.sort_order - 排序方向
   * @returns {Promise<Object>} 事件列表
   */
  async getEvents(params = {}) {
    try {
      const queryParams = {
        page: params.page || 1,
        page_size: params.page_size || 20,
        ...params
      };

      // 过滤空值参数
      Object.keys(queryParams).forEach(key => {
        if (queryParams[key] === undefined || queryParams[key] === '') {
          delete queryParams[key];
        }
      });

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取事件列表失败');
    }
  }

  /**
   * 获取事件详情
   * @param {string} eventId - 事件ID
   * @returns {Promise<Object>} 事件详情
   */
  async getEventDetail(eventId) {
    try {
      const response = await this.get(`/${eventId}`);
      return response;
    } catch (error) {
      throw new Error(error.message || '获取事件详情失败');
    }
  }

  /**
   * 更新事件信息
   * @param {string} eventId - 事件ID
   * @param {Object} updateData - 更新数据
   * @returns {Promise<Object>} 更新结果
   */
  async updateEvent(eventId, updateData) {
    try {
      const response = await this.put(`/${eventId}`, updateData);

      if (response.success) {
        // 触发事件更新事件
        this.dispatchEventEvent('updated', { 
          eventId, 
          event: response.data,
          updates: updateData 
        });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '事件更新失败');
    }
  }

  /**
   * 更新事件状态
   * @param {string} eventId - 事件ID
   * @param {string} status - 新状态
   * @param {string} comment - 状态变更备注
   * @returns {Promise<Object>} 更新结果
   */
  async updateEventStatus(eventId, status, comment = '') {
    try {
      const response = await this.patch(`/${eventId}/status`, {
        status,
        comment
      });

      if (response.success) {
        // 触发状态更新事件
        this.dispatchEventEvent('status-updated', { 
          eventId, 
          status, 
          comment,
          event: response.data 
        });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '状态更新失败');
    }
  }

  /**
   * 删除事件
   * @param {string} eventId - 事件ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteEvent(eventId) {
    try {
      const response = await this.delete(`/${eventId}`);

      if (response.success) {
        // 触发事件删除事件
        this.dispatchEventEvent('deleted', { eventId });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '事件删除失败');
    }
  }

  /**
   * 获取事件时间线
   * @param {string} eventId - 事件ID
   * @returns {Promise<Object>} 时间线数据
   */
  async getEventTimeline(eventId) {
    try {
      const response = await this.get(`/${eventId}/timeline`);
      return response;
    } catch (error) {
      throw new Error(error.message || '获取事件时间线失败');
    }
  }

  /**
   * 添加事件评论
   * @param {string} eventId - 事件ID
   * @param {string} comment - 评论内容
   * @param {Array} attachments - 附件URLs
   * @returns {Promise<Object>} 添加结果
   */
  async addEventComment(eventId, comment, attachments = []) {
    try {
      const response = await this.post(`/${eventId}/comments`, {
        comment,
        attachments
      });

      if (response.success) {
        // 触发评论添加事件
        this.dispatchEventEvent('comment-added', { 
          eventId, 
          comment: response.data 
        });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '添加评论失败');
    }
  }

  /**
   * 获取事件评论列表
   * @param {string} eventId - 事件ID
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 评论列表
   */
  async getEventComments(eventId, params = {}) {
    try {
      const queryParams = {
        page: params.page || 1,
        page_size: params.page_size || 10,
        ...params
      };

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/${eventId}/comments?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取评论列表失败');
    }
  }

  /**
   * 获取我的事件列表
   * @param {Object} params - 查询参数
   * @returns {Promise<Object>} 我的事件列表
   */
  async getMyEvents(params = {}) {
    try {
      const queryParams = {
        page: params.page || 1,
        page_size: params.page_size || 20,
        ...params
      };

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/my?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取我的事件失败');
    }
  }

  /**
   * 获取事件统计数据
   * @param {Object} params - 统计参数
   * @param {string} params.period - 统计周期 (day|week|month|year)
   * @param {string} params.start_date - 开始日期
   * @param {string} params.end_date - 结束日期
   * @returns {Promise<Object>} 统计数据
   */
  async getEventStatistics(params = {}) {
    try {
      const queryParams = {
        period: params.period || 'month',
        ...params
      };

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/statistics?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取统计数据失败');
    }
  }

  /**
   * 获取用户统计数据
   * @returns {Promise<Object>} 用户统计数据
   */
  async getUserStats() {
    try {
      const response = await this.get('/user/stats');
      return response;
    } catch (error) {
      throw new Error(error.message || '获取用户统计数据失败');
    }
  }

  /**
   * 获取事件类型列表
   * @returns {Promise<Object>} 事件类型列表
   */
  async getEventTypes() {
    try {
      const response = await this.get('/types');
      return response;
    } catch (error) {
      throw new Error(error.message || '获取事件类型失败');
    }
  }

  /**
   * 搜索事件
   * @param {string} keyword - 搜索关键词
   * @param {Object} filters - 筛选条件
   * @returns {Promise<Object>} 搜索结果
   */
  async searchEvents(keyword, filters = {}) {
    try {
      const params = {
        search: keyword,
        ...filters
      };

      return await this.getEvents(params);
    } catch (error) {
      throw new Error(error.message || '搜索事件失败');
    }
  }

  /**
   * 获取附近的事件
   * @param {Object} location - 位置信息
   * @param {number} location.latitude - 纬度
   * @param {number} location.longitude - 经度
   * @param {number} radius - 搜索半径(km)
   * @param {Object} params - 其他查询参数
   * @returns {Promise<Object>} 附近事件列表
   */
  async getNearbyEvents(location, radius = 5, params = {}) {
    try {
      const queryParams = {
        latitude: location.latitude,
        longitude: location.longitude,
        radius,
        ...params
      };

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/nearby?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取附近事件失败');
    }
  }

  /**
   * 批量操作事件
   * @param {Array} eventIds - 事件ID列表
   * @param {string} action - 操作类型 (delete|update_status|assign)
   * @param {Object} data - 操作数据
   * @returns {Promise<Object>} 批量操作结果
   */
  async batchOperation(eventIds, action, data = {}) {
    try {
      const response = await this.post('/batch', {
        event_ids: eventIds,
        action,
        data
      });

      if (response.success) {
        // 触发批量操作事件
        this.dispatchEventEvent('batch-operation', { 
          eventIds, 
          action, 
          data,
          result: response.data 
        });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '批量操作失败');
    }
  }

  /**
   * 触发事件相关的自定义事件
   * @param {string} eventType - 事件类型
   * @param {Object} data - 事件数据
   */
  dispatchEventEvent(eventType, data = {}) {
    const event = new CustomEvent(`event:${eventType}`, {
      detail: data
    });
    window.dispatchEvent(event);
  }

  /**
   * 格式化事件数据用于显示
   * @param {Object} event - 事件对象
   * @returns {Object} 格式化后的事件数据
   */
  static formatEventForDisplay(event) {
    return {
      ...event,
      statusText: EventService.getStatusText(event.status),
      priorityText: EventService.getPriorityText(event.priority),
      createdAtFormatted: EventService.formatDate(event.created_at),
      updatedAtFormatted: EventService.formatDate(event.updated_at)
    };
  }

  /**
   * 获取状态文本
   * @param {string} status - 状态值
   * @returns {string} 状态文本
   */
  static getStatusText(status) {
    const statusMap = {
      pending: '待处理',
      in_progress: '处理中',
      resolved: '已解决',
      closed: '已关闭'
    };
    return statusMap[status] || status;
  }

  /**
   * 获取优先级文本
   * @param {string} priority - 优先级值
   * @returns {string} 优先级文本
   */
  static getPriorityText(priority) {
    const priorityMap = {
      low: '低',
      medium: '中',
      high: '高',
      urgent: '紧急'
    };
    return priorityMap[priority] || priority;
  }

  /**
   * 格式化日期
   * @param {string} dateString - 日期字符串
   * @returns {string} 格式化后的日期
   */
  static formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // 小于1分钟
    if (diff < 60000) {
      return '刚刚';
    }
    
    // 小于1小时
    if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前`;
    }
    
    // 小于1天
    if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)}小时前`;
    }
    
    // 小于7天
    if (diff < 604800000) {
      return `${Math.floor(diff / 86400000)}天前`;
    }
    
    // 超过7天显示具体日期
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}