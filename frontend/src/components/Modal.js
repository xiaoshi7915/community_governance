/**
 * 模态框组件
 * 实现通用模态框，支持自定义内容和操作按钮
 */
export class Modal {
  constructor(options = {}) {
    this.title = options.title || '';
    this.content = options.content || '';
    this.actions = options.actions || [];
    this.closable = options.closable !== false;
    this.maskClosable = options.maskClosable !== false;
    this.className = options.className || '';
    this.onClose = options.onClose || null;
    this.onShow = options.onShow || null;
    
    this.container = null;
    this.isVisible = false;
    this.isAnimating = false;
    
    // 绑定方法
    this.handleMaskClick = this.handleMaskClick.bind(this);
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }

  /**
   * 创建模态框HTML结构
   */
  createModalHTML() {
    return `
      <div class="modal-overlay" role="dialog" aria-modal="true" ${this.title ? `aria-labelledby="modal-title"` : ''}>
        <div class="modal-dialog ${this.className}">
          ${this.title ? `
            <div class="modal-header flex items-center justify-between mb-6">
              <h2 id="modal-title" class="text-xl font-semibold text-gray-900">${this.title}</h2>
              ${this.closable ? `
                <button class="modal-close p-2 hover:bg-gray-100 rounded-full transition-colors" aria-label="关闭">
                  <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              ` : ''}
            </div>
          ` : ''}
          
          <div class="modal-body">
            ${typeof this.content === 'string' ? this.content : ''}
          </div>
          
          ${this.actions.length > 0 ? `
            <div class="modal-footer flex space-x-3 mt-6">
              ${this.actions.map(action => `
                <button 
                  class="modal-action flex-1 ${action.className || 'btn-primary'}" 
                  data-action="${action.key || ''}"
                  ${action.disabled ? 'disabled' : ''}
                >
                  ${action.loading ? `
                    <div class="loading-spinner mr-2"></div>
                  ` : ''}
                  ${action.label}
                </button>
              `).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * 渲染模态框
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'modal fixed inset-0 z-50 hidden';
    this.container.innerHTML = this.createModalHTML();
    
    // 如果content是DOM元素，替换内容
    if (this.content && typeof this.content === 'object' && this.content.nodeType) {
      const modalBody = this.container.querySelector('.modal-body');
      modalBody.innerHTML = '';
      modalBody.appendChild(this.content);
    }
    
    this.bindEvents();
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.container) return;
    
    // 关闭按钮事件
    const closeBtn = this.container.querySelector('.modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hide());
    }
    
    // 遮罩点击事件
    const overlay = this.container.querySelector('.modal-overlay');
    if (overlay && this.maskClosable) {
      overlay.addEventListener('click', this.handleMaskClick);
    }
    
    // 操作按钮事件
    const actionBtns = this.container.querySelectorAll('.modal-action');
    actionBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const actionKey = e.target.dataset.action;
        const action = this.actions.find(a => a.key === actionKey);
        if (action && action.handler) {
          action.handler(this);
        }
      });
    });
  }

  /**
   * 处理遮罩点击
   */
  handleMaskClick(e) {
    if (e.target === e.currentTarget) {
      this.hide();
    }
  }

  /**
   * 处理键盘事件
   */
  handleKeyDown(e) {
    if (e.key === 'Escape' && this.closable) {
      this.hide();
    }
  }

  /**
   * 显示模态框
   */
  show() {
    if (this.isVisible || this.isAnimating) return Promise.resolve();
    
    return new Promise((resolve) => {
      if (!this.container) {
        this.render();
      }
      
      // 添加到DOM
      document.body.appendChild(this.container);
      
      // 添加键盘事件监听
      document.addEventListener('keydown', this.handleKeyDown);
      
      // 防止背景滚动
      document.body.style.overflow = 'hidden';
      
      this.isAnimating = true;
      
      // 显示动画
      requestAnimationFrame(() => {
        this.container.classList.remove('hidden');
        this.container.classList.add('show');
        
        const dialog = this.container.querySelector('.modal-dialog');
        if (dialog) {
          dialog.style.animation = 'slideUp 0.3s ease-out';
        }
        
        setTimeout(() => {
          this.isVisible = true;
          this.isAnimating = false;
          
          // 触发显示回调
          if (this.onShow) {
            this.onShow(this);
          }
          
          resolve();
        }, 300);
      });
    });
  }

  /**
   * 隐藏模态框
   */
  hide() {
    if (!this.isVisible || this.isAnimating) return Promise.resolve();
    
    return new Promise((resolve) => {
      this.isAnimating = true;
      
      const dialog = this.container.querySelector('.modal-dialog');
      if (dialog) {
        dialog.style.animation = 'slideDown 0.3s ease-out';
      }
      
      this.container.classList.add('hide');
      
      setTimeout(() => {
        this.container.classList.add('hidden');
        this.container.classList.remove('show', 'hide');
        
        // 移除键盘事件监听
        document.removeEventListener('keydown', this.handleKeyDown);
        
        // 恢复背景滚动
        document.body.style.overflow = '';
        
        // 从DOM移除
        if (this.container.parentNode) {
          this.container.parentNode.removeChild(this.container);
        }
        
        this.isVisible = false;
        this.isAnimating = false;
        
        // 触发关闭回调
        if (this.onClose) {
          this.onClose(this);
        }
        
        resolve();
      }, 300);
    });
  }

  /**
   * 更新内容
   */
  updateContent(content) {
    this.content = content;
    
    if (this.container) {
      const modalBody = this.container.querySelector('.modal-body');
      if (modalBody) {
        if (typeof content === 'string') {
          modalBody.innerHTML = content;
        } else if (content && content.nodeType) {
          modalBody.innerHTML = '';
          modalBody.appendChild(content);
        }
      }
    }
  }

  /**
   * 更新标题
   */
  updateTitle(title) {
    this.title = title;
    
    if (this.container) {
      const titleElement = this.container.querySelector('#modal-title');
      if (titleElement) {
        titleElement.textContent = title;
      }
    }
  }

  /**
   * 更新操作按钮
   */
  updateActions(actions) {
    this.actions = actions;
    
    if (this.container) {
      const footer = this.container.querySelector('.modal-footer');
      if (footer) {
        footer.innerHTML = `
          <div class="flex space-x-3">
            ${actions.map(action => `
              <button 
                class="modal-action flex-1 ${action.className || 'btn-primary'}" 
                data-action="${action.key || ''}"
                ${action.disabled ? 'disabled' : ''}
              >
                ${action.loading ? `<div class="loading-spinner mr-2"></div>` : ''}
                ${action.label}
              </button>
            `).join('')}
          </div>
        `;
        
        // 重新绑定事件
        this.bindActionEvents();
      }
    }
  }

  /**
   * 绑定操作按钮事件
   */
  bindActionEvents() {
    const actionBtns = this.container.querySelectorAll('.modal-action');
    actionBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const actionKey = e.target.dataset.action;
        const action = this.actions.find(a => a.key === actionKey);
        if (action && action.handler) {
          action.handler(this);
        }
      });
    });
  }

  /**
   * 设置加载状态
   */
  setLoading(actionKey, loading = true) {
    const action = this.actions.find(a => a.key === actionKey);
    if (action) {
      action.loading = loading;
      
      if (this.container) {
        const btn = this.container.querySelector(`[data-action="${actionKey}"]`);
        if (btn) {
          if (loading) {
            btn.disabled = true;
            btn.innerHTML = `
              <div class="loading-spinner mr-2"></div>
              ${action.label}
            `;
          } else {
            btn.disabled = action.disabled || false;
            btn.innerHTML = action.label;
          }
        }
      }
    }
  }

  /**
   * 销毁模态框
   */
  destroy() {
    if (this.isVisible) {
      this.hide();
    }
    
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    document.removeEventListener('keydown', this.handleKeyDown);
    document.body.style.overflow = '';
    
    this.container = null;
    this.onClose = null;
    this.onShow = null;
  }

  /**
   * 静态方法：创建确认对话框
   */
  static confirm(options = {}) {
    const modal = new Modal({
      title: options.title || '确认',
      content: options.content || '确定要执行此操作吗？',
      actions: [
        {
          key: 'cancel',
          label: '取消',
          className: 'btn-secondary',
          handler: (modal) => {
            modal.hide();
            if (options.onCancel) options.onCancel();
          }
        },
        {
          key: 'confirm',
          label: '确定',
          className: 'btn-primary',
          handler: (modal) => {
            if (options.onConfirm) {
              const result = options.onConfirm();
              if (result !== false) {
                modal.hide();
              }
            } else {
              modal.hide();
            }
          }
        }
      ]
    });
    
    modal.show();
    return modal;
  }

  /**
   * 静态方法：创建警告对话框
   */
  static alert(options = {}) {
    const modal = new Modal({
      title: options.title || '提示',
      content: options.content || '',
      actions: [
        {
          key: 'ok',
          label: '确定',
          className: 'btn-primary',
          handler: (modal) => {
            modal.hide();
            if (options.onOk) options.onOk();
          }
        }
      ]
    });
    
    modal.show();
    return modal;
  }
}