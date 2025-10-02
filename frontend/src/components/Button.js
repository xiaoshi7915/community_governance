/**
 * 按钮组件
 * 实现可复用的按钮组件，支持不同类型和状态
 */
export class Button {
  constructor(options = {}) {
    this.text = options.text || '';
    this.type = options.type || 'primary'; // primary, secondary, success, danger
    this.size = options.size || 'medium'; // small, medium, large
    this.disabled = options.disabled || false;
    this.loading = options.loading || false;
    this.icon = options.icon || null;
    this.iconPosition = options.iconPosition || 'left'; // left, right
    this.className = options.className || '';
    this.onClick = options.onClick || null;
    
    this.container = null;
    
    // 绑定方法
    this.handleClick = this.handleClick.bind(this);
  }

  /**
   * 获取按钮类型样式
   */
  getTypeClass() {
    const typeClasses = {
      primary: 'button primary',
      secondary: 'button secondary',
      success: 'button success',
      danger: 'button danger'
    };
    return typeClasses[this.type] || typeClasses.primary;
  }

  /**
   * 获取按钮尺寸样式
   */
  getSizeClass() {
    const sizeClasses = {
      small: 'px-3 py-2 text-sm',
      medium: 'px-4 py-3',
      large: 'px-6 py-4 text-lg'
    };
    return sizeClasses[this.size] || sizeClasses.medium;
  }

  /**
   * 获取图标HTML
   */
  getIconHTML() {
    if (!this.icon) return '';
    
    if (typeof this.icon === 'string') {
      // 如果是字符串，假设是SVG
      return this.icon;
    }
    
    // 预定义图标
    const icons = {
      loading: `<div class="loading-spinner w-4 h-4"></div>`,
      plus: `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
      </svg>`,
      check: `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
      </svg>`,
      x: `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>`,
      upload: `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
      </svg>`
    };
    
    return icons[this.icon] || '';
  }

  /**
   * 创建按钮HTML结构
   */
  createButtonHTML() {
    const iconHTML = this.loading ? this.getIconHTML('loading') : this.getIconHTML();
    const hasIcon = iconHTML && !this.loading;
    const hasText = this.text && this.text.trim();
    
    let content = '';
    
    if (this.loading) {
      content = `
        <div class="loading-spinner w-4 h-4 mr-2"></div>
        <span>加载中...</span>
      `;
    } else if (hasIcon && hasText) {
      if (this.iconPosition === 'right') {
        content = `
          <span>${this.text}</span>
          <span class="ml-2">${iconHTML}</span>
        `;
      } else {
        content = `
          <span class="mr-2">${iconHTML}</span>
          <span>${this.text}</span>
        `;
      }
    } else if (hasIcon) {
      content = iconHTML;
    } else {
      content = `<span>${this.text}</span>`;
    }
    
    return content;
  }

  /**
   * 渲染按钮
   */
  render() {
    this.container = document.createElement('button');
    this.container.className = `${this.getTypeClass()} ${this.getSizeClass()} ${this.className}`.trim();
    this.container.innerHTML = this.createButtonHTML();
    
    // 设置属性
    if (this.disabled || this.loading) {
      this.container.disabled = true;
    }
    
    if (this.loading) {
      this.container.classList.add('loading');
    }
    
    this.bindEvents();
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.container) return;
    
    this.container.addEventListener('click', this.handleClick);
  }

  /**
   * 处理点击事件
   */
  handleClick(e) {
    if (this.disabled || this.loading) {
      e.preventDefault();
      return;
    }
    
    // 添加点击动画
    this.animateClick();
    
    if (this.onClick) {
      this.onClick(e, this);
    }
  }

  /**
   * 点击动画
   */
  animateClick() {
    if (!this.container) return;
    
    this.container.style.transform = 'scale(0.95)';
    this.container.style.transition = 'transform 0.1s ease-out';
    
    setTimeout(() => {
      if (this.container) {
        this.container.style.transform = '';
        this.container.style.transition = '';
      }
    }, 100);
  }

  /**
   * 设置加载状态
   */
  setLoading(loading = true) {
    this.loading = loading;
    
    if (this.container) {
      if (loading) {
        this.container.disabled = true;
        this.container.classList.add('loading');
        this.container.innerHTML = `
          <div class="loading-spinner w-4 h-4 mr-2"></div>
          <span>加载中...</span>
        `;
      } else {
        this.container.disabled = this.disabled;
        this.container.classList.remove('loading');
        this.container.innerHTML = this.createButtonHTML();
      }
    }
  }

  /**
   * 设置禁用状态
   */
  setDisabled(disabled = true) {
    this.disabled = disabled;
    
    if (this.container) {
      this.container.disabled = disabled || this.loading;
    }
  }

  /**
   * 更新文本
   */
  setText(text) {
    this.text = text;
    
    if (this.container && !this.loading) {
      this.container.innerHTML = this.createButtonHTML();
    }
  }

  /**
   * 更新图标
   */
  setIcon(icon) {
    this.icon = icon;
    
    if (this.container && !this.loading) {
      this.container.innerHTML = this.createButtonHTML();
    }
  }

  /**
   * 更新类型
   */
  setType(type) {
    if (this.container) {
      // 移除旧的类型类
      this.container.classList.remove('primary', 'secondary', 'success', 'danger');
    }
    
    this.type = type;
    
    if (this.container) {
      // 添加新的类型类
      this.container.className = `${this.getTypeClass()} ${this.getSizeClass()} ${this.className}`.trim();
    }
  }

  /**
   * 获取DOM元素
   */
  getElement() {
    return this.container;
  }

  /**
   * 销毁按钮
   */
  destroy() {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.container = null;
    this.onClick = null;
  }
}