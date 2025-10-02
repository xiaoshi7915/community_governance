/**
 * 事件跟踪页面组件
 * 实现事件列表展示、筛选、详情查看和实时更新功能
 */
import { Navigation } from '../components/Navigation.js';
import { Modal } from '../components/Modal.js';
import { Notification } from '../components/Notification.js';
import { EventService } from '../services/EventService.js';
import EventStore from '../stores/EventStore.js';
import UserStore from '../stores/UserStore.js';

export class TrackingPage {
  constructor() {
    this.container = null;
    this.navigation = null;
    this.currentDetailModal = null;
    this.refreshTimer = null;
    this.isRefreshing = false;
    this.isLoadingMore = false;
    this.isInitialized = false;

    // 服务实例
    this.eventService = new EventService();

    // 状态管理
    this.eventStore = EventStore;
    this.userStore = UserStore;

    // 下拉刷新相关
    this.pullToRefresh = {
      startY: 0,
      currentY: 0,
      isDragging: false,
      threshold: 80,
      maxDistance: 120
    };

    // 延迟初始化，等待DOM渲染
    this.bindStoreEvents();
  }

  /**
   * 初始化组件
   */
  async init() {
    this.bindStoreEvents();
    await this.loadInitialData();
  }

  /**
   * 绑定状态管理事件
   */
  bindStoreEvents() {
    // 监听事件状态变化
    this.eventStore.subscribe((state) => {
      this.handleEventStateChange(state);
    });

    // 监听用户状态变化
    this.userStore.subscribe((state) => {
      if (!state.isAuthenticated) {
        this.handleUnauthenticated();
      }
    });

    // 监听事件实时更新
    window.addEventListener('event:updated', (e) => {
      this.handleEventUpdate(e.detail);
    });

    window.addEventListener('event:status-updated', (e) => {
      this.handleEventStatusUpdate(e.detail);
    });
  }

