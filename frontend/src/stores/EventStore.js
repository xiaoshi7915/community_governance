import Store from './Store.js';
import { createStorageMiddleware, restoreFromStorage } from './StorageMiddleware.js';

/**
 * 事件数据状态管理
 * 管理事件列表、详情、筛选条件和分页状态
 */
class EventStore extends Store {
  constructor() {
    // 从本地存储恢复部分状态
    const persistedState = restoreFromStorage('eventStore', {
      whitelist: ['filters', 'sortBy', 'sortOrder']
    });

    const initialState = {
      // 事件列表数据
      events: [],
      totalCount: 0,
      
      // 当前选中的事件
      currentEvent: null,
      currentEventTimeline: [],
      
      // 筛选条件
      filters: {
        status: 'all', // all, pending, processing, resolved, closed
        type: 'all',
        priority: 'all', // all, low, medium, high, urgent
        dateRange: null, // { start: Date, end: Date }
        keyword: ''
      },
      
      // 排序设置
      sortBy: 'created_at', // created_at, updated_at, priority
      sortOrder: 'desc', // asc, desc
      
      // 分页信息
      pagination: {
        page: 1,
        pageSize: 20,
        hasMore: true
      },
      
      // 加载状态
      loading: false,
      refreshing: false,
      loadingMore: false,
      
      // 错误状态
      error: null,
      
      // 缓存设置
      cache: {
        lastFetch: null,
        maxAge: 5 * 60 * 1000 // 5分钟缓存
      },
      
      // 实时更新设置
      realTimeEnabled: true,
      lastUpdateCheck: null,
      
      ...persistedState
    };

    super(initialState);

    // 添加持久化中间件（只持久化筛选和排序设置）
    this.addMiddleware(createStorageMiddleware('eventStore', {
      whitelist: ['filters', 'sortBy', 'sortOrder']
    }));
  }

  /**
   * 设置事件列表
   * @param {Array} events - 事件列表
   * @param {number} totalCount - 总数量
   * @param {boolean} append - 是否追加到现有列表
   */
  setEvents(events, totalCount = null, append = false) {
    this.setState(prevState => ({
      events: append ? [...prevState.events, ...events] : events,
      totalCount: totalCount !== null ? totalCount : prevState.totalCount,
      loading: false,
      refreshing: false,
      loadingMore: false,
      error: null,
      cache: {
        ...prevState.cache,
        lastFetch: Date.now()
      }
    }));
  }

  /**
   * 添加新事件到列表开头
   * @param {Object} event - 新事件
   */
  addEvent(event) {
    this.setState(prevState => ({
      events: [event, ...prevState.events],
      totalCount: prevState.totalCount + 1
    }));
  }

  /**
   * 更新事件信息
   * @param {string} eventId - 事件ID
   * @param {Object} updates - 更新内容
   */
  updateEvent(eventId, updates) {
    this.setState(prevState => ({
      events: prevState.events.map(event =>
        event.id === eventId ? { ...event, ...updates } : event
      ),
      currentEvent: prevState.currentEvent && prevState.currentEvent.id === eventId
        ? { ...prevState.currentEvent, ...updates }
        : prevState.currentEvent
    }));
  }

  /**
   * 删除事件
   * @param {string} eventId - 事件ID
   */
  removeEvent(eventId) {
    this.setState(prevState => ({
      events: prevState.events.filter(event => event.id !== eventId),
      totalCount: Math.max(0, prevState.totalCount - 1),
      currentEvent: prevState.currentEvent && prevState.currentEvent.id === eventId
        ? null
        : prevState.currentEvent
    }));
  }

  /**
   * 设置当前选中的事件
   * @param {Object} event - 事件对象
   */
  setCurrentEvent(event) {
    this.setState({
      currentEvent: event,
      currentEventTimeline: [] // 清空时间线，需要重新加载
    });
  }

  /**
   * 设置事件时间线
   * @param {Array} timeline - 时间线数据
   */
  setEventTimeline(timeline) {
    this.setState({
      currentEventTimeline: timeline
    });
  }

  /**
   * 更新筛选条件
   * @param {Object} filters - 筛选条件
   */
  updateFilters(filters) {
    this.setState(prevState => ({
      filters: {
        ...prevState.filters,
        ...filters
      },
      pagination: {
        ...prevState.pagination,
        page: 1 // 重置分页
      }
    }));
  }

  /**
   * 重置筛选条件
   */
  resetFilters() {
    this.setState({
      filters: {
        status: 'all',
        type: 'all',
        priority: 'all',
        dateRange: null,
        keyword: ''
      },
      pagination: {
        page: 1,
        pageSize: 20,
        hasMore: true
      }
    });
  }

