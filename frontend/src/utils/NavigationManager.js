/**
 * 导航管理器
 * 统一管理应用的导航状态和行为
 */
import { Navigation } from '../components/Navigation.js';

export class NavigationManager {
  static instance = null;
  
  constructor() {
    this.navigation = null;
    this.currentPage = null;
    this.isInitialized = false;
  }

  /**
   * 获取单例实例
   */
  static getInstance() {
    if (!NavigationManager.instance) {
      NavigationManager.instance = new NavigationManager();
    }
    return NavigationManager.instance;
  }

  /**
   * 初始化导航管理器
   * @param {Object} options - 初始化选项
   */
  init(options = {}) {
    if (this.isInitialized) return;

    this.navigation = new Navigation({
      activeTab: options.activeTab || 'home',
      onNavigate: this.handleNavigation.bind(this)
    });

    // 监听路由变化
    this.setupRouteListeners();
    
    this.isInitialized = true;
    console.log('NavigationManager initialized');
  }

  /**
   * 设置路由监听器
   */
  setupRouteListeners() {
    // 监听路由变化事件
    window.addEventListener('routechange', (event) => {
      const { path } = event.detail;
      this.updateNavigationFromRoute(path);
    });

    // 监听导航更新事件
    document.addEventListener('navigationupdate', (event) => {
      const { activeTab } = event.detail;
      if (this.navigation && activeTab !== this.navigation.getActiveTab()) {
        this.navigation.setActiveTab(activeTab);
      }
    });
  }

  /**
   * 根据路由更新导航状态
   * @param {string} path - 当前路径
   */
  updateNavigationFromRoute(path) {
    if (!this.navigation) return;

    let activeTab = 'home';
    
    if (path.startsWith('/tracking')) {
      activeTab = 'tracking';
    } else if (path.startsWith('/profile')) {
      activeTab = 'profile';
    } else if (path === '/') {
      activeTab = 'home';
    }

    this.navigation.setActiveTab(activeTab);
  }

  /**
   * 处理导航点击
   * @param {string} path - 目标路径
   * @param {string} tabId - 标签ID
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
   * 挂载导航到指定容器
   * @param {HTMLElement} container - 容器元素
   */
  mount(container) {
    if (!this.navigation) {
      console.warn('NavigationManager not initialized');
      return;
    }

    this.navigation.mount(container);
  }

  /**
   * 获取导航组件
   */
  getNavigation() {
    return this.navigation;
  }

  /**
   * 设置当前页面
   * @param {string} pageName - 页面名称
   */
  setCurrentPage(pageName) {
    this.currentPage = pageName;
  }

  /**
   * 获取当前页面
   */
  getCurrentPage() {
    return this.currentPage;
  }

  /**
   * 显示导航
   */
  show() {
    if (this.navigation) {
      this.navigation.show();
    }
  }

  /**
   * 隐藏导航
   */
  hide() {
    if (this.navigation) {
      this.navigation.hide();
    }
  }

  /**
   * 更新导航项
   * @param {Array} navItems - 导航项配置
   */
  updateNavItems(navItems) {
    if (this.navigation) {
      this.navigation.updateNavItems(navItems);
    }
  }

  /**
   * 添加导航动画
   * @param {string} animationType - 动画类型
   */
  addNavigationAnimation(animationType = 'bounce') {
    if (!this.navigation || !this.navigation.container) return;

    const navElement = this.navigation.container;
    
    switch (animationType) {
      case 'bounce':
        navElement.style.animation = 'bounceIn 0.6s ease-out';
        break;
      case 'slide':
        navElement.style.animation = 'slideUp 0.4s ease-out';
        break;
      case 'fade':
        navElement.style.animation = 'fadeIn 0.3s ease-out';
        break;
    }

    // 清理动画
    setTimeout(() => {
      if (navElement) {
        navElement.style.animation = '';
      }
    }, 600);
  }

  /**
   * 设置导航徽章
   * @param {string} tabId - 标签ID
   * @param {number|string} badge - 徽章内容
   */
  setBadge(tabId, badge) {
    if (!this.navigation || !this.navigation.container) return;

    const navItem = this.navigation.container.querySelector(`[data-tab="${tabId}"]`);
    if (!navItem) return;

    // 移除现有徽章
    const existingBadge = navItem.querySelector('.nav-badge');
    if (existingBadge) {
      existingBadge.remove();
    }

    // 添加新徽章
    if (badge) {
      const badgeElement = document.createElement('span');
      badgeElement.className = 'nav-badge';
      badgeElement.textContent = badge;
      badgeElement.style.cssText = `
        position: absolute;
        top: -2px;
        right: -2px;
        background: #ef4444;
        color: white;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        font-size: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
      `;

      navItem.style.position = 'relative';
      navItem.appendChild(badgeElement);
    }
  }

  /**
   * 清除导航徽章
   * @param {string} tabId - 标签ID
   */
  clearBadge(tabId) {
    this.setBadge(tabId, null);
  }

  /**
   * 启用/禁用导航项
   * @param {string} tabId - 标签ID
   * @param {boolean} enabled - 是否启用
   */
  setNavItemEnabled(tabId, enabled) {
    if (!this.navigation || !this.navigation.container) return;

    const navItem = this.navigation.container.querySelector(`[data-tab="${tabId}"]`);
    if (!navItem) return;

    if (enabled) {
      navItem.classList.remove('disabled');
      navItem.style.opacity = '1';
      navItem.style.pointerEvents = 'auto';
    } else {
      navItem.classList.add('disabled');
      navItem.style.opacity = '0.5';
      navItem.style.pointerEvents = 'none';
    }
  }

  /**
   * 获取导航状态
   */
  getNavigationState() {
    return {
      currentPage: this.currentPage,
      activeTab: this.navigation?.getActiveTab(),
      isInitialized: this.isInitialized
    };
  }

  /**
   * 销毁导航管理器
   */
  destroy() {
    if (this.navigation) {
      this.navigation.destroy();
      this.navigation = null;
    }

    this.currentPage = null;
    this.isInitialized = false;
    
    // 清理事件监听器
    window.removeEventListener('routechange', this.updateNavigationFromRoute);
    document.removeEventListener('navigationupdate', this.handleNavigationUpdate);

    NavigationManager.instance = null;
  }
}