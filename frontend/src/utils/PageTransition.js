/**
 * 页面转场动画系统
 * 提供平滑的页面切换体验和加载状态管理
 */
export class PageTransition {
  static currentTransition = null;
  static transitionDuration = 400;
  static loadingTimeout = null;

  /**
   * 页面淡入动画
   * @param {HTMLElement} element - 目标元素
   * @param {Object} options - 动画选项
   */
  static async fadeIn(element, options = {}) {
    const {
      duration = this.transitionDuration,
      delay = 0,
      easing = 'ease-out'
    } = options;

    // 设置初始状态
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    element.style.transition = `opacity ${duration}ms ${easing}, transform ${duration}ms ${easing}`;

    // 延迟后开始动画
    await this.delay(delay);

    // 触发动画
    element.style.opacity = '1';
    element.style.transform = 'translateY(0)';

    // 等待动画完成
    await this.delay(duration);

    // 清理样式
    element.style.transition = '';
  }

  /**
   * 页面淡出动画
   * @param {HTMLElement} element - 目标元素
   * @param {Object} options - 动画选项
   */
  static async fadeOut(element, options = {}) {
    const {
      duration = this.transitionDuration,
      delay = 0,
      easing = 'ease-in'
    } = options;

    element.style.transition = `opacity ${duration}ms ${easing}, transform ${duration}ms ${easing}`;

    await this.delay(delay);

    element.style.opacity = '0';
    element.style.transform = 'translateY(-20px)';

    await this.delay(duration);
  }

  /**
   * 滑入动画
   * @param {HTMLElement} element - 目标元素
   * @param {string} direction - 滑入方向 ('left', 'right', 'up', 'down')
   * @param {Object} options - 动画选项
   */
  static async slideIn(element, direction = 'right', options = {}) {
    const {
      duration = this.transitionDuration,
      delay = 0,
      easing = 'ease-out'
    } = options;

    const transforms = {
      left: 'translateX(-100%)',
      right: 'translateX(100%)',
      up: 'translateY(-100%)',
      down: 'translateY(100%)'
    };

    element.style.transform = transforms[direction] || transforms.right;
    element.style.opacity = '0';
    element.style.transition = `transform ${duration}ms ${easing}, opacity ${duration}ms ${easing}`;

    await this.delay(delay);

    element.style.transform = 'translate(0, 0)';
    element.style.opacity = '1';

    await this.delay(duration);

    element.style.transition = '';
  }

  /**
   * 滑出动画
   * @param {HTMLElement} element - 目标元素
   * @param {string} direction - 滑出方向
   * @param {Object} options - 动画选项
   */
  static async slideOut(element, direction = 'left', options = {}) {
    const {
      duration = this.transitionDuration,
      delay = 0,
      easing = 'ease-in'
    } = options;

    const transforms = {
      left: 'translateX(-100%)',
      right: 'translateX(100%)',
      up: 'translateY(-100%)',
      down: 'translateY(100%)'
    };

    element.style.transition = `transform ${duration}ms ${easing}, opacity ${duration}ms ${easing}`;

    await this.delay(delay);

    element.style.transform = transforms[direction] || transforms.left;
    element.style.opacity = '0';

    await this.delay(duration);
  }

  /**
   * 缩放动画
   * @param {HTMLElement} element - 目标元素
   * @param {Object} options - 动画选项
   */
  static async scaleIn(element, options = {}) {
    const {
      duration = this.transitionDuration,
      delay = 0,
      easing = 'ease-out',
      fromScale = 0.8
    } = options;

    element.style.transform = `scale(${fromScale})`;
    element.style.opacity = '0';
    element.style.transition = `transform ${duration}ms ${easing}, opacity ${duration}ms ${easing}`;

    await this.delay(delay);

    element.style.transform = 'scale(1)';
    element.style.opacity = '1';

    await this.delay(duration);

    element.style.transition = '';
  }

