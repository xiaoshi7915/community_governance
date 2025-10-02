/**
 * 文件上传组件
 * 实现图片上传和预览，支持拖拽上传和进度显示
 */
export class FileUpload {
  constructor(options = {}) {
    this.accept = options.accept || 'image/*,video/*';
    this.multiple = options.multiple || false;
    this.maxSize = options.maxSize || 10 * 1024 * 1024; // 10MB
    this.maxFiles = options.maxFiles || 5;
    this.compress = options.compress !== false;
    this.quality = options.quality || 0.8;
    this.maxWidth = options.maxWidth || 1920;
    this.maxHeight = options.maxHeight || 1080;
    this.className = options.className || '';
    this.placeholder = options.placeholder || '点击或拖拽文件到此处';
    this.hint = options.hint || '支持图片和视频文件';
    this.onFileSelect = options.onFileSelect || null;
    this.onUploadProgress = options.onUploadProgress || null;
    this.onUploadComplete = options.onUploadComplete || null;
    this.onError = options.onError || null;
    
    this.container = null;
    this.fileInput = null;
    this.uploadArea = null;
    this.previewArea = null;
    this.files = [];
    this.isUploading = false;
    
    // 绑定方法
    this.handleFileSelect = this.handleFileSelect.bind(this);
    this.handleDragOver = this.handleDragOver.bind(this);
    this.handleDragLeave = this.handleDragLeave.bind(this);
    this.handleDrop = this.handleDrop.bind(this);
    this.handleClick = this.handleClick.bind(this);
  }

  /**
   * 创建上传组件HTML结构
   */
  createUploadHTML() {
    return `
      <div class="file-upload-container">
        <div class="file-upload ${this.className}" tabindex="0">
          <div class="file-upload-content">
            <div class="file-upload-icon">
              <svg class="w-16 h-16 text-blue-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
              </svg>
            </div>
            <p class="file-upload-text">${this.placeholder}</p>
            <p class="file-upload-hint">${this.hint}</p>
          </div>
          
          <input 
            type="file" 
            class="file-input hidden" 
            accept="${this.accept}"
            ${this.multiple ? 'multiple' : ''}
          />
        </div>
        
        <div class="file-preview-area mt-4 hidden">
          <div class="preview-grid grid grid-cols-2 gap-4"></div>
        </div>
        
        <div class="upload-progress mt-4 hidden">
          <div class="progress-bar bg-gray-200 rounded-full h-2">
            <div class="progress-fill bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
          </div>
          <div class="progress-text text-sm text-gray-600 mt-2 text-center">上传中... 0%</div>
        </div>
      </div>
    `;
  }

  /**
   * 渲染上传组件
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'file-upload-wrapper';
    this.container.innerHTML = this.createUploadHTML();
    
    // 获取元素引用
    this.fileInput = this.container.querySelector('.file-input');
    this.uploadArea = this.container.querySelector('.file-upload');
    this.previewArea = this.container.querySelector('.file-preview-area');
    
    this.bindEvents();
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.fileInput || !this.uploadArea) return;
    
    // 文件选择事件
    this.fileInput.addEventListener('change', this.handleFileSelect);
    
    // 拖拽事件
    this.uploadArea.addEventListener('dragover', this.handleDragOver);
    this.uploadArea.addEventListener('dragleave', this.handleDragLeave);
    this.uploadArea.addEventListener('drop', this.handleDrop);
    
    // 点击事件
    this.uploadArea.addEventListener('click', this.handleClick);
    
    // 键盘事件
    this.uploadArea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.handleClick();
      }
    });
  }

  /**
   * 处理文件选择
   */
  handleFileSelect(e) {
    const files = Array.from(e.target.files);
    this.processFiles(files);
  }

