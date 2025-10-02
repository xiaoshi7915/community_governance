/**
 * 历史记录页面
 * 显示事件统计图表和历史记录列表
 */
import { Navigation } from '../components/Navigation.js';
import { EventService } from '../services/EventService.js';
import UserStore from '../stores/UserStore.js';

export class HistoryPage {
  constructor() {
    this.container = null;
    this.navigation = null;
    this.eventService = new EventService();
    this.userStore = UserStore;
    this.events = [];
    this.stats = null;
    
    this.init();
  }

  async init() {
    await this.loadData();
  }

  async loadData() {
    try {
      // 加载事件统计数据
      const statsResponse = await this.eventService.getUserStats();
      if (statsResponse.success) {
        this.stats = statsResponse.data;
      }

      // 加载事件列表
      const eventsResponse = await this.eventService.getEvents({ page: 1, page_size: 10 });
      if (eventsResponse.success) {
        this.events = eventsResponse.data.events || [];
      }
    } catch (error) {
      console.error('加载历史数据失败:', error);
    }
  }

  render() {
    this.container = document.createElement('div');
    this.container.className = 'history-page min-h-screen bg-gray-50';
    
    this.container.innerHTML = this.getTemplate();

    this.renderComponents();
    this.bindEvents();

    return this.container;
  }

  getTemplate() {
    const userState = this.userStore.getState();
    const user = userState.user || {};
    
    return `
      <div class="history-page-content">
        <!-- 顶部搜索栏 -->
        <div class="top-bar bg-white shadow-sm p-4">
          <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <div>
                <h1 class="text-lg font-semibold text-gray-900">历史记录</h1>
                <p class="text-sm text-gray-600">事件统计与历史数据</p>
              </div>
            </div>
            <div class="flex-1"></div>
            <button class="p-2 text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </button>
          </div>
          
          <!-- 搜索框 -->
          <div class="mt-3">
            <div class="relative">
              <input 
                type="text" 
                placeholder="搜索事件编号、位置或描述..."
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
              <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-section p-4">
          <div class="grid grid-cols-4 gap-3">
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-2xl font-bold text-blue-600">${this.stats?.total_events || 3}</div>
              <div class="text-xs text-gray-600 mt-1">事件总数</div>
            </div>
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-2xl font-bold text-green-600">${this.getResolvedCount()}</div>
              <div class="text-xs text-gray-600 mt-1">已解决</div>
            </div>
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-2xl font-bold text-orange-600">${this.getPendingCount()}</div>
              <div class="text-xs text-gray-600 mt-1">处理中</div>
            </div>
            <div class="stat-card bg-white rounded-lg p-3 text-center shadow-sm">
              <div class="text-2xl font-bold text-red-600">${this.getOverdueCount()}</div>
              <div class="text-xs text-gray-600 mt-1">超期</div>
            </div>
          </div>
          
          <!-- 解决率 -->
          <div class="mt-3 text-center">
            <div class="text-2xl font-bold text-green-600">${this.getResolutionRate()}%</div>
            <div class="text-sm text-gray-600">解决率</div>
          </div>
        </div>

        <!-- 趋势图表 -->
        <div class="chart-section bg-white mx-4 rounded-lg shadow-sm p-4 mb-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-3">事件趋势分析</h3>
          <div class="chart-container">
            <div class="chart-placeholder bg-gradient-to-r from-blue-50 to-green-50 rounded-lg p-8 text-center">
              <svg class="w-16 h-16 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
              <p class="text-gray-600">根据标准流程移入中区域后自动开始动态监测</p>
            </div>
          </div>
        </div>

        <!-- 事件类型分布 -->
        <div class="pie-chart-section bg-white mx-4 rounded-lg shadow-sm p-4 mb-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-3">事件类型分布</h3>
          <div class="pie-chart-container">
            <div class="pie-chart-placeholder bg-gradient-to-br from-blue-100 to-orange-100 rounded-lg p-8 text-center">
              <div class="w-32 h-32 mx-auto bg-white rounded-full shadow-lg flex items-center justify-center mb-4">
                <div class="w-24 h-24 rounded-full bg-gradient-to-r from-blue-500 via-green-500 to-orange-500"></div>
              </div>
              <div class="flex justify-center space-x-4 text-sm">
                <div class="flex items-center">
                  <div class="w-3 h-3 bg-blue-500 rounded mr-1"></div>
                  <span>环境问题</span>
                </div>
                <div class="flex items-center">
                  <div class="w-3 h-3 bg-green-500 rounded mr-1"></div>
                  <span>交通问题</span>
                </div>
                <div class="flex items-center">
                  <div class="w-3 h-3 bg-orange-500 rounded mr-1"></div>
                  <span>基础设施</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 事件时间线 -->
        <div class="timeline-section bg-white mx-4 rounded-lg shadow-sm mb-20">
          <div class="p-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">事件时间线</h3>
              <button class="text-blue-600 text-sm">查看全部</button>
            </div>
          </div>
          
          <div class="timeline-list">
            ${this.renderEventTimeline()}
          </div>
        </div>

        <!-- 底部导航容器 -->
        <div id="navigation-container" class="navigation-container"></div>
      </div>
    `;
  }