  /**
   * 加载初始数据
   */
  async loadInitialData() {
    try {
      // 检查缓存是否有效
      if (!this.eventStore.isCacheValid()) {
        await this.loadEvents();
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
      this.eventStore.setError('加载数据失败，请刷新重试');
    }
  }

  /**
   * 加载事件列表
   */
  async loadEvents(append = false) {
    try {
      const state = this.eventStore.getState();

      if (!append) {
        this.eventStore.setLoading(true);
      } else {
        this.eventStore.setLoading(true, 'loadingMore');
      }

      const params = {
        page: append ? state.pagination.page : 1,
        page_size: state.pagination.pageSize,
        sort_by: state.sortBy,
        sort_order: state.sortOrder,
        ...this.buildFilterParams(state.filters)
      };

      const response = await this.eventService.getEvents(params);

      if (response.success) {
        this.eventStore.setEvents(
          response.data.events,
          response.data.total_count,
          append
        );

        // 更新分页信息
        this.eventStore.updatePagination({
          hasMore: response.data.events.length === state.pagination.pageSize
        });
      } else {
        throw new Error(response.message || '获取事件列表失败');
      }
    } catch (error) {
      console.error('Load events failed:', error);
      this.eventStore.setError(error.message);
      Notification.show(error.message, 'error');
    }
  }

  /**
   * 构建筛选参数
   */
  buildFilterParams(filters) {
    const params = {};

    if (filters.status !== 'all') {
      params.status = filters.status;
    }

    if (filters.type !== 'all') {
      params.event_type = filters.type;
    }

    if (filters.priority !== 'all') {
      params.priority = filters.priority;
    }

    if (filters.keyword) {
      params.search = filters.keyword;
    }

    if (filters.dateRange) {
      params.start_date = filters.dateRange.start.toISOString();
      params.end_date = filters.dateRange.end.toISOString();
    }

    return params;
  }

  /**
   * 渲染页面
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'tracking-page min-h-screen bg-gray-50';

    this.container.innerHTML = this.getTemplate();

    // 渲染子组件
    this.renderComponents();

    // 绑定页面事件
    this.bindPageEvents();

    // 添加页面加载动画
    this.animatePageLoad();

    // 渲染初始内容
    this.renderEventList();
    this.renderFilterTabs();

    // DOM渲染完成后初始化数据
    if (!this.isInitialized) {
      this.isInitialized = true;
      // 使用setTimeout确保DOM完全渲染
      setTimeout(() => {
        this.init();
      }, 0);
    }

    return this.container;
  }

  /**
   * 获取页面模板
   */
  getTemplate() {
    return `
      <!-- 页面头部 -->
      <header class="page-header bg-white shadow-sm sticky top-0 z-40">
        <div class="px-4 py-3">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                </svg>
              </div>
              <div>
                <h1 class="text-lg font-semibold text-gray-900">事件跟踪</h1>
                <p class="text-sm text-gray-500">查看和管理事件状态</p>
              </div>
            </div>
            
            <!-- 搜索和排序按钮 -->
            <div class="flex items-center space-x-2">
              <button id="search-btn" class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </button>
              <button id="sort-btn" class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"></path>
                </svg>
              </button>
            </div>
          </div>
          
          <!-- 筛选标签 -->
          <div id="filter-tabs" class="filter-tabs">
            <!-- 筛选标签将在这里渲染 -->
          </div>
        </div>
        
        <!-- 下拉刷新指示器 -->
        <div id="pull-refresh-indicator" class="pull-refresh-indicator hidden">
          <div class="flex items-center justify-center py-2">
            <svg class="animate-spin h-5 w-5 text-blue-600 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="text-sm text-blue-600">正在刷新...</span>
          </div>
        </div>
      </header>

      <!-- 搜索栏 (隐藏状态) -->
      <div id="search-bar" class="search-bar bg-white border-b hidden">
        <div class="px-4 py-3">
          <div class="relative">
            <input 
              type="text" 
              id="search-input"
              placeholder="搜索事件标题、描述或位置..."
              class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
            <svg class="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <main class="page-content pb-20">
        <!-- 事件统计卡片 -->
        <section id="stats-section" class="stats-section px-4 py-4">
          <div class="grid grid-cols-4 gap-3">
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-lg font-semibold text-gray-900" id="total-count">-</div>
              <div class="text-xs text-gray-500">总计</div>
            </div>
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-lg font-semibold text-yellow-600" id="pending-count">-</div>
              <div class="text-xs text-gray-500">待处理</div>
            </div>
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-lg font-semibold text-blue-600" id="processing-count">-</div>
              <div class="text-xs text-gray-500">处理中</div>
            </div>
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-lg font-semibold text-green-600" id="resolved-count">-</div>
              <div class="text-xs text-gray-500">已解决</div>
            </div>
          </div>
        </section>

        <!-- 事件列表 -->
        <section class="event-list-section px-4">
          <!-- 加载状态 -->
          <div id="loading-state" class="loading-state hidden">
            <div class="flex items-center justify-center py-12">
              <div class="text-center">
                <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-gray-600">加载中...</p>
              </div>
            </div>
          </div>

          <!-- 错误状态 -->
          <div id="error-state" class="error-state hidden">
            <div class="text-center py-12">
              <div class="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                <svg class="h-8 w-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">加载失败</h3>
              <p class="text-gray-600 mb-4" id="error-message">网络连接异常，请检查网络后重试</p>
              <button id="retry-btn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                重试
              </button>
            </div>
          </div>

          <!-- 空状态 -->
          <div id="empty-state" class="empty-state hidden">
            <div class="text-center py-12">
              <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg class="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">暂无事件</h3>
              <p class="text-gray-600 mb-4">还没有符合条件的事件记录</p>
              <button id="create-event-btn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                创建事件
              </button>
            </div>
          </div>

          <!-- 事件列表容器 -->
          <div id="event-list" class="event-list space-y-3">
            <!-- 事件卡片将在这里渲染 -->
          </div>

          <!-- 加载更多 -->
          <div id="load-more-section" class="load-more-section text-center py-6 hidden">
            <button id="load-more-btn" class="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
              加载更多
            </button>
            <div id="loading-more" class="loading-more hidden">
              <svg class="animate-spin h-5 w-5 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-sm text-gray-600 mt-2">加载中...</p>
            </div>
          </div>
        </section>
      </main>

      <!-- 底部导航容器 -->
      <div id="navigation-container" class="navigation-container">
        <!-- Navigation 组件将在这里渲染 -->
      </div>
    `;
  }

  /**
   * 渲染子组件
   */
  renderComponents() {
    // 渲染导航组件
    this.navigation = new Navigation({
      activeTab: 'tracking',
      onNavigate: (path, tabId) => this.handleNavigation(path, tabId)
    });

    const navContainer = this.container.querySelector('#navigation-container');
    this.navigation.mount(navContainer);
  }

  /**
   * 绑定页面事件
   */
  bindPageEvents() {
    // 搜索相关事件
    const searchBtn = this.container.querySelector('#search-btn');
    const searchInput = this.container.querySelector('#search-input');
    const searchBar = this.container.querySelector('#search-bar');

    searchBtn.addEventListener('click', () => {
      this.toggleSearchBar();
    });

    searchInput.addEventListener('input', (e) => {
      this.handleSearchInput(e.target.value);
    });

    // 排序按钮事件
    const sortBtn = this.container.querySelector('#sort-btn');
    sortBtn.addEventListener('click', () => {
      this.showSortOptions();
    });

    // 重试按钮事件
    const retryBtn = this.container.querySelector('#retry-btn');
    retryBtn.addEventListener('click', () => {
      this.loadEvents();
    });

    // 创建事件按钮事件
    const createEventBtn = this.container.querySelector('#create-event-btn');
    createEventBtn.addEventListener('click', () => {
      this.handleNavigation('/', 'home');
    });

    // 加载更多按钮事件
    const loadMoreBtn = this.container.querySelector('#load-more-btn');
    loadMoreBtn.addEventListener('click', () => {
      this.loadMoreEvents();
    });

    // 下拉刷新事件
    this.bindPullToRefreshEvents();
  }

  /**
   * 绑定下拉刷新事件
   */
  bindPullToRefreshEvents() {
    const header = this.container.querySelector('.page-header');

    // 触摸开始
    header.addEventListener('touchstart', (e) => {
      if (window.scrollY === 0) {
        this.pullToRefresh.startY = e.touches[0].clientY;
        this.pullToRefresh.isDragging = true;
      }
    }, { passive: true });

    // 触摸移动
    header.addEventListener('touchmove', (e) => {
      if (!this.pullToRefresh.isDragging || window.scrollY > 0) return;

      this.pullToRefresh.currentY = e.touches[0].clientY;
      const distance = this.pullToRefresh.currentY - this.pullToRefresh.startY;

      if (distance > 0) {
        e.preventDefault();
        this.updatePullToRefreshIndicator(distance);
      }
    }, { passive: false });

    // 触摸结束
    header.addEventListener('touchend', () => {
      if (!this.pullToRefresh.isDragging) return;

      const distance = this.pullToRefresh.currentY - this.pullToRefresh.startY;

      if (distance > this.pullToRefresh.threshold) {
        this.triggerRefresh();
      } else {
        this.resetPullToRefresh();
      }

      this.pullToRefresh.isDragging = false;
    }, { passive: true });
  }

  /**
   * 更新下拉刷新指示器
   */
  updatePullToRefreshIndicator(distance) {
    const indicator = this.container.querySelector('#pull-refresh-indicator');
    const progress = Math.min(distance / this.pullToRefresh.threshold, 1);

    if (distance > 20) {
      indicator.classList.remove('hidden');
      indicator.style.transform = `translateY(${Math.min(distance - 20, this.pullToRefresh.maxDistance)}px)`;
      indicator.style.opacity = progress;
    }
  }

  /**
   * 触发刷新
   */
  async triggerRefresh() {
    if (this.isRefreshing) return;

    this.isRefreshing = true;
    const indicator = this.container.querySelector('#pull-refresh-indicator');

    indicator.classList.remove('hidden');
    indicator.style.transform = 'translateY(0)';
    indicator.style.opacity = '1';

    try {
      await this.refreshEvents();
    } finally {
      setTimeout(() => {
        this.resetPullToRefresh();
        this.isRefreshing = false;
      }, 500);
    }
  }

  /**
   * 重置下拉刷新
   */
  resetPullToRefresh() {
    const indicator = this.container.querySelector('#pull-refresh-indicator');
    indicator.style.transform = 'translateY(-100%)';
    indicator.style.opacity = '0';

    setTimeout(() => {
      indicator.classList.add('hidden');
    }, 300);
  }

  /**
   * 页面加载动画
   */
  animatePageLoad() {
    this.container.classList.add('animate-fade-in');

    // 依次显示各个区域
    const sections = this.container.querySelectorAll('section');
    sections.forEach((section, index) => {
      setTimeout(() => {
        section.classList.add('animate-slide-up');
      }, index * 100);
    });
  }

  /**
   * 处理导航
   */
  handleNavigation(path, tabId) {
    // 使用路由系统进行导航
    if (window.router) {
      window.router.navigate(path);
    } else {
      // 降级处理：触发自定义导航事件
      const navigationEvent = new CustomEvent('navigate', {
        detail: { path, tabId }
      });
      document.dispatchEvent(navigationEvent);
    }
  }

  /**
   * 处理事件状态变化
   */
  handleEventStateChange(state) {
    // 更新加载状态
    this.updateLoadingState(state);

    // 更新事件列表
    this.renderEventList();

    // 更新统计信息
    this.updateStats();

    // 更新加载更多按钮
    this.updateLoadMoreButton(state);
  }

  /**
   * 更新加载状态
   */
  updateLoadingState(state) {
    // 检查容器是否存在
    if (!this.container) {
      console.warn('TrackingPage container not found, skipping state update');
      return;
    }

    const loadingState = this.container.querySelector('#loading-state');
    const errorState = this.container.querySelector('#error-state');
    const emptyState = this.container.querySelector('#empty-state');
    const eventList = this.container.querySelector('#event-list');

    // 检查必要的DOM元素是否存在
    if (!loadingState || !errorState || !emptyState || !eventList) {
      console.warn('TrackingPage DOM elements not found, skipping state update');
      return;
    }

    // 隐藏所有状态
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    emptyState.classList.add('hidden');

    if (state.loading && state.events.length === 0) {
      // 首次加载中
      loadingState.classList.remove('hidden');
      eventList.classList.add('hidden');
    } else if (state.error) {
      // 错误状态
      const errorMessage = this.container.querySelector('#error-message');
      errorMessage.textContent = state.error;
      errorState.classList.remove('hidden');
      eventList.classList.add('hidden');
    } else if (state.events.length === 0) {
      // 空状态
      emptyState.classList.remove('hidden');
      eventList.classList.add('hidden');
    } else {
      // 有数据状态
      eventList.classList.remove('hidden');
    }
  }

  /**
   * 渲染事件列表
   */
  renderEventList() {
    // 检查容器是否存在
    if (!this.container) {
      console.warn('TrackingPage container not found, skipping event list render');
      return;
    }

    const eventList = this.container.querySelector('#event-list');
    if (!eventList) {
      console.warn('Event list element not found, skipping render');
      return;
    }

    const state = this.eventStore.getState();

    if (state.events.length === 0) return;

    eventList.innerHTML = state.events.map(event => this.createEventCard(event)).join('');

    // 绑定事件卡片点击事件
    this.bindEventCardEvents();
  }

  /**
   * 创建事件卡片
   */
  createEventCard(event) {
    const formattedEvent = EventService.formatEventForDisplay(event);

    return `
      <div class="event-card bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer" data-event-id="${event.id}">
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <h3 class="text-base font-medium text-gray-900 mb-1 line-clamp-2">${event.title}</h3>
            <p class="text-sm text-gray-600 line-clamp-2">${event.description || '暂无描述'}</p>
          </div>
          
          <!-- 状态标签 -->
          <span class="status-badge ${this.getStatusBadgeClass(event.status)} ml-3 flex-shrink-0">
            ${formattedEvent.statusText}
          </span>
        </div>

        <div class="flex items-center justify-between text-sm text-gray-500">
          <div class="flex items-center space-x-4">
            <!-- 优先级 -->
            <div class="flex items-center space-x-1">
              <div class="w-2 h-2 rounded-full ${this.getPriorityColor(event.priority)}"></div>
              <span>${formattedEvent.priorityText}</span>
            </div>
            
            <!-- 位置 -->
            ${event.location ? `
              <div class="flex items-center space-x-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                </svg>
                <span class="truncate max-w-24">${typeof event.location === 'string' ? event.location : event.location.address || '未知位置'}</span>
              </div>
            ` : ''}
          </div>
          
          <!-- 时间 -->
          <span class="text-xs">${formattedEvent.createdAtFormatted}</span>
        </div>

        <!-- 媒体预览 -->
        ${event.media_urls && event.media_urls.length > 0 ? `
          <div class="mt-3 flex space-x-2">
            ${event.media_urls.slice(0, 3).map(url => `
              <div class="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden">
                <img src="${url}" alt="事件图片" class="w-full h-full object-cover">
              </div>
            `).join('')}
            ${event.media_urls.length > 3 ? `
              <div class="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <span class="text-xs text-gray-500">+${event.media_urls.length - 3}</span>
              </div>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * 获取状态标签样式类
   */
  getStatusBadgeClass(status) {
    const statusClasses = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      resolved: 'bg-green-100 text-green-800',
      closed: 'bg-gray-100 text-gray-800'
    };
    return `px-2 py-1 text-xs font-medium rounded-full ${statusClasses[status] || statusClasses.pending}`;
  }

  /**
   * 获取优先级颜色
   */
  getPriorityColor(priority) {
    const priorityColors = {
      low: 'bg-green-500',
      medium: 'bg-yellow-500',
      high: 'bg-orange-500',
      urgent: 'bg-red-500'
    };
    return priorityColors[priority] || priorityColors.medium;
  }

  /**
   * 绑定事件卡片事件
   */
  bindEventCardEvents() {
    const eventCards = this.container.querySelectorAll('.event-card');

    eventCards.forEach(card => {
      card.addEventListener('click', () => {
        const eventId = card.dataset.eventId;
        this.showEventDetail(eventId);
      });
    });
  }

  /**
   * 显示事件详情
   */
  async showEventDetail(eventId) {
    try {
      // 从状态中获取事件数据
      const state = this.eventStore.getState();
      const event = state.events.find(e => e.id === eventId);

      if (!event) {
        throw new Error('事件不存在');
      }

      // 设置当前事件
      this.eventStore.setCurrentEvent(event);

      // 加载事件详情和时间线
      const [detailResponse, timelineResponse] = await Promise.all([
        this.eventService.getEventDetail(eventId),
        this.eventService.getEventTimeline(eventId)
      ]);

      if (detailResponse.success) {
        this.eventStore.setCurrentEvent(detailResponse.data);
      }

      if (timelineResponse.success) {
        this.eventStore.setEventTimeline(timelineResponse.data);
      }

      // 显示详情模态框
      this.showDetailModal();

    } catch (error) {
      console.error('Show event detail failed:', error);
      Notification.show(error.message || '获取事件详情失败', 'error');
    }
  }

  /**
   * 显示详情模态框
   */
  showDetailModal() {
    const state = this.eventStore.getState();
    const event = state.currentEvent;
    const timeline = state.currentEventTimeline;

    if (!event) return;

    // 创建详情内容
    const detailContent = this.createEventDetailContent(event, timeline);

    // 创建模态框
    this.currentDetailModal = new Modal({
      title: '事件详情',
      content: detailContent,
      className: 'max-w-lg',
      actions: [
        {
          key: 'close',
          label: '关闭',
          className: 'btn-secondary',
          handler: (modal) => modal.hide()
        }
      ],
      onClose: () => {
        this.currentDetailModal = null;
      }
    });

    this.currentDetailModal.show();
  }

  /**
   * 创建事件详情内容
   */
  createEventDetailContent(event, timeline) {
    const formattedEvent = EventService.formatEventForDisplay(event);

    const detailElement = document.createElement('div');
    detailElement.className = 'event-detail-content';

    detailElement.innerHTML = `
      <!-- 基本信息 -->
      <div class="mb-6">
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1">
            <h2 class="text-lg font-semibold text-gray-900 mb-2">${event.title}</h2>
            <div class="flex items-center space-x-3 mb-3">
              <span class="status-badge ${this.getStatusBadgeClass(event.status)}">
                ${formattedEvent.statusText}
              </span>
              <div class="flex items-center space-x-1">
                <div class="w-2 h-2 rounded-full ${this.getPriorityColor(event.priority)}"></div>
                <span class="text-sm text-gray-600">${formattedEvent.priorityText}优先级</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 描述 -->
        <div class="mb-4">
          <h3 class="text-sm font-medium text-gray-700 mb-2">详细描述</h3>
          <p class="text-gray-600 text-sm leading-relaxed">${event.description || '暂无描述'}</p>
        </div>

        <!-- 位置信息 -->
        ${event.location ? `
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 mb-2">位置信息</h3>
            <div class="flex items-start space-x-2">
              <svg class="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
              </svg>
              <span class="text-sm text-gray-600">${typeof event.location === 'string' ? event.location : event.location.address || '未知位置'}</span>
            </div>
          </div>
        ` : ''}

        <!-- 媒体文件 -->
        ${event.media_urls && event.media_urls.length > 0 ? `
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 mb-2">相关媒体</h3>
            <div class="grid grid-cols-2 gap-2">
              ${event.media_urls.map(url => `
                <div class="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                  <img src="${url}" alt="事件图片" class="w-full h-full object-cover cursor-pointer" onclick="this.requestFullscreen()">
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <!-- 时间信息 -->
        <div class="mb-4">
          <h3 class="text-sm font-medium text-gray-700 mb-2">时间信息</h3>
          <div class="space-y-1 text-sm text-gray-600">
            <div>创建时间：${formattedEvent.createdAtFormatted}</div>
            <div>更新时间：${formattedEvent.updatedAtFormatted}</div>
          </div>
        </div>
      </div>

      <!-- 时间线 -->
      ${timeline && timeline.length > 0 ? `
        <div class="border-t pt-4">
          <h3 class="text-sm font-medium text-gray-700 mb-3">处理时间线</h3>
          <div class="space-y-3">
            ${timeline.map(item => `
              <div class="flex items-start space-x-3">
                <div class="w-2 h-2 rounded-full bg-blue-500 mt-2 flex-shrink-0"></div>
                <div class="flex-1">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-900">${item.action_type}</span>
                    <span class="text-xs text-gray-500">${EventService.formatDate(item.created_at)}</span>
                  </div>
                  ${item.comment ? `<p class="text-sm text-gray-600 mt-1">${item.comment}</p>` : ''}
                  ${item.operator ? `<p class="text-xs text-gray-500 mt-1">操作人：${item.operator}</p>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}
    `;

    return detailElement;
  }

  /**
   * 渲染筛选标签
   */
  renderFilterTabs() {
    const filterTabs = this.container.querySelector('#filter-tabs');
    const state = this.eventStore.getState();

    const tabs = [
      { key: 'all', label: '全部', count: null },
      { key: 'pending', label: '待处理', count: null },
      { key: 'in_progress', label: '处理中', count: null },
      { key: 'resolved', label: '已解决', count: null },
      { key: 'closed', label: '已关闭', count: null }
    ];

    filterTabs.innerHTML = `
      <div class="flex space-x-1 overflow-x-auto pb-1">
        ${tabs.map(tab => `
          <button 
            class="filter-tab px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${state.filters.status === tab.key
        ? 'bg-blue-600 text-white'
        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }"
            data-status="${tab.key}"
          >
            ${tab.label}
            ${tab.count !== null ? `<span class="ml-1 text-xs">(${tab.count})</span>` : ''}
          </button>
        `).join('')}
      </div>
    `;

    // 绑定筛选标签事件
    this.bindFilterTabEvents();
  }

  /**
   * 绑定筛选标签事件
   */
  bindFilterTabEvents() {
    const filterTabs = this.container.querySelectorAll('.filter-tab');

    filterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const status = tab.dataset.status;
        this.handleFilterChange({ status });
      });
    });
  }

