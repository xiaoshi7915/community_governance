/**
 * 客户端路由管理系统
 * 实现SPA路由功能，支持懒加载、路由守卫和权限验证
 */
export class Router {
  constructor(options = {}) {
    this.routes = new Map();
    this.guards = [];
    this.currentRoute = null;
    this.currentComponent = null;
    this.container = options.container || document.getElementById('app') || document.body;
    this.basePath = options.basePath || '';
    this.mode = options.mode || 'hash'; // 'hash' or 'history'
    this.defaultRoute = options.defaultRoute || '/';
    
    // 绑定事件处理器
    this.handlePopState = this.handlePopState.bind(this);
    this.handleHashChange = this.handleHashChange.bind(this);
  }

  /**
   * 注册路由
   * @param {string} path - 路由路径
   * @param {Function|Object} component - 组件构造函数或配置对象
   * @param {Object} options - 路由选项
   */
  register(path, component, options = {}) {
    const route = {
      path: this.normalizePath(path),
      component,
      options: {
        requiresAuth: options.requiresAuth || false,
        roles: options.roles || [],
        meta: options.meta || {},
        beforeEnter: options.beforeEnter,
        ...options
      }
    };

    this.routes.set(route.path, route);
    return this;
  }

  /**
   * 批量注册路由
   * @param {Array} routes - 路由配置数组
   */
  registerRoutes(routes) {
    routes.forEach(route => {
      this.register(route.path, route.component, route.options);
    });
    return this;
  }

  /**
   * 添加全局路由守卫
   * @param {Function} guard - 守卫函数
   */
  addGuard(guard) {
    if (typeof guard === 'function') {
      this.guards.push(guard);
    }
    return this;
  }

  /**
   * 启动路由系统
   */
  start() {
    // 注册默认路由
    this.registerDefaultRoutes();
    
    // 监听路由变化
    if (this.mode === 'history') {
      window.addEventListener('popstate', this.handlePopState);
    } else {
      window.addEventListener('hashchange', this.handleHashChange);
    }

    // 处理初始路由
    const initialPath = this.getCurrentPath();
    this.navigate(initialPath || this.defaultRoute, { replace: true });
    
    console.log('Router started with mode:', this.mode);
    return this;
  }

  /**
   * 停止路由系统
   */
  stop() {
    if (this.mode === 'history') {
      window.removeEventListener('popstate', this.handlePopState);
    } else {
      window.removeEventListener('hashchange', this.handleHashChange);
    }
    return this;
  }

  /**
   * 导航到指定路径
   * @param {string} path - 目标路径
   * @param {Object} options - 导航选项
   */
  async navigate(path, options = {}) {
    const normalizedPath = this.normalizePath(path);
    
    try {
      // 执行路由守卫
      const guardResult = await this.executeGuards(normalizedPath, this.currentRoute);
      if (guardResult === false) {
        console.log('Navigation blocked by guard');
        return false;
      }

      // 如果守卫返回重定向路径
      if (typeof guardResult === 'string') {
        return this.navigate(guardResult, options);
      }

      // 查找匹配的路由
      const route = this.findRoute(normalizedPath);
      if (!route) {
        console.warn(`Route not found: ${normalizedPath}`);
        return this.navigate('/404', { replace: true });
      }

      // 执行路由特定的守卫
      if (route.options.beforeEnter) {
        const beforeEnterResult = await route.options.beforeEnter(normalizedPath, this.currentRoute);
        if (beforeEnterResult === false) {
          return false;
        }
        if (typeof beforeEnterResult === 'string') {
          return this.navigate(beforeEnterResult, options);
        }
      }

      // 更新浏览器历史
      this.updateHistory(normalizedPath, options.replace);

      // 渲染新组件
      await this.renderRoute(route, normalizedPath);

      // 更新当前路由
      this.currentRoute = {
        path: normalizedPath,
        route: route
      };

      // 触发路由变化事件
      this.emitRouteChange(normalizedPath, route);

      return true;
    } catch (error) {
      console.error('Navigation error:', error);
      this.handleNavigationError(error, path);
      return false;
    }
  }

  /**
   * 后退
   */
  back() {
    window.history.back();
  }

  /**
   * 前进
   */
  forward() {
    window.history.forward();
  }

  /**
   * 替换当前路由
   * @param {string} path - 目标路径
   */
  replace(path) {
    return this.navigate(path, { replace: true });
  }

