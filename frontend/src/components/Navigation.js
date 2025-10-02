/**
 * 底部导航组件
 * 实现底部导航栏，支持路由跳转和状态管理，支持角色权限
 */
export class Navigation {
  constructor(options = {}) {
    this.activeTab = options.activeTab || 'home';
    this.onNavigate = options.onNavigate || this.defaultNavigate;
    this.container = null;
    
    // 获取用户角色
    const userRole = this.getUserRole();
    
    // 根据角色过滤导航项
    this.navItems = this.getNavItemsForRole(userRole);
  }

  /**
   * 获取当前用户角色
   */
  getUserRole() {
    try {
      if (window.userStore) {
        const userState = window.userStore.getState();
        return userState.user?.role || 'citizen';
      }
      return 'citizen';
    } catch (error) {
      console.warn('获取用户角色失败:', error);
      return 'citizen';
    }
  }

  /**
   * 根据角色获取导航项
   */
  getNavItemsForRole(role) {
    const allNavItems = [
      {
        id: 'home',
        label: '上报',
        path: '/',
        icon: this.getIcon('plus'),
        roles: ['citizen', 'grid_worker', 'manager', 'decision_maker']
      },
      {
        id: 'tracking',
        label: '跟踪',
        path: '/tracking',
        icon: this.getIcon('clipboard'),
        roles: ['citizen', 'grid_worker', 'manager', 'decision_maker']
      },
      {
        id: 'history',
        label: '历史',
        path: '/history',
        icon: this.getIcon('clock'),
        roles: ['grid_worker', 'manager', 'decision_maker']
      },
      {
        id: 'profile',
        label: '我的',
        path: '/profile',
        icon: this.getIcon('user'),
        roles: ['citizen', 'grid_worker', 'manager', 'decision_maker']
      }
    ];

    return allNavItems.filter(item => item.roles.includes(role));
  }

  /**
   * 获取SVG图标
   */
  getIcon(type) {
    const icons = {
      plus: `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
      </svg>`,
      clipboard: `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
      </svg>`,
      clock: `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>`,
      user: `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
      </svg>`
    };
    return icons[type] || icons.plus;
  }

  /**
   * 渲染导航组件
   */
  render() {
    this.container = document.createElement('nav');
    this.container.className = 'nav-bottom';
    
    const navContent = document.createElement('div');
    navContent.className = 'flex items-center justify-around py-3';
    
    this.navItems.forEach(item => {
      const navItem = this.createNavItem(item);
      navContent.appendChild(navItem);
    });
    
    this.container.appendChild(navContent);
    return this.container;
  }

  /**
   * 创建导航项
   */
  createNavItem(item) {
    const navItem = document.createElement('a');
    navItem.href = '#';
    navItem.className = `nav-item flex flex-col items-center space-y-1 ${
      this.activeTab === item.id ? 'active text-blue-600' : 'text-gray-500'
    }`;
    navItem.dataset.tab = item.id;
    navItem.dataset.path = item.path;
    
    navItem.innerHTML = `
      ${item.icon}
      <span class="text-xs">${item.label}</span>
    `;
    
    // 添加点击事件
    navItem.addEventListener('click', (e) => {
      e.preventDefault();
      this.handleNavClick(item);
    });
    
    return navItem;
  }

  /**
   * 处理导航点击
   */
  handleNavClick(item) {
    if (this.activeTab === item.id) return;
    
    // 添加点击动画
    this.animateClick(event.currentTarget);
    
    // 更新活动状态
    this.setActiveTab(item.id);
    
    // 触发导航回调
    this.onNavigate(item.path, item.id);
  }

  /**
   * 设置活动标签
   */
  setActiveTab(tabId) {
    if (this.activeTab === tabId) return;
    
    this.activeTab = tabId;
    this.updateActiveState();
  }