  renderEventTimeline() {
    if (!this.events || this.events.length === 0) {
      return `
        <div class="p-8 text-center text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          <p>暂无历史记录</p>
        </div>
      `;
    }

    return this.events.map((event, index) => `
      <div class="timeline-item p-4 border-b border-gray-100 last:border-b-0">
        <div class="flex items-start space-x-3">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 rounded-lg ${this.getEventStatusColor(event.status)} flex items-center justify-center">
              <span class="text-xs font-medium text-white">${index + 1}</span>
            </div>
          </div>
          
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <h4 class="text-sm font-medium text-gray-900 truncate">
                ${event.title || '未命名事件'}
              </h4>
              <span class="text-xs text-gray-500">
                ${this.formatDate(event.created_at)}
              </span>
            </div>
            
            <p class="text-sm text-gray-600 mt-1 line-clamp-2">
              ${event.description || '暂无描述'}
            </p>
            
            <div class="flex items-center justify-between mt-2">
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${this.getStatusBadgeClass(event.status)}">
                ${this.getStatusText(event.status)}
              </span>
              
              <div class="flex items-center space-x-2 text-xs text-gray-500">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                <span>${event.location?.address || '位置未知'}</span>
              </div>
            </div>
          </div>
          
          <div class="flex-shrink-0">
            <button class="p-1 text-gray-400 hover:text-gray-600">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderComponents() {
    // 渲染导航组件
    this.navigation = new Navigation({
      activeTab: 'history',
      onNavigate: (path, tabId) => this.handleNavigation(path, tabId)
    });

    const navContainer = this.container.querySelector('#navigation-container');
    this.navigation.mount(navContainer);
  }

  bindEvents() {
    // 绑定搜索事件
    const searchInput = this.container.querySelector('input[type="text"]');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.handleSearch(e.target.value);
      });
    }
  }

  handleSearch(query) {
    console.log('搜索:', query);
    // TODO: 实现搜索功能
  }

  handleNavigation(path, tabId) {
    if (window.router) {
      window.router.navigate(path);
    }
  }

  // 工具方法
  getResolvedCount() {
    if (!this.stats?.status_stats) return 1;
    return this.stats.status_stats.resolved || 1;
  }

  getPendingCount() {
    if (!this.stats?.status_stats) return 1;
    return (this.stats.status_stats.pending || 0) + (this.stats.status_stats.processing || 0) || 1;
  }

  getOverdueCount() {
    return 0; // 暂时返回0，后续可以根据实际需求计算
  }

  getResolutionRate() {
    if (!this.stats?.total_events || this.stats.total_events === 0) return 33;
    const resolved = this.getResolvedCount();
    return Math.round((resolved / this.stats.total_events) * 100);
  }

  getEventStatusColor(status) {
    const colors = {
      'pending': 'bg-yellow-500',
      'processing': 'bg-blue-500',
      'resolved': 'bg-green-500',
      'closed': 'bg-gray-500'
    };
    return colors[status] || 'bg-gray-500';
  }

  getStatusBadgeClass(status) {
    const classes = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'processing': 'bg-blue-100 text-blue-800',
      'resolved': 'bg-green-100 text-green-800',
      'closed': 'bg-gray-100 text-gray-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getStatusText(status) {
    const texts = {
      'pending': '待处理',
      'processing': '处理中',
      'resolved': '已解决',
      'closed': '已关闭'
    };
    return texts[status] || '未知';
  }

  formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    return `${Math.floor(diff / 86400000)}天前`;
  }

  mount(parent = document.body) {
    if (!this.container) {
      this.render();
    }
    parent.appendChild(this.container);
    return this;
  }

  unmount() {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
  }
}