  /**
   * 处理筛选变化
   */
  handleFilterChange(filters) {
    this.eventStore.updateFilters(filters);
    this.loadEvents();
    this.renderFilterTabs();
  }

  /**
   * 更新统计信息
   */
  updateStats() {
    const stats = this.eventStore.getEventStats();

    this.container.querySelector('#total-count').textContent = stats.total;
    this.container.querySelector('#pending-count').textContent = stats.pending || 0;
    this.container.querySelector('#processing-count').textContent = stats.processing || 0;
    this.container.querySelector('#resolved-count').textContent = stats.resolved || 0;
  }

  /**
   * 更新加载更多按钮
   */
  updateLoadMoreButton(state) {
    const loadMoreSection = this.container.querySelector('#load-more-section');
    const loadMoreBtn = this.container.querySelector('#load-more-btn');
    const loadingMore = this.container.querySelector('#loading-more');

    if (state.pagination.hasMore && state.events.length > 0) {
      loadMoreSection.classList.remove('hidden');

      if (state.loadingMore) {
        loadMoreBtn.classList.add('hidden');
        loadingMore.classList.remove('hidden');
      } else {
        loadMoreBtn.classList.remove('hidden');
        loadingMore.classList.add('hidden');
      }
    } else {
      loadMoreSection.classList.add('hidden');
    }
  }