  /**
   * 获取当前路径
   */
  getCurrentPath() {
    if (this.mode === 'history') {
      return window.location.pathname.replace(this.basePath, '') || '/';
    } else {
      return window.location.hash.slice(1) || '/';
    }
  }

  /**
   * 查找匹配的路由
   * @param {string} path - 路径
   */
  findRoute(path) {
    // 精确匹配
    if (this.routes.has(path)) {
      return this.routes.get(path);
    }

    // 参数匹配（简单实现）
    for (const [routePath, route] of this.routes) {
      if (this.matchPath(routePath, path)) {
        return route;
      }
    }

    return null;
  }

  /**
   * 路径匹配
   * @param {string} routePath - 路由路径
   * @param {string} actualPath - 实际路径
   */
  matchPath(routePath, actualPath) {
    // 简单的参数匹配实现
    const routeSegments = routePath.split('/');
    const actualSegments = actualPath.split('/');

    if (routeSegments.length !== actualSegments.length) {
      return false;
    }

    return routeSegments.every((segment, index) => {
      return segment.startsWith(':') || segment === actualSegments[index];
    });
  }

  /**
   * 执行全局路由守卫
   * @param {string} to - 目标路径
   * @param {Object} from - 当前路由
   */
  async executeGuards(to, from) {
    for (const guard of this.guards) {
      try {
        const result = await guard(to, from);
        if (result === false || typeof result === 'string') {
          return result;
        }
      } catch (error) {
        console.error('Guard execution error:', error);
        return false;
      }
    }
    return true;
  }

  /**
   * 渲染路由组件
   * @param {Object} route - 路由配置
   * @param {string} path - 路径
   */
  async renderRoute(route, path) {
    try {
      // 动态导入PageTransition
      const { PageTransition } = await import('./PageTransition.js');

      // 获取当前元素用于转场动画
      const currentElement = this.container.firstElementChild;
      
      // 显示加载状态
      const loadingElement = PageTransition.showLoading(this.container, {
        message: '页面加载中...',
        timeout: 8000
      });

      // 懒加载组件
      let ComponentClass = route.component;
      
      // 检查是否是动态导入函数
      if (typeof ComponentClass === 'function') {
        // 检查函数字符串是否包含import()，这表明它是一个动态导入函数
        const funcString = ComponentClass.toString();
        if (funcString.includes('import(') || funcString.includes('then(')) {
          try {
            // 是动态导入函数，调用它获取Promise
            const modulePromise = ComponentClass();
            if (modulePromise && typeof modulePromise.then === 'function') {
              // 等待模块加载
              const module = await modulePromise;
              ComponentClass = module.default || module[Object.keys(module)[0]] || module;
            }
          } catch (error) {
            console.error('Dynamic import failed:', error);
            throw new Error(`Failed to load component: ${error.message}`);
          }
        }
        // 如果不是动态导入函数，直接使用作为构造函数
      }

      // 销毁当前组件
      if (this.currentComponent && typeof this.currentComponent.destroy === 'function') {
        this.currentComponent.destroy();
      }

      // 创建组件实例
      const component = new ComponentClass({
        path,
        route: route.options,
        router: this
      });

      // 渲染新组件
      let newElement;
      if (typeof component.render === 'function') {
        newElement = component.render();
      } else {
        throw new Error('Component must have a render method');
      }

      // 隐藏加载状态
      PageTransition.hideLoading(this.container);

      // 清空容器并添加新元素
      this.container.innerHTML = '';
      this.container.appendChild(newElement);
      
      // 执行页面转场动画
      if (currentElement && newElement && currentElement !== newElement) {
        // 执行淡入动画
        await PageTransition.fadeIn(newElement);
      } else {
        // 执行淡入动画
        await PageTransition.fadeIn(newElement);
      }

      this.currentComponent = component;

    } catch (error) {
      console.error('Route rendering error:', error);
      this.showErrorState(error);
    }
  }

  /**
   * 获取转场方向
   * @param {string} fromPath - 来源路径
   * @param {string} toPath - 目标路径
   */
  getTransitionDirection(fromPath, toPath) {
    // 定义页面层级
    const pageHierarchy = {
      '/': 0,
      '/tracking': 1,
      '/profile': 2
    };

    const fromLevel = pageHierarchy[fromPath] || 0;
    const toLevel = pageHierarchy[toPath] || 0;

    // 根据层级确定方向
    return toLevel > fromLevel ? 'forward' : 'backward';
  }