  /**
   * 处理拖拽悬停
   */
  handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.uploadArea.classList.add('dragover');
  }

  /**
   * 处理拖拽离开
   */
  handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.uploadArea.classList.remove('dragover');
  }

  /**
   * 处理文件拖放
   */
  handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.uploadArea.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    this.processFiles(files);
  }

  /**
   * 处理点击事件
   */
  handleClick() {
    if (this.isUploading) return;
    this.fileInput.click();
  }

  /**
   * 处理文件
   */
  async processFiles(files) {
    if (!files.length) return;
    
    // 验证文件
    const validFiles = [];
    for (const file of files) {
      const validation = this.validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        this.showError(validation.error);
      }
    }
    
    if (!validFiles.length) return;
    
    // 检查文件数量限制
    if (!this.multiple && validFiles.length > 1) {
      this.showError('只能选择一个文件');
      return;
    }
    
    if (this.files.length + validFiles.length > this.maxFiles) {
      this.showError(`最多只能上传${this.maxFiles}个文件`);
      return;
    }
    
    // 处理文件
    for (const file of validFiles) {
      try {
        const processedFile = await this.processFile(file);
        this.addFile(processedFile);
      } catch (error) {
        this.showError(`处理文件失败: ${error.message}`);
      }
    }
    
    this.updatePreview();
    
    if (this.onFileSelect) {
      this.onFileSelect(this.files, this);
    }
  }

  /**
   * 验证文件
   */
  validateFile(file) {
    // 检查文件大小
    if (file.size > this.maxSize) {
      return {
        valid: false,
        error: `文件大小不能超过${this.formatFileSize(this.maxSize)}`
      };
    }
    
    // 检查文件类型
    const acceptTypes = this.accept.split(',').map(type => type.trim());
    const isValidType = acceptTypes.some(type => {
      if (type === '*/*') return true;
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type || file.name.toLowerCase().endsWith(type.slice(1));
    });
    
    if (!isValidType) {
      return {
        valid: false,
        error: '不支持的文件类型'
      };
    }
    
    return { valid: true };
  }

  /**
   * 处理单个文件
   */
  async processFile(file) {
    const fileData = {
      id: Date.now() + Math.random(),
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      url: null,
      thumbnail: null,
      compressed: null
    };
    
    // 创建预览URL
    fileData.url = URL.createObjectURL(file);
    
    // 如果是图片，创建缩略图和压缩版本
    if (file.type.startsWith('image/')) {
      try {
        fileData.thumbnail = await this.createThumbnail(file);
        if (this.compress) {
          fileData.compressed = await this.compressImage(file);
        }
      } catch (error) {
        console.warn('创建缩略图或压缩失败:', error);
      }
    }
    
    return fileData;
  }

  /**
   * 创建缩略图
   */
  createThumbnail(file, size = 200) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      img.onload = () => {
        // 计算缩略图尺寸
        let { width, height } = img;
        if (width > height) {
          if (width > size) {
            height = (height * size) / width;
            width = size;
          }
        } else {
          if (height > size) {
            width = (width * size) / height;
            height = size;
          }
        }
        
        canvas.width = width;
        canvas.height = height;
        
        // 绘制缩略图
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob(resolve, 'image/jpeg', 0.8);
      };
      
      img.onerror = reject;
      img.src = URL.createObjectURL(file);
    });
  }

  /**
   * 压缩图片
   */
  compressImage(file) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      img.onload = () => {
        let { width, height } = img;
        
        // 计算压缩后尺寸
        if (width > this.maxWidth || height > this.maxHeight) {
          const ratio = Math.min(this.maxWidth / width, this.maxHeight / height);
          width *= ratio;
          height *= ratio;
        }
        
        canvas.width = width;
        canvas.height = height;
        
        // 绘制压缩图片
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob(resolve, file.type, this.quality);
      };
      
      img.onerror = reject;
      img.src = URL.createObjectURL(file);
    });
  }

  /**
   * 添加文件
   */
  addFile(fileData) {
    this.files.push(fileData);
  }

  /**
   * 移除文件
   */
  removeFile(fileId) {
    const index = this.files.findIndex(f => f.id === fileId);
    if (index > -1) {
      const file = this.files[index];
      
      // 清理URL
      if (file.url) URL.revokeObjectURL(file.url);
      if (file.thumbnail) URL.revokeObjectURL(file.thumbnail);
      if (file.compressed) URL.revokeObjectURL(file.compressed);
      
      this.files.splice(index, 1);
      this.updatePreview();
      
      if (this.onFileSelect) {
        this.onFileSelect(this.files, this);
      }
    }
  }

  /**
   * 更新预览
   */
  updatePreview() {
    if (!this.previewArea) return;
    
    const previewGrid = this.previewArea.querySelector('.preview-grid');
    
    if (this.files.length === 0) {
      this.previewArea.classList.add('hidden');
      return;
    }
    
    this.previewArea.classList.remove('hidden');
    
    previewGrid.innerHTML = this.files.map(file => {
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');
      
      return `
        <div class="media-preview relative" data-file-id="${file.id}">
          ${isImage ? `
            <img 
              src="${file.thumbnail || file.url}" 
              alt="${file.name}"
              class="media-preview-image w-full h-32 object-cover rounded-lg"
            />
          ` : isVideo ? `
            <video 
              src="${file.url}" 
              class="media-preview-image w-full h-32 object-cover rounded-lg"
              muted
            ></video>
            <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded-lg">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h8a2 2 0 012 2v8a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2z"></path>
              </svg>
            </div>
          ` : `
            <div class="media-preview-image w-full h-32 bg-gray-100 rounded-lg flex items-center justify-center">
              <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
          `}
          
          <button 
            class="media-preview-remove absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
            onclick="this.closest('.file-upload-wrapper').fileUpload.removeFile('${file.id}')"
          >×</button>
          
          <div class="file-info mt-2">
            <p class="text-xs text-gray-600 truncate" title="${file.name}">${file.name}</p>
            <p class="text-xs text-gray-500">${this.formatFileSize(file.size)}</p>
          </div>
        </div>
      `;
    }).join('');
    
    // 保存引用以便移除文件时调用
    this.container.fileUpload = this;
  }

  /**
   * 上传文件
   */
  async uploadFiles(uploadUrl, options = {}) {
    if (this.isUploading || !this.files.length) return;
    
    this.isUploading = true;
    this.showProgress(0);
    
    try {
      const results = [];
      
      for (let i = 0; i < this.files.length; i++) {
        const file = this.files[i];
        const fileToUpload = file.compressed || file.file;
        
        const result = await this.uploadSingleFile(fileToUpload, uploadUrl, {
          ...options,
          onProgress: (progress) => {
            const totalProgress = ((i / this.files.length) + (progress / 100 / this.files.length)) * 100;
            this.showProgress(totalProgress);
            
            if (this.onUploadProgress) {
              this.onUploadProgress(totalProgress, i + 1, this.files.length);
            }
          }
        });
        
        results.push(result);
      }
      
      this.hideProgress();
      this.isUploading = false;
      
      if (this.onUploadComplete) {
        this.onUploadComplete(results, this);
      }
      
      return results;
    } catch (error) {
      this.hideProgress();
      this.isUploading = false;
      this.showError(`上传失败: ${error.message}`);
      throw error;
    }
  }

  /**
   * 上传单个文件
   */
  uploadSingleFile(file, url, options = {}) {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);
      
      // 添加额外参数
      if (options.data) {
        Object.keys(options.data).forEach(key => {
          formData.append(key, options.data[key]);
        });
      }
      
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && options.onProgress) {
          const progress = Math.round((e.loaded / e.total) * 100);
          options.onProgress(progress);
        }
      });
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            resolve({ success: true, data: xhr.responseText });
          }
        } else {
          reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
        }
      };
      
      xhr.onerror = () => {
        reject(new Error('网络错误'));
      };
      
      xhr.open('POST', url);
      
      // 设置请求头
      if (options.headers) {
        Object.keys(options.headers).forEach(key => {
          xhr.setRequestHeader(key, options.headers[key]);
        });
      }
      
      xhr.send(formData);
    });
  }

  /**
   * 显示进度
   */
  showProgress(progress) {
    const progressContainer = this.container.querySelector('.upload-progress');
    const progressFill = this.container.querySelector('.progress-fill');
    const progressText = this.container.querySelector('.progress-text');
    
    if (progressContainer && progressFill && progressText) {
      progressContainer.classList.remove('hidden');
      progressFill.style.width = `${progress}%`;
      progressText.textContent = `上传中... ${Math.round(progress)}%`;
    }
  }

  /**
   * 隐藏进度
   */
  hideProgress() {
    const progressContainer = this.container.querySelector('.upload-progress');
    if (progressContainer) {
      progressContainer.classList.add('hidden');
    }
  }

  /**
   * 显示错误
   */
  showError(message) {
    if (this.onError) {
      this.onError(message, this);
    } else {
      console.error('FileUpload Error:', message);
      // 这里可以集成通知组件
      if (window.Notification && window.Notification.error) {
        window.Notification.error(message);
      }
    }
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 获取文件列表
   */
  getFiles() {
    return this.files;
  }

  /**
   * 清空文件
   */
  clear() {
    this.files.forEach(file => {
      if (file.url) URL.revokeObjectURL(file.url);
      if (file.thumbnail) URL.revokeObjectURL(file.thumbnail);
      if (file.compressed) URL.revokeObjectURL(file.compressed);
    });
    
    this.files = [];
    this.updatePreview();
    
    // 重置文件输入
    if (this.fileInput) {
      this.fileInput.value = '';
    }
  }

  /**
   * 设置禁用状态
   */
  setDisabled(disabled = true) {
    if (this.uploadArea) {
      if (disabled) {
        this.uploadArea.classList.add('opacity-50', 'cursor-not-allowed');
        this.uploadArea.tabIndex = -1;
      } else {
        this.uploadArea.classList.remove('opacity-50', 'cursor-not-allowed');
        this.uploadArea.tabIndex = 0;
      }
    }
    
    if (this.fileInput) {
      this.fileInput.disabled = disabled;
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
    this.clear();
    
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.container = null;
    this.fileInput = null;
    this.uploadArea = null;
    this.previewArea = null;
    this.onFileSelect = null;
    this.onUploadProgress = null;
    this.onUploadComplete = null;
    this.onError = null;
  }
}