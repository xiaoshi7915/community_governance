/**
 * 输入框组件
 * 实现可复用的输入框组件，支持验证和不同类型
 */
export class Input {
  constructor(options = {}) {
    this.type = options.type || 'text'; // text, password, email, tel, number, textarea
    this.placeholder = options.placeholder || '';
    this.value = options.value || '';
    this.label = options.label || '';
    this.required = options.required || false;
    this.disabled = options.disabled || false;
    this.readonly = options.readonly || false;
    this.maxLength = options.maxLength || null;
    this.minLength = options.minLength || null;
    this.pattern = options.pattern || null;
    this.rows = options.rows || 3; // for textarea
    this.className = options.className || '';
    this.validator = options.validator || null;
    this.onChange = options.onChange || null;
    this.onBlur = options.onBlur || null;
    this.onFocus = options.onFocus || null;
    this.onInput = options.onInput || null;
    
    this.container = null;
    this.inputElement = null;
    this.errorElement = null;
    this.isValid = true;
    this.errorMessage = '';
    
    // 绑定方法
    this.handleInput = this.handleInput.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleBlur = this.handleBlur.bind(this);
    this.handleFocus = this.handleFocus.bind(this);
  }

  /**
   * 创建输入框HTML结构
   */
  createInputHTML() {
    const inputId = `input-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return `
      <div class="input-group">
        ${this.label ? `
          <label for="${inputId}" class="form-label">
            ${this.label}
            ${this.required ? '<span class="text-red-500 ml-1">*</span>' : ''}
          </label>
        ` : ''}
        
        ${this.type === 'textarea' ? `
          <textarea
            id="${inputId}"
            class="input form-input ${this.className}"
            placeholder="${this.placeholder}"
            rows="${this.rows}"
            ${this.required ? 'required' : ''}
            ${this.disabled ? 'disabled' : ''}
            ${this.readonly ? 'readonly' : ''}
            ${this.maxLength ? `maxlength="${this.maxLength}"` : ''}
            ${this.minLength ? `minlength="${this.minLength}"` : ''}
          >${this.value}</textarea>
        ` : `
          <input
            id="${inputId}"
            type="${this.type}"
            class="input form-input ${this.className}"
            placeholder="${this.placeholder}"
            value="${this.value}"
            ${this.required ? 'required' : ''}
            ${this.disabled ? 'disabled' : ''}
            ${this.readonly ? 'readonly' : ''}
            ${this.maxLength ? `maxlength="${this.maxLength}"` : ''}
            ${this.minLength ? `minlength="${this.minLength}"` : ''}
            ${this.pattern ? `pattern="${this.pattern}"` : ''}
          />
        `}
        
        <div class="error-message text-sm text-red-600 mt-1 hidden"></div>
        
        ${this.maxLength ? `
          <div class="character-count text-xs text-gray-500 mt-1 text-right">
            <span class="current">0</span>/<span class="max">${this.maxLength}</span>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * 渲染输入框
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'input-wrapper';
    this.container.innerHTML = this.createInputHTML();
    
    // 获取元素引用
    this.inputElement = this.container.querySelector('.input');
    this.errorElement = this.container.querySelector('.error-message');
    
    this.bindEvents();
    this.updateCharacterCount();
    
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.inputElement) return;
    
    this.inputElement.addEventListener('input', this.handleInput);
    this.inputElement.addEventListener('change', this.handleChange);
    this.inputElement.addEventListener('blur', this.handleBlur);
    this.inputElement.addEventListener('focus', this.handleFocus);
  }

  /**
   * 处理输入事件
   */
  handleInput(e) {
    this.value = e.target.value;
    this.updateCharacterCount();
    
    // 实时验证
    if (this.validator) {
      this.validate();
    }
    
    if (this.onInput) {
      this.onInput(e, this);
    }
  }

  /**
   * 处理变化事件
   */
  handleChange(e) {
    this.value = e.target.value;
    
    if (this.onChange) {
      this.onChange(e, this);
    }
  }

  /**
   * 处理失焦事件
   */
  handleBlur(e) {
    // 失焦时进行验证
    this.validate();
    
    if (this.onBlur) {
      this.onBlur(e, this);
    }
  }

  /**
   * 处理聚焦事件
   */
  handleFocus(e) {
    // 清除错误状态
    this.clearError();
    
    if (this.onFocus) {
      this.onFocus(e, this);
    }
  }

  /**
   * 验证输入
   */
  validate() {
    let isValid = true;
    let errorMessage = '';
    
    // 必填验证
    if (this.required && !this.value.trim()) {
      isValid = false;
      errorMessage = '此字段为必填项';
    }
    
    // 长度验证
    if (isValid && this.minLength && this.value.length < this.minLength) {
      isValid = false;
      errorMessage = `最少需要${this.minLength}个字符`;
    }
    
    if (isValid && this.maxLength && this.value.length > this.maxLength) {
      isValid = false;
      errorMessage = `最多允许${this.maxLength}个字符`;
    }
    
    // 模式验证
    if (isValid && this.pattern && !new RegExp(this.pattern).test(this.value)) {
      isValid = false;
      errorMessage = '输入格式不正确';
    }
    
    // 类型验证
    if (isValid && this.value) {
      switch (this.type) {
        case 'email':
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (!emailRegex.test(this.value)) {
            isValid = false;
            errorMessage = '请输入有效的邮箱地址';
          }
          break;
        case 'tel':
          const phoneRegex = /^1[3-9]\d{9}$/;
          if (!phoneRegex.test(this.value)) {
            isValid = false;
            errorMessage = '请输入有效的手机号码';
          }
          break;
        case 'number':
          if (isNaN(this.value)) {
            isValid = false;
            errorMessage = '请输入有效的数字';
          }
          break;
      }
    }
    
    // 自定义验证器
    if (isValid && this.validator) {
      const validationResult = this.validator(this.value);
      if (validationResult !== true) {
        isValid = false;
        errorMessage = validationResult || '输入无效';
      }
    }
    
    this.isValid = isValid;
    this.errorMessage = errorMessage;
    
    if (isValid) {
      this.clearError();
    } else {
      this.showError(errorMessage);
    }
    
    return isValid;
  }

  /**
   * 显示错误
   */
  showError(message) {
    if (!this.inputElement || !this.errorElement) return;
    
    this.inputElement.classList.add('error');
    this.errorElement.textContent = message;
    this.errorElement.classList.remove('hidden');
  }

  /**
   * 清除错误
   */
  clearError() {
    if (!this.inputElement || !this.errorElement) return;
    
    this.inputElement.classList.remove('error');
    this.errorElement.textContent = '';
    this.errorElement.classList.add('hidden');
  }

  /**
   * 更新字符计数
   */
  updateCharacterCount() {
    if (!this.maxLength) return;
    
    const countElement = this.container?.querySelector('.character-count .current');
    if (countElement) {
      countElement.textContent = this.value.length;
      
      // 接近限制时改变颜色
      const countContainer = this.container.querySelector('.character-count');
      if (this.value.length > this.maxLength * 0.8) {
        countContainer.classList.add('text-yellow-600');
        countContainer.classList.remove('text-gray-500');
      } else {
        countContainer.classList.add('text-gray-500');
        countContainer.classList.remove('text-yellow-600');
      }
    }
  }

  /**
   * 获取值
   */
  getValue() {
    return this.value;
  }

  /**
   * 设置值
   */
  setValue(value) {
    this.value = value;
    
    if (this.inputElement) {
      this.inputElement.value = value;
      this.updateCharacterCount();
    }
  }

  /**
   * 设置占位符
   */
  setPlaceholder(placeholder) {
    this.placeholder = placeholder;
    
    if (this.inputElement) {
      this.inputElement.placeholder = placeholder;
    }
  }

  /**
   * 设置禁用状态
   */
  setDisabled(disabled = true) {
    this.disabled = disabled;
    
    if (this.inputElement) {
      this.inputElement.disabled = disabled;
    }
  }

  /**
   * 设置只读状态
   */
  setReadonly(readonly = true) {
    this.readonly = readonly;
    
    if (this.inputElement) {
      this.inputElement.readonly = readonly;
    }
  }

  /**
   * 聚焦
   */
  focus() {
    if (this.inputElement) {
      this.inputElement.focus();
    }
  }

  /**
   * 失焦
   */
  blur() {
    if (this.inputElement) {
      this.inputElement.blur();
    }
  }

  /**
   * 选中文本
   */
  select() {
    if (this.inputElement) {
      this.inputElement.select();
    }
  }

  /**
   * 获取验证状态
   */
  getValidationState() {
    return {
      isValid: this.isValid,
      errorMessage: this.errorMessage
    };
  }

  /**
   * 重置
   */
  reset() {
    this.setValue('');
    this.clearError();
    this.isValid = true;
    this.errorMessage = '';
  }

  /**
   * 获取DOM元素
   */
  getElement() {
    return this.container;
  }

  /**
   * 获取输入元素
   */
  getInputElement() {
    return this.inputElement;
  }

  /**
   * 销毁组件
   */
  destroy() {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.container = null;
    this.inputElement = null;
    this.errorElement = null;
    this.onChange = null;
    this.onBlur = null;
    this.onFocus = null;
    this.onInput = null;
    this.validator = null;
  }
}