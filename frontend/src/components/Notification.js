/**
 * 通知组件
 * 实现全局通知提示，支持不同类型和自动消失
 */
export class Notification {
  constructor(options = {}) {
    this.message = options.message || '';
    this.type = options.type || 'info'; // success, error, warning, info
    this.duration = options.duration || 3000;
    this.closable = options.closable !== false;
    this.position = options.position || 'top-right'; // top-right, top-left, bottom-right, bottom-left, top-center
    this.onClose = options.onClose || null;
    this.onClick = options.onClick || null;
    
    this.container = null;
    this.isVisible = false;
    this.timer = null;
    
    // 绑定方法
    this.handleClick = this.handleClick.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  /**
   * 获取图标
   */
  getIcon() {
    const icons = {
      success: `<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
      </svg>`,
      error: `<svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>`,
      warning: `<svg class="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
      </svg>`,
      info: `<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>`
    };
    return icons[this.type] || icons.info;
  }

  /**
   * 获取位置样式类
   */
  getPositionClass() {
    const positions = {
      'top-right': 'top-4 right-4',
      'top-left': 'top-4 left-4',
      'bottom-right': 'bottom-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'top-center': 'top-4 left-1/2 transform -translate-x-1/2'
    };
    return positions[this.position] || positions['top-right'];
  }

  /**
   * 创建通知HTML结构
   */
  createNotificationHTML() {
    return `
      <div class="notification ${this.type} ${this.getPositionClass()} max-w-sm cursor-pointer" role="alert">
        <div class="flex items-start space-x-3 p-4">
          <div class="flex-shrink-0">
            ${this.getIcon()}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium">${this.message}</p>
          </div>
          ${this.closable ? `
            <button class="notification-close flex-shrink-0 ml-2 p-1 hover:bg-black hover:bg-opacity-10 rounded-full transition-colors" aria-label="关闭">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          ` : ''}
        </div>
        ${this.duration > 0 ? `
          <div class="notification-progress absolute bottom-0 left-0 h-1 bg-current opacity-30 transition-all duration-${this.duration} ease-linear" style="width: 100%"></div>
        ` : ''}
      </div>
    `;
  }

  /**
   * 渲染通知
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'toast fixed z-50';
    this.container.innerHTML = this.createNotificationHTML();
    
    this.bindEvents();
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.container) return;
    
    // 点击事件
    this.container.addEventListener('click', this.handleClick);
    
    // 关闭按钮事件
    const closeBtn = this.container.querySelector('.notification-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleClose();
      });
    }
    
    // 鼠标悬停暂停自动关闭
    if (this.duration > 0) {
      this.container.addEventListener('mouseenter', () => {
        this.pauseTimer();
      });
      
      this.container.addEventListener('mouseleave', () => {
        this.resumeTimer();
      });
    }
  }

  /**
   * 处理点击事件
   */
  handleClick() {
    if (this.onClick) {
      this.onClick(this);
    }
  }

  /**
   * 处理关闭事件
   */
  handleClose() {
    this.hide();
  }

  /**
   * 显示通知
   */
  show() {
    if (this.isVisible) return Promise.resolve();
    
    return new Promise((resolve) => {
      if (!this.container) {
        this.render();
      }
      
      // 添加到DOM
      document.body.appendChild(this.container);
      
      this.isVisible = true;
      
      // 显示动画
      requestAnimationFrame(() => {
        this.container.classList.add('show');
        
        const notification = this.container.querySelector('.notification');
        if (notification) {
          notification.style.animation = 'slideDown 0.3s ease-out';
        }
        
        // 启动进度条动画
        if (this.duration > 0) {
          const progressBar = this.container.querySelector('.notification-progress');
          if (progressBar) {
            requestAnimationFrame(() => {
              progressBar.style.width = '0%';
            });
          }
        }
        
        setTimeout(() => {
          resolve();
        }, 300);
      });
      
      // 设置自动关闭定时器
      if (this.duration > 0) {
        this.startTimer();
      }
    });
  }

  /**
   * 隐藏通知
   */
  hide() {
    if (!this.isVisible) return Promise.resolve();
    
    return new Promise((resolve) => {
      this.clearTimer();
      
      const notification = this.container.querySelector('.notification');
      if (notification) {
        notification.style.animation = 'slideUp 0.3s ease-out';
      }
      
      this.container.classList.add('hide');
      
      setTimeout(() => {
        if (this.container && this.container.parentNode) {
          this.container.parentNode.removeChild(this.container);
        }
        
        this.isVisible = false;
        
        // 触发关闭回调
        if (this.onClose) {
          this.onClose(this);
        }
        
        resolve();
      }, 300);
    });
  }

  /**
   * 启动定时器
   */
  startTimer() {
    if (this.duration <= 0) return;
    
    this.timer = setTimeout(() => {
      this.hide();
    }, this.duration);
  }

  /**
   * 暂停定时器
   */
  pauseTimer() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    
    // 暂停进度条动画
    const progressBar = this.container?.querySelector('.notification-progress');
    if (progressBar) {
      progressBar.style.animationPlayState = 'paused';
    }
  }

  /**
   * 恢复定时器
   */
  resumeTimer() {
    if (this.duration > 0 && !this.timer) {
      this.startTimer();
    }
    
    // 恢复进度条动画
    const progressBar = this.container?.querySelector('.notification-progress');
    if (progressBar) {
      progressBar.style.animationPlayState = 'running';
    }
  }

  /**
   * 清除定时器
   */
  clearTimer() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  /**
   * 更新消息
   */
  updateMessage(message) {
    this.message = message;
    
    if (this.container) {
      const messageElement = this.container.querySelector('.notification p');
      if (messageElement) {
        messageElement.textContent = message;
      }
    }
  }

  /**
   * 销毁通知
   */
  destroy() {
    this.clearTimer();
    
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.container = null;
    this.onClose = null;
    this.onClick = null;
  }

  // 静态方法和通知管理器
  static notifications = new Map();
  static maxNotifications = 5;

  /**
   * 显示成功通知
   */
  static success(message, options = {}) {
    return this.show({
      ...options,
      message,
      type: 'success'
    });
  }

  /**
   * 显示错误通知
   */
  static error(message, options = {}) {
    return this.show({
      ...options,
      message,
      type: 'error',
      duration: options.duration || 5000 // 错误通知显示更长时间
    });
  }

  /**
   * 显示警告通知
   */
  static warning(message, options = {}) {
    return this.show({
      ...options,
      message,
      type: 'warning'
    });
  }

  /**
   * 显示信息通知
   */
  static info(message, options = {}) {
    return this.show({
      ...options,
      message,
      type: 'info'
    });
  }

  /**
   * 显示通知（通用方法）
   */
  static show(options = {}) {
    // 限制同时显示的通知数量
    if (this.notifications.size >= this.maxNotifications) {
      const firstNotification = this.notifications.values().next().value;
      if (firstNotification) {
        firstNotification.hide();
      }
    }
    
    const notification = new Notification(options);
    const id = Date.now() + Math.random();
    
    // 添加到管理器
    this.notifications.set(id, notification);
    
    // 设置关闭回调，从管理器中移除
    const originalOnClose = notification.onClose;
    notification.onClose = (instance) => {
      this.notifications.delete(id);
      if (originalOnClose) {
        originalOnClose(instance);
      }
    };
    
    notification.show();
    return notification;
  }

  /**
   * 清除所有通知
   */
  static clearAll() {
    this.notifications.forEach(notification => {
      notification.hide();
    });
    this.notifications.clear();
  }

  /**
   * 获取当前通知数量
   */
  static getCount() {
    return this.notifications.size;
  }
}