  /**
   * 切换搜索栏
   */
  toggleSearchBar() {
    const searchBar = this.container.querySelector('#search-bar');
    const searchInput = this.container.querySelector('#search-input');

    if (searchBar.classList.contains('hidden')) {
      searchBar.classList.remove('hidden');
      searchBar.classList.add('animate-slide-down');
      setTimeout(() => searchInput.focus(), 300);
    } else {
      searchBar.classList.add('hidden');
      searchBar.classList.remove('animate-slide-down');
      searchInput.value = '';
      this.handleSearchInput('');
    }
  }

  /**
   * 处理搜索输入
   */
  handleSearchInput(keyword) {
    // 防抖处理
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.handleFilterChange({ keyword });
    }, 500);
  }

  /**
   * 显示排序选项
   */
  showSortOptions() {
    const state = this.eventStore.getState();

    const sortModal = new Modal({
      title: '排序方式',
      content: `
        <div class="space-y-3">
          <label class="flex items-center space-x-3 cursor-pointer">
            <input type="radio" name="sort" value="created_at_desc" ${state.sortBy === 'created_at' && state.sortOrder === 'desc' ? 'checked' : ''}>
            <span>按创建时间（最新优先）</span>
          </label>
          <label class="flex items-center space-x-3 cursor-pointer">
            <input type="radio" name="sort" value="created_at_asc" ${state.sortBy === 'created_at' && state.sortOrder === 'asc' ? 'checked' : ''}>
            <span>按创建时间（最早优先）</span>
          </label>
          <label class="flex items-center space-x-3 cursor-pointer">
            <input type="radio" name="sort" value="updated_at_desc" ${state.sortBy === 'updated_at' && state.sortOrder === 'desc' ? 'checked' : ''}>
            <span>按更新时间（最新优先）</span>
          </label>
          <label class="flex items-center space-x-3 cursor-pointer">
            <input type="radio" name="sort" value="priority_desc" ${state.sortBy === 'priority' && state.sortOrder === 'desc' ? 'checked' : ''}>
            <span>按优先级（高到低）</span>
          </label>
        </div>
      `,
      actions: [
        {
          key: 'cancel',
          label: '取消',
          className: 'btn-secondary',
          handler: (modal) => modal.hide()
        },
        {
          key: 'apply',
          label: '应用',
          className: 'btn-primary',
          handler: (modal) => {
            const selectedSort = modal.container.querySelector('input[name="sort"]:checked');
            if (selectedSort) {
              const [sortBy, sortOrder] = selectedSort.value.split('_');
              this.eventStore.setSorting(sortBy, sortOrder);
              this.loadEvents();
            }
            modal.hide();
          }
        }
      ]
    });

    sortModal.show();
  }

  /**
   * 刷新事件列表
   */
  async refreshEvents() {
    this.eventStore.setLoading(true, 'refreshing');
    await this.loadEvents();
  }

  /**
   * 加载更多事件
   */
  async loadMoreEvents() {
    if (this.isLoadingMore) return;

    this.isLoadingMore = true;
    this.eventStore.nextPage();
    await this.loadEvents(true);
    this.isLoadingMore = false;
  }

  /**
   * 处理事件更新
   */
  handleEventUpdate(detail) {
    this.eventStore.updateEvent(detail.eventId, detail.event);
    Notification.show('事件已更新', 'success');
  }

  /**
   * 处理事件状态更新
   */
  handleEventStatusUpdate(detail) {
    this.eventStore.updateEvent(detail.eventId, {
      status: detail.status,
      updated_at: new Date().toISOString()
    });
    Notification.show(`事件状态已更新为${EventService.getStatusText(detail.status)}`, 'success');
  }

  /**
   * 处理未认证状态
   */
  handleUnauthenticated() {
    // 跳转到登录页面或显示登录提示
    Notification.show('请先登录', 'warning');
  }

  /**
   * 挂载到DOM
   */
  mount(parent = document.body) {
    if (!this.container) {
      this.render();
    }
    parent.appendChild(this.container);
    return this;
  }

  /**
   * 从DOM卸载
   */
  unmount() {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }

    // 清理定时器
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }

    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }

    return this;
  }

  /**
   * 销毁组件
   */
  destroy() {
    this.unmount();

    // 销毁子组件
    if (this.navigation) {
      this.navigation.destroy();
    }

    if (this.currentDetailModal) {
      this.currentDetailModal.destroy();
    }

    // 清理引用
    this.container = null;
    this.navigation = null;
    this.currentDetailModal = null;
  }
}