  /**
   * 设置排序方式
   * @param {string} sortBy - 排序字段
   * @param {string} sortOrder - 排序顺序
   */
  setSorting(sortBy, sortOrder = 'desc') {
    this.setState({
      sortBy,
      sortOrder,
      pagination: {
        page: 1,
        pageSize: 20,
        hasMore: true
      }
    });
  }

  /**
   * 更新分页信息
   * @param {Object} pagination - 分页信息
   */
  updatePagination(pagination) {
    this.setState(prevState => ({
      pagination: {
        ...prevState.pagination,
        ...pagination
      }
    }));
  }

  /**
   * 下一页
   */
  nextPage() {
    this.setState(prevState => ({
      pagination: {
        ...prevState.pagination,
        page: prevState.pagination.page + 1
      }
    }));
  }

  /**
   * 设置加载状态
   * @param {boolean} loading - 是否加载中
   * @param {string} type - 加载类型：loading, refreshing, loadingMore
   */
  setLoading(loading, type = 'loading') {
    this.setState({
      [type]: loading,
      error: loading ? null : this.getState().error
    });
  }

  /**
   * 设置错误状态
   * @param {string|null} error - 错误信息
   */
  setError(error) {
    this.setState({
      error,
      loading: false,
      refreshing: false,
      loadingMore: false
    });
  }

  /**
   * 检查缓存是否有效
   * @returns {boolean} 缓存是否有效
   */
  isCacheValid() {
    const { cache } = this.getState();
    if (!cache.lastFetch) return false;
    
    return Date.now() - cache.lastFetch < cache.maxAge;
  }

  /**
   * 获取筛选后的事件数量
   * @returns {number} 筛选后的事件数量
   */
  getFilteredCount() {
    const { filters, events } = this.getState();
    
    if (this.isDefaultFilters(filters)) {
      return events.length;
    }
    
    return this.filterEvents(events, filters).length;
  }

  /**
   * 检查是否为默认筛选条件
   * @param {Object} filters - 筛选条件
   * @returns {boolean} 是否为默认筛选条件
   */
  isDefaultFilters(filters) {
    return filters.status === 'all' &&
           filters.type === 'all' &&
           filters.priority === 'all' &&
           !filters.dateRange &&
           !filters.keyword;
  }

  /**
   * 根据筛选条件过滤事件
   * @param {Array} events - 事件列表
   * @param {Object} filters - 筛选条件
   * @returns {Array} 过滤后的事件列表
   */
  filterEvents(events, filters) {
    return events.filter(event => {
      // 状态筛选
      if (filters.status !== 'all' && event.status !== filters.status) {
        return false;
      }
      
      // 类型筛选
      if (filters.type !== 'all' && event.type !== filters.type) {
        return false;
      }
      
      // 优先级筛选
      if (filters.priority !== 'all' && event.priority !== filters.priority) {
        return false;
      }
      
      // 日期范围筛选
      if (filters.dateRange) {
        const eventDate = new Date(event.created_at);
        if (eventDate < filters.dateRange.start || eventDate > filters.dateRange.end) {
          return false;
        }
      }
      
      // 关键词筛选
      if (filters.keyword) {
        const keyword = filters.keyword.toLowerCase();
        const searchText = `${event.title} ${event.description} ${event.location}`.toLowerCase();
        if (!searchText.includes(keyword)) {
          return false;
        }
      }
      
      return true;
    });
  }

  /**
   * 获取事件统计信息
   * @returns {Object} 统计信息
   */
  getEventStats() {
    const { events } = this.getState();
    
    const stats = {
      total: events.length,
      pending: 0,
      processing: 0,
      resolved: 0,
      closed: 0,
      byPriority: {
        low: 0,
        medium: 0,
        high: 0,
        urgent: 0
      }
    };
    
    events.forEach(event => {
      // 按状态统计
      if (stats.hasOwnProperty(event.status)) {
        stats[event.status]++;
      }
      
      // 按优先级统计
      if (stats.byPriority.hasOwnProperty(event.priority)) {
        stats.byPriority[event.priority]++;
      }
    });
    
    return stats;
  }

  /**
   * 清空事件列表
   */
  clearEvents() {
    this.setState({
      events: [],
      totalCount: 0,
      currentEvent: null,
      currentEventTimeline: [],
      pagination: {
        page: 1,
        pageSize: 20,
        hasMore: true
      }
    });
  }

  /**
   * 设置实时更新状态
   * @param {boolean} enabled - 是否启用实时更新
   */
  setRealTimeEnabled(enabled) {
    this.setState({
      realTimeEnabled: enabled,
      lastUpdateCheck: enabled ? Date.now() : null
    });
  }

  /**
   * 更新最后检查时间
   */
  updateLastCheck() {
    this.setState({
      lastUpdateCheck: Date.now()
    });
  }
}

// 创建单例实例
const eventStore = new EventStore();

export default eventStore;