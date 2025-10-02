/**
 * 选择器组件
 * 实现可复用的下拉选择组件
 */
export class Select {
  constructor(options = {}) {
    this.options = options.options || []; // [{value, label, disabled}]
    this.value = options.value || '';
    this.placeholder = options.placeholder || '请选择';
    this.label = options.label || '';
    this.required = options.required || false;
    this.disabled = options.disabled || false;
    this.multiple = options.multiple || false;
    this.searchable = options.searchable || false;
    this.clearable = options.clearable || false;
    this.className = options.className || '';
    this.onChange = options.onChange || null;
    this.onSearch = options.onSearch || null;
    
    this.container = null;
    this.selectElement = null;
    this.dropdownElement = null;
    this.searchInput = null;
    this.isOpen = false;
    this.filteredOptions = [...this.options];
    this.selectedValues = this.multiple ? (Array.isArray(this.value) ? this.value : []) : [];
    
    // 绑定方法
    this.handleToggle = this.handleToggle.bind(this);
    this.handleOptionClick = this.handleOptionClick.bind(this);
    this.handleSearch = this.handleSearch.bind(this);
    this.handleClickOutside = this.handleClickOutside.bind(this);
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }

  /**
   * 获取选中项的显示文本
   */
  getDisplayText() {
    if (this.multiple) {
      if (this.selectedValues.length === 0) {
        return this.placeholder;
      }
      if (this.selectedValues.length === 1) {
        const option = this.options.find(opt => opt.value === this.selectedValues[0]);
        return option ? option.label : this.selectedValues[0];
      }
      return `已选择 ${this.selectedValues.length} 项`;
    } else {
      if (!this.value) {
        return this.placeholder;
      }
      const option = this.options.find(opt => opt.value === this.value);
      return option ? option.label : this.value;
    }
  }

