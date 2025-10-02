/**
 * 全局错误处理系统
 * 处理应用中的各种错误情况
 */
export class ErrorHandler {
  static isInitialized = false;
  static errorQueue = [];
  static maxErrors = 50;

  /**
   * 初始化错误处理系统
   */
  static init() {
    if (this.isInitialized) return;

    // 监听全局错误
    window.addEventListener('error', this.handleGlobalError.bind(this));
    
    // 监听未处理的Promise拒绝
    window.addEventListener('unhandledrejection', this.handleUnhandledRejection.bind(this));
    
    this.isInitialized = true;
    console.log('ErrorHandler initialized');
  }

  /**
   * 处理全局错误
   * @param {ErrorEvent} event - 错误事件
   */
  static handleGlobalError(event) {
    const error = {
      type: 'javascript',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    this.logError(error);
    this.showErrorNotification('应用发生错误，请刷新页面重试');
  }

  /**
   * 处理未处理的Promise拒绝
   * @param {PromiseRejectionEvent} event - Promise拒绝事件
   */
  static handleUnhandledRejection(event) {
    const error = {
      type: 'promise',
      message: event.reason?.message || 'Unhandled promise rejection',
      reason: event.reason,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    this.logError(error);
    this.showErrorNotification('网络请求失败，请检查网络连接');
    
    // 阻止默认的控制台错误输出
    event.preventDefault();
  }

  /**
   * 手动处理错误
   * @param {Error|string} error - 错误对象或错误消息
   * @param {Object} context - 错误上下文
   */
  static handleError(error, context = {}) {
    const errorInfo = {
      type: 'manual',
      message: error?.message || error || 'Unknown error',
      stack: error?.stack,
      context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    this.logError(errorInfo);
    
    // 根据错误类型显示不同的通知
    if (context.showNotification !== false) {
      this.showErrorNotification(this.getErrorMessage(error, context));
    }
  }

  /**
   * 处理API错误
   * @param {Error} error - API错误
   * @param {Object} context - 请求上下文
   */
  static handleAPIError(error, context = {}) {
    const errorInfo = {
      type: 'api',
      message: error.message,
      status: error.status,
      statusText: error.statusText,
      url: context.url,
      method: context.method,
      timestamp: new Date().toISOString()
    };

    this.logError(errorInfo);

    // 根据HTTP状态码处理不同的错误
    switch (error.status) {
      case 401:
        this.handleUnauthorized(context);
        break;
      case 403:
        this.handleForbidden(context);
        break;
      case 404:
        this.handleNotFound(context);
        break;
      case 500:
        this.handleServerError(context);
        break;
      default:
        this.handleGenericAPIError(error, context);
    }
  }

  /**
   * 处理未授权错误
   * @param {Object} context - 错误上下文
   */
  static handleUnauthorized(context) {
    this.showErrorNotification('登录已过期，请重新登录');
    
    // 清除认证信息
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // 跳转到登录页面
    setTimeout(() => {
      if (window.router) {
        window.router.navigate('/login');
      } else {
        window.location.href = '/login';
      }
    }, 2000);
  }

  /**
   * 处理禁止访问错误
   * @param {Object} context - 错误上下文
   */
  static handleForbidden(context) {
    this.showErrorNotification('您没有权限访问此资源');
  }

  /**
   * 处理资源未找到错误
   * @param {Object} context - 错误上下文
   */
  static handleNotFound(context) {
    this.showErrorNotification('请求的资源不存在');
  }

  /**
   * 处理服务器错误
   * @param {Object} context - 错误上下文
   */
  static handleServerError(context) {
    this.showErrorNotification('服务器错误，请稍后重试');
  }

  /**
   * 处理通用API错误
   * @param {Error} error - 错误对象
   * @param {Object} context - 错误上下文
   */
  static handleGenericAPIError(error, context) {
    const message = error.message || '网络请求失败，请检查网络连接';
    this.showErrorNotification(message);
  }

  /**
   * 记录错误
   * @param {Object} errorInfo - 错误信息
   */
  static logError(errorInfo) {
    // 添加到错误队列
    this.errorQueue.push(errorInfo);
    
    // 限制队列大小
    if (this.errorQueue.length > this.maxErrors) {
      this.errorQueue.shift();
    }

    // 控制台输出
    console.error('Error logged:', errorInfo);

    // 发送到服务器（如果需要）
    this.sendErrorToServer(errorInfo);
  }

  /**
   * 发送错误到服务器
   * @param {Object} errorInfo - 错误信息
   */
  static sendErrorToServer(errorInfo) {
    // 只在生产环境发送错误报告
    if (process.env.NODE_ENV !== 'production') return;

    try {
      fetch('/api/v1/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(errorInfo)
      }).catch(err => {
        // 静默处理错误报告失败
        console.warn('Failed to send error report:', err);
      });
    } catch (err) {
      // 静默处理
    }
  }

  /**
   * 显示错误通知
   * @param {string} message - 错误消息
   */
  static showErrorNotification(message) {
    // 检查是否有通知组件
    if (window.Notification && typeof window.Notification.show === 'function') {
      window.Notification.show(message, 'error', 5000);
      return;
    }

    // 创建简单的错误通知
    this.createSimpleNotification(message, 'error');
  }

  /**
   * 显示成功通知
   * @param {string} message - 成功消息
   */
  static showSuccessNotification(message) {
    if (window.Notification && typeof window.Notification.show === 'function') {
      window.Notification.show(message, 'success', 3000);
      return;
    }

    this.createSimpleNotification(message, 'success');
  }

  /**
   * 显示警告通知
   * @param {string} message - 警告消息
   */
  static showWarningNotification(message) {
    if (window.Notification && typeof window.Notification.show === 'function') {
      window.Notification.show(message, 'warning', 4000);
      return;
    }

    this.createSimpleNotification(message, 'warning');
  }

  /**
   * 创建简单通知
   * @param {string} message - 消息
   * @param {string} type - 类型
   */
  static createSimpleNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${this.getNotificationClasses(type)}`;
    notification.innerHTML = `
      <div class="flex items-center">
        <div class="flex-shrink-0">
          ${this.getNotificationIcon(type)}
        </div>
        <div class="ml-3">
          <p class="text-sm font-medium">${message}</p>
        </div>
        <div class="ml-auto pl-3">
          <button class="inline-flex text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
            <span class="sr-only">关闭</span>
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(notification);

    // 自动移除
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
      }
    }, type === 'error' ? 5000 : 3000);

    // 添加进入动画
    notification.style.transform = 'translateX(100%)';
    notification.style.transition = 'transform 0.3s ease-out';
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 10);
  }

  /**
   * 获取通知样式类
   * @param {string} type - 通知类型
   */
  static getNotificationClasses(type) {
    const classes = {
      error: 'bg-red-50 border border-red-200 text-red-800',
      success: 'bg-green-50 border border-green-200 text-green-800',
      warning: 'bg-yellow-50 border border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border border-blue-200 text-blue-800'
    };
    return classes[type] || classes.info;
  }

  /**
   * 获取通知图标
   * @param {string} type - 通知类型
   */
  static getNotificationIcon(type) {
    const icons = {
      error: `<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
      </svg>`,
      success: `<svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
      </svg>`,
      warning: `<svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>`,
      info: `<svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
      </svg>`
    };
    return icons[type] || icons.info;
  }

  /**
   * 获取错误消息
   * @param {Error|string} error - 错误
   * @param {Object} context - 上下文
   */
  static getErrorMessage(error, context) {
    if (context.message) return context.message;
    if (typeof error === 'string') return error;
    if (error?.message) return error.message;
    return '发生未知错误';
  }

  /**
   * 获取错误队列
   */
  static getErrorQueue() {
    return [...this.errorQueue];
  }

  /**
   * 清空错误队列
   */
  static clearErrorQueue() {
    this.errorQueue = [];
  }

  /**
   * 获取错误统计
   */
  static getErrorStats() {
    const stats = {
      total: this.errorQueue.length,
      byType: {},
      recent: this.errorQueue.slice(-10)
    };

    this.errorQueue.forEach(error => {
      stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
    });

    return stats;
  }
}