  /**
   * 更新活动状态
   */
  updateActiveState() {
    if (!this.container) return;
    
    const navItems = this.container.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      const isActive = item.dataset.tab === this.activeTab;
      
      if (isActive) {
        item.classList.add('active', 'text-blue-600');
        item.classList.remove('text-gray-500');
        // 添加激活动画
        this.animateActivation(item);
      } else {
        item.classList.remove('active', 'text-blue-600');
        item.classList.add('text-gray-500');
      }
    });
  }

  /**
   * 点击动画
   */
  animateClick(element) {
    element.style.transform = 'scale(0.95) translateY(-2px)';
    element.style.transition = 'transform 0.1s ease-out';
    
    setTimeout(() => {
      element.style.transform = '';
      element.style.transition = 'all 0.3s ease-in-out';
    }, 100);
  }

  /**
   * 激活动画
   */
  animateActivation(element) {
    // 添加弹跳效果
    element.style.animation = 'none';
    element.offsetHeight; // 触发重排
    element.style.animation = 'bounceIn 0.6s ease-out';
    
    setTimeout(() => {
      element.style.animation = '';
    }, 600);
  }

  /**
   * 默认导航处理
   */
  defaultNavigate(path, tabId) {
    console.log(`Navigate to ${path} (${tabId})`);
    
    // 集成路由系统
    if (window.router) {
      window.router.navigate(path);
    } else {
      // 降级处理：简单的页面跳转逻辑
      this.handleSimpleNavigation(path);
    }
  }

  /**
   * 简单导航处理（无路由系统时）
   */
  handleSimpleNavigation(path) {
    // 触发自定义事件，让应用层处理导航
    const navigationEvent = new CustomEvent('navigation', {
      detail: { path, activeTab: this.activeTab }
    });
    document.dispatchEvent(navigationEvent);
  }

  /**
   * 监听路由变化并同步导航状态
   */
  syncWithRouter() {
    if (!window.router) return;

    // 监听路由变化事件
    window.addEventListener('routechange', (event) => {
      const { path } = event.detail;
      this.updateActiveTabFromPath(path);
    });

    // 监听导航更新事件
    document.addEventListener('navigationupdate', (event) => {
      const { activeTab } = event.detail;
      if (activeTab !== this.activeTab) {
        this.setActiveTab(activeTab);
      }
    });

    // 初始同步
    const currentPath = window.router.getCurrentPath();
    this.updateActiveTabFromPath(currentPath);
  }

  /**
   * 根据路径更新活动标签
   * @param {string} path - 当前路径
   */
  updateActiveTabFromPath(path) {
    let activeTab = 'home';
    
    if (path.startsWith('/tracking')) {
      activeTab = 'tracking';
    } else if (path.startsWith('/profile')) {
      activeTab = 'profile';
    } else if (path === '/') {
      activeTab = 'home';
    }

    if (activeTab !== this.activeTab) {
      this.setActiveTab(activeTab);
    }
  }

  /**
   * 挂载到DOM
   */
  mount(parent = document.body) {
    if (!this.container) {
      this.render();
    }
    parent.appendChild(this.container);
    
    // 自动与路由系统同步
    this.syncWithRouter();
    
    return this;
  }

  /**
   * 从DOM卸载
   */
  unmount() {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    return this;
  }

  /**
   * 销毁组件
   */
  destroy() {
    this.unmount();
    this.container = null;
    this.onNavigate = null;
  }

  /**
   * 获取当前活动标签
   */
  getActiveTab() {
    return this.activeTab;
  }

  /**
   * 更新导航项
   */
  updateNavItems(newItems) {
    this.navItems = newItems;
    if (this.container) {
      this.container.innerHTML = '';
      this.render();
    }
  }

  /**
   * 显示/隐藏导航
   */
  show() {
    if (this.container) {
      this.container.style.display = 'block';
      this.container.style.animation = 'slideUp 0.3s ease-out';
    }
  }

  hide() {
    if (this.container) {
      this.container.style.animation = 'slideDown 0.3s ease-out';
      setTimeout(() => {
        if (this.container) {
          this.container.style.display = 'none';
        }
      }, 300);
    }
  }
}