  /**
   * 创建选择器HTML结构
   */
  createSelectHTML() {
    const selectId = `select-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return `
      <div class="select-group">
        ${this.label ? `
          <label for="${selectId}" class="form-label">
            ${this.label}
            ${this.required ? '<span class="text-red-500 ml-1">*</span>' : ''}
          </label>
        ` : ''}
        
        <div class="select-container relative">
          <div 
            id="${selectId}"
            class="select-trigger form-input cursor-pointer flex items-center justify-between ${this.className} ${this.disabled ? 'opacity-50 cursor-not-allowed' : ''}"
            tabindex="${this.disabled ? -1 : 0}"
          >
            <span class="select-text ${!this.value && !this.selectedValues.length ? 'text-gray-500' : ''}">${this.getDisplayText()}</span>
            <svg class="select-arrow w-5 h-5 text-gray-400 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
          
          <div class="select-dropdown absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 hidden max-h-60 overflow-y-auto">
            ${this.searchable ? `
              <div class="search-container p-2 border-b border-gray-100">
                <input 
                  type="text" 
                  class="search-input w-full px-3 py-2 text-sm border border-gray-200 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  placeholder="搜索选项..."
                />
              </div>
            ` : ''}
            
            <div class="options-container">
              ${this.renderOptions()}
            </div>
          </div>
        </div>
        
        ${this.multiple && this.selectedValues.length > 0 ? `
          <div class="selected-tags flex flex-wrap gap-2 mt-2">
            ${this.selectedValues.map(value => {
              const option = this.options.find(opt => opt.value === value);
              return `
                <span class="tag inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                  ${option ? option.label : value}
                  <button class="tag-remove ml-1 text-blue-600 hover:text-blue-800" data-value="${value}">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </span>
              `;
            }).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * 渲染选项
   */
  renderOptions() {
    if (this.filteredOptions.length === 0) {
      return '<div class="option-item px-3 py-2 text-gray-500 text-center">无匹配选项</div>';
    }
    
    return this.filteredOptions.map(option => {
      const isSelected = this.multiple 
        ? this.selectedValues.includes(option.value)
        : this.value === option.value;
      
      return `
        <div 
          class="option-item px-3 py-2 cursor-pointer hover:bg-gray-50 flex items-center justify-between ${isSelected ? 'bg-blue-50 text-blue-600' : ''} ${option.disabled ? 'opacity-50 cursor-not-allowed' : ''}"
          data-value="${option.value}"
          ${option.disabled ? 'data-disabled="true"' : ''}
        >
          <span>${option.label}</span>
          ${isSelected ? `
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          ` : ''}
        </div>
      `;
    }).join('');
  }

  /**
   * 渲染选择器
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'select-wrapper';
    this.container.innerHTML = this.createSelectHTML();
    
    // 获取元素引用
    this.selectElement = this.container.querySelector('.select-trigger');
    this.dropdownElement = this.container.querySelector('.select-dropdown');
    this.searchInput = this.container.querySelector('.search-input');
    
    this.bindEvents();
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.selectElement || !this.dropdownElement) return;
    
    // 选择器点击事件
    this.selectElement.addEventListener('click', this.handleToggle);
    this.selectElement.addEventListener('keydown', this.handleKeyDown);
    
    // 选项点击事件
    this.dropdownElement.addEventListener('click', this.handleOptionClick);
    
    // 搜索输入事件
    if (this.searchInput) {
      this.searchInput.addEventListener('input', this.handleSearch);
    }
    
    // 标签移除事件
    if (this.multiple) {
      this.container.addEventListener('click', (e) => {
        if (e.target.closest('.tag-remove')) {
          const value = e.target.closest('.tag-remove').dataset.value;
          this.removeValue(value);
        }
      });
    }
    
    // 点击外部关闭
    document.addEventListener('click', this.handleClickOutside);
  }

  /**
   * 处理切换显示/隐藏
   */
  handleToggle(e) {
    if (this.disabled) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  /**
   * 处理选项点击
   */
  handleOptionClick(e) {
    const optionElement = e.target.closest('.option-item');
    if (!optionElement || optionElement.dataset.disabled === 'true') return;
    
    const value = optionElement.dataset.value;
    
    if (this.multiple) {
      if (this.selectedValues.includes(value)) {
        this.removeValue(value);
      } else {
        this.addValue(value);
      }
    } else {
      this.setValue(value);
      this.close();
    }
  }

  /**
   * 处理搜索
   */
  handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    
    this.filteredOptions = this.options.filter(option => 
      option.label.toLowerCase().includes(searchTerm) ||
      option.value.toLowerCase().includes(searchTerm)
    );
    
    this.updateOptions();
    
    if (this.onSearch) {
      this.onSearch(searchTerm, this);
    }
  }

  /**
   * 处理点击外部
   */
  handleClickOutside(e) {
    if (!this.container.contains(e.target)) {
      this.close();
    }
  }

  /**
   * 处理键盘事件
   */
  handleKeyDown(e) {
    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        this.handleToggle(e);
        break;
      case 'Escape':
        this.close();
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (!this.isOpen) {
          this.open();
        }
        // TODO: 实现键盘导航
        break;
      case 'ArrowUp':
        e.preventDefault();
        // TODO: 实现键盘导航
        break;
    }
  }

  /**
   * 打开下拉框
   */
  open() {
    if (this.disabled || this.isOpen) return;
    
    this.isOpen = true;
    this.dropdownElement.classList.remove('hidden');
    
    // 旋转箭头
    const arrow = this.selectElement.querySelector('.select-arrow');
    if (arrow) {
      arrow.style.transform = 'rotate(180deg)';
    }
    
    // 聚焦搜索框
    if (this.searchInput) {
      setTimeout(() => this.searchInput.focus(), 100);
    }
    
    // 添加动画
    this.dropdownElement.style.animation = 'slideDown 0.2s ease-out';
  }

  /**
   * 关闭下拉框
   */
  close() {
    if (!this.isOpen) return;
    
    this.isOpen = false;
    this.dropdownElement.classList.add('hidden');
    
    // 重置箭头
    const arrow = this.selectElement.querySelector('.select-arrow');
    if (arrow) {
      arrow.style.transform = '';
    }
    
    // 清空搜索
    if (this.searchInput) {
      this.searchInput.value = '';
      this.filteredOptions = [...this.options];
      this.updateOptions();
    }
  }

  /**
   * 设置值
   */
  setValue(value) {
    this.value = value;
    this.updateDisplay();
    
    if (this.onChange) {
      this.onChange(value, this);
    }
  }

  /**
   * 添加值（多选）
   */
  addValue(value) {
    if (!this.multiple || this.selectedValues.includes(value)) return;
    
    this.selectedValues.push(value);
    this.updateDisplay();
    this.updateTags();
    
    if (this.onChange) {
      this.onChange([...this.selectedValues], this);
    }
  }

  /**
   * 移除值（多选）
   */
  removeValue(value) {
    if (!this.multiple) return;
    
    const index = this.selectedValues.indexOf(value);
    if (index > -1) {
      this.selectedValues.splice(index, 1);
      this.updateDisplay();
      this.updateTags();
      
      if (this.onChange) {
        this.onChange([...this.selectedValues], this);
      }
    }
  }

  /**
   * 更新显示
   */
  updateDisplay() {
    const textElement = this.selectElement?.querySelector('.select-text');
    if (textElement) {
      const displayText = this.getDisplayText();
      textElement.textContent = displayText;
      
      // 更新占位符样式
      if (!this.value && !this.selectedValues.length) {
        textElement.classList.add('text-gray-500');
      } else {
        textElement.classList.remove('text-gray-500');
      }
    }
    
    this.updateOptions();
  }

  /**
   * 更新选项显示
   */
  updateOptions() {
    const optionsContainer = this.dropdownElement?.querySelector('.options-container');
    if (optionsContainer) {
      optionsContainer.innerHTML = this.renderOptions();
    }
  }

  /**
   * 更新标签显示（多选）
   */
  updateTags() {
    if (!this.multiple) return;
    
    const existingTags = this.container.querySelector('.selected-tags');
    if (existingTags) {
      existingTags.remove();
    }
    
    if (this.selectedValues.length > 0) {
      const tagsHTML = `
        <div class="selected-tags flex flex-wrap gap-2 mt-2">
          ${this.selectedValues.map(value => {
            const option = this.options.find(opt => opt.value === value);
            return `
              <span class="tag inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                ${option ? option.label : value}
                <button class="tag-remove ml-1 text-blue-600 hover:text-blue-800" data-value="${value}">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </span>
            `;
          }).join('')}
        </div>
      `;
      
      this.container.querySelector('.select-group').insertAdjacentHTML('beforeend', tagsHTML);
    }
  }

  /**
   * 更新选项
   */
  updateOptions(newOptions) {
    this.options = newOptions;
    this.filteredOptions = [...newOptions];
    this.updateDisplay();
  }

  /**
   * 获取值
   */
  getValue() {
    return this.multiple ? [...this.selectedValues] : this.value;
  }

  /**
   * 清空选择
   */
  clear() {
    if (this.multiple) {
      this.selectedValues = [];
    } else {
      this.value = '';
    }
    this.updateDisplay();
    this.updateTags();
    
    if (this.onChange) {
      this.onChange(this.getValue(), this);
    }
  }

  /**
   * 设置禁用状态
   */
  setDisabled(disabled = true) {
    this.disabled = disabled;
    
    if (this.selectElement) {
      if (disabled) {
        this.selectElement.classList.add('opacity-50', 'cursor-not-allowed');
        this.selectElement.tabIndex = -1;
      } else {
        this.selectElement.classList.remove('opacity-50', 'cursor-not-allowed');
        this.selectElement.tabIndex = 0;
      }
    }
  }

  /**
   * 获取DOM元素
   */
  getElement() {
    return this.container;
  }

  /**
   * 销毁组件
   */
  destroy() {
    document.removeEventListener('click', this.handleClickOutside);
    
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.container = null;
    this.selectElement = null;
    this.dropdownElement = null;
    this.searchInput = null;
    this.onChange = null;
    this.onSearch = null;
  }
}