  /**
   * 显示错误状态
   * @param {Error} error - 错误对象
   */
  async showErrorState(error) {
    try {
      const { PageTransition } = await import('./PageTransition.js');
      PageTransition.showLoadingError(this.container, error.message || '页面加载失败');
    } catch (importError) {
      // 降级处理
      this.container.innerHTML = `
        <div class="error-state flex items-center justify-center min-h-screen">
          <div class="text-center">
            <div class="text-red-500 text-6xl mb-4">⚠️</div>
            <h2 class="text-xl font-bold text-gray-800 mb-2">页面加载失败</h2>
            <p class="text-gray-600 mb-4">${error.message || '未知错误'}</p>
            <button onclick="location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              重新加载
            </button>
          </div>
        </div>
      `;
    }
  }

  /**
   * 更新浏览器历史
   * @param {string} path - 路径
   * @param {boolean} replace - 是否替换当前历史记录
   */
  updateHistory(path, replace = false) {
    if (this.mode === 'history') {
      const url = this.basePath + path;
      if (replace) {
        window.history.replaceState({ path }, '', url);
      } else {
        window.history.pushState({ path }, '', url);
      }
    } else {
      if (replace) {
        window.location.replace('#' + path);
      } else {
        window.location.hash = path;
      }
    }
  }

  /**
   * 处理popstate事件
   */
  handlePopState(event) {
    const path = event.state?.path || this.getCurrentPath();
    this.navigate(path, { replace: true });
  }

  /**
   * 处理hashchange事件
   */
  handleHashChange() {
    const path = this.getCurrentPath();
    this.navigate(path, { replace: true });
  }

  /**
   * 标准化路径
   * @param {string} path - 原始路径
   */
  normalizePath(path) {
    if (!path || path === '/') return '/';
    return path.startsWith('/') ? path : '/' + path;
  }

  /**
   * 触发路由变化事件
   * @param {string} path - 路径
   * @param {Object} route - 路由配置
   */
  emitRouteChange(path, route) {
    const event = new CustomEvent('routechange', {
      detail: { path, route, router: this }
    });
    window.dispatchEvent(event);
  }

  /**
   * 处理导航错误
   * @param {Error} error - 错误对象
   * @param {string} path - 目标路径
   */
  handleNavigationError(error, path) {
    console.error(`Navigation to ${path} failed:`, error);
    
    // 尝试导航到错误页面
    if (path !== '/error') {
      this.navigate('/error', { replace: true });
    }
  }

  /**
   * 注册默认路由
   */
  registerDefaultRoutes() {
    // 404页面
    if (!this.routes.has('/404')) {
      this.register('/404', class NotFoundPage {
        render() {
          const div = document.createElement('div');
          div.innerHTML = `
            <div class="not-found-page flex items-center justify-center min-h-screen">
              <div class="text-center">
                <div class="text-gray-400 text-8xl mb-4">404</div>
                <h2 class="text-2xl font-bold text-gray-800 mb-2">页面未找到</h2>
                <p class="text-gray-600 mb-4">您访问的页面不存在</p>
                <button onclick="history.back()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                  返回上页
                </button>
              </div>
            </div>
          `;
          return div;
        }
      });
    }

    // 错误页面
    if (!this.routes.has('/error')) {
      this.register('/error', class ErrorPage {
        render() {
          const div = document.createElement('div');
          div.innerHTML = `
            <div class="error-page flex items-center justify-center min-h-screen">
              <div class="text-center">
                <div class="text-red-500 text-6xl mb-4">⚠️</div>
                <h2 class="text-xl font-bold text-gray-800 mb-2">系统错误</h2>
                <p class="text-gray-600 mb-4">系统遇到了一些问题</p>
                <button onclick="location.reload()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                  重新加载
                </button>
              </div>
            </div>
          `;
          return div;
        }
      });
    }
  }

  /**
   * 获取路由信息
   */
  getRouteInfo() {
    return {
      currentPath: this.getCurrentPath(),
      currentRoute: this.currentRoute,
      routes: Array.from(this.routes.keys())
    };
  }

  /**
   * 销毁路由器
   */
  destroy() {
    this.stop();
    
    if (this.currentComponent && typeof this.currentComponent.destroy === 'function') {
      this.currentComponent.destroy();
    }
    
    this.routes.clear();
    this.guards = [];
    this.currentRoute = null;
    this.currentComponent = null;
  }
}