  /**
   * 页面切换动画
   * @param {HTMLElement} outElement - 离开的元素
   * @param {HTMLElement} inElement - 进入的元素
   * @param {string} direction - 切换方向 ('forward', 'backward')
   * @param {Object} options - 动画选项
   */
  static async pageTransition(outElement, inElement, direction = 'forward', options = {}) {
    const {
      duration = this.transitionDuration,
      easing = 'ease-in-out'
    } = options;

    // 取消当前进行的转场
    if (this.currentTransition) {
      this.currentTransition.cancel();
    }

    // 创建转场Promise
    this.currentTransition = this.createCancellablePromise(async () => {
      // 设置容器样式
      const container = outElement.parentElement;
      if (container) {
        container.style.position = 'relative';
        container.style.overflow = 'hidden';
      }

      // 设置元素初始位置
      if (inElement) {
        inElement.style.position = 'absolute';
        inElement.style.top = '0';
        inElement.style.left = '0';
        inElement.style.width = '100%';
        inElement.style.height = '100%';
      }

      // 执行并行动画
      const animations = [];

      if (outElement) {
        const outDirection = direction === 'forward' ? 'left' : 'right';
        animations.push(this.slideOut(outElement, outDirection, { duration, easing }));
      }

      if (inElement) {
        const inDirection = direction === 'forward' ? 'right' : 'left';
        animations.push(this.slideIn(inElement, inDirection, { duration, easing }));
      }

      await Promise.all(animations);

      // 清理样式
      if (inElement) {
        inElement.style.position = '';
        inElement.style.top = '';
        inElement.style.left = '';
        inElement.style.width = '';
        inElement.style.height = '';
      }

      if (container) {
        container.style.position = '';
        container.style.overflow = '';
      }
    });

    try {
      await this.currentTransition.promise;
    } catch (error) {
      if (error.name !== 'TransitionCancelled') {
        throw error;
      }
    } finally {
      this.currentTransition = null;
    }
  }

  /**
   * 显示加载状态
   * @param {HTMLElement} container - 容器元素
   * @param {Object} options - 选项
   */
  static showLoading(container, options = {}) {
    const {
      message = '加载中...',
      timeout = 10000,
      showSpinner = true
    } = options;

    // 清除之前的加载状态
    this.hideLoading(container);

    // 创建加载元素
    const loadingElement = document.createElement('div');
    loadingElement.className = 'page-loading-overlay';
    loadingElement.innerHTML = `
      <div class="loading-content">
        ${showSpinner ? `
          <div class="loading-spinner">
            <div class="spinner-ring"></div>
          </div>
        ` : ''}
        <p class="loading-message">${message}</p>
      </div>
    `;

    // 添加样式
    this.addLoadingStyles(loadingElement);

    // 添加到容器
    container.appendChild(loadingElement);

    // 淡入动画
    this.fadeIn(loadingElement, { duration: 200 });

    // 设置超时
    if (timeout > 0) {
      this.loadingTimeout = setTimeout(() => {
        this.showLoadingError(container, '加载超时，请重试');
      }, timeout);
    }

    return loadingElement;
  }

  /**
   * 隐藏加载状态
   * @param {HTMLElement} container - 容器元素
   */
  static hideLoading(container) {
    const loadingElement = container.querySelector('.page-loading-overlay');
    if (loadingElement) {
      this.fadeOut(loadingElement, { duration: 200 }).then(() => {
        if (loadingElement.parentNode) {
          loadingElement.parentNode.removeChild(loadingElement);
        }
      });
    }

    // 清除超时
    if (this.loadingTimeout) {
      clearTimeout(this.loadingTimeout);
      this.loadingTimeout = null;
    }
  }

  /**
   * 显示加载错误
   * @param {HTMLElement} container - 容器元素
   * @param {string} message - 错误消息
   */
  static showLoadingError(container, message = '加载失败') {
    this.hideLoading(container);

    const errorElement = document.createElement('div');
    errorElement.className = 'page-loading-error';
    errorElement.innerHTML = `
      <div class="error-content">
        <div class="error-icon">⚠️</div>
        <p class="error-message">${message}</p>
        <button class="retry-button" onclick="location.reload()">重试</button>
      </div>
    `;

    this.addErrorStyles(errorElement);
    container.appendChild(errorElement);
    this.fadeIn(errorElement, { duration: 200 });
  }

  /**
   * 添加加载样式
   * @param {HTMLElement} element - 加载元素
   */
  static addLoadingStyles(element) {
    const styles = `
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    `;

    element.style.cssText = styles;

    // 添加内容样式
    const content = element.querySelector('.loading-content');
    if (content) {
      content.style.cssText = `
        text-align: center;
        color: #374151;
      `;
    }

    // 添加旋转器样式
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) {
      spinner.style.cssText = `
        margin-bottom: 16px;
      `;
    }

    const ring = element.querySelector('.spinner-ring');
    if (ring) {
      ring.style.cssText = `
        width: 32px;
        height: 32px;
        border: 3px solid #e5e7eb;
        border-top: 3px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto;
      `;
    }

    // 添加消息样式
    const message = element.querySelector('.loading-message');
    if (message) {
      message.style.cssText = `
        margin: 0;
        font-size: 14px;
        color: #6b7280;
      `;
    }

    // 添加旋转动画
    this.addSpinAnimation();
  }

  /**
   * 添加错误样式
   * @param {HTMLElement} element - 错误元素
   */
  static addErrorStyles(element) {
    element.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.95);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    `;

    const content = element.querySelector('.error-content');
    if (content) {
      content.style.cssText = `
        text-align: center;
        padding: 20px;
      `;
    }

    const icon = element.querySelector('.error-icon');
    if (icon) {
      icon.style.cssText = `
        font-size: 48px;
        margin-bottom: 16px;
      `;
    }

    const message = element.querySelector('.error-message');
    if (message) {
      message.style.cssText = `
        margin: 0 0 16px 0;
        color: #374151;
        font-size: 16px;
      `;
    }

    const button = element.querySelector('.retry-button');
    if (button) {
      button.style.cssText = `
        background: #3b82f6;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
      `;
    }
  }

  /**
   * 添加旋转动画
   */
  static addSpinAnimation() {
    if (document.getElementById('page-transition-styles')) return;

    const style = document.createElement('style');
    style.id = 'page-transition-styles';
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      .page-transition-enter {
        opacity: 0;
        transform: translateX(100%);
      }
      
      .page-transition-enter-active {
        opacity: 1;
        transform: translateX(0);
        transition: opacity 400ms ease-out, transform 400ms ease-out;
      }
      
      .page-transition-exit {
        opacity: 1;
        transform: translateX(0);
      }
      
      .page-transition-exit-active {
        opacity: 0;
        transform: translateX(-100%);
        transition: opacity 400ms ease-in, transform 400ms ease-in;
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * 创建可取消的Promise
   * @param {Function} executor - 执行函数
   */
  static createCancellablePromise(executor) {
    let cancelled = false;
    let cancel;

    const promise = new Promise(async (resolve, reject) => {
      cancel = () => {
        cancelled = true;
        reject(new Error('TransitionCancelled'));
      };

      try {
        await executor();
        if (!cancelled) {
          resolve();
        }
      } catch (error) {
        if (!cancelled) {
          reject(error);
        }
      }
    });

    return { promise, cancel };
  }

  /**
   * 延迟函数
   * @param {number} ms - 延迟毫秒数
   */
  static delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 设置全局转场持续时间
   * @param {number} duration - 持续时间（毫秒）
   */
  static setTransitionDuration(duration) {
    this.transitionDuration = duration;
  }

  /**
   * 获取当前转场持续时间
   */
  static getTransitionDuration() {
    return this.transitionDuration;
  }

  /**
   * 取消当前转场
   */
  static cancelCurrentTransition() {
    if (this.currentTransition) {
      this.currentTransition.cancel();
      this.currentTransition = null;
    }
  }

  /**
   * 清理所有转场相关的元素和样式
   */
  static cleanup() {
    this.cancelCurrentTransition();
    
    if (this.loadingTimeout) {
      clearTimeout(this.loadingTimeout);
      this.loadingTimeout = null;
    }

    // 移除样式
    const styleElement = document.getElementById('page-transition-styles');
    if (styleElement) {
      styleElement.remove();
    }

    // 移除加载和错误元素
    document.querySelectorAll('.page-loading-overlay, .page-loading-error').forEach(el => {
      el.remove();
    });
  }
}