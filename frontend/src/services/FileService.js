import { HttpClient } from './HttpClient.js';

/**
 * 文件上传服务类
 * 处理文件上传、带进度显示的文件上传功能
 * 添加文件压缩和格式验证
 */
export class FileService extends HttpClient {
  constructor() {
    super('/files');
    
    // 支持的文件类型
    this.SUPPORTED_TYPES = {
      IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
      VIDEO: ['video/mp4', 'video/avi', 'video/mov', 'video/wmv'],
      DOCUMENT: ['application/pdf', 'text/plain', 'application/msword']
    };

    // 文件大小限制 (字节)
    this.SIZE_LIMITS = {
      IMAGE: 10 * 1024 * 1024,    // 10MB
      VIDEO: 100 * 1024 * 1024,   // 100MB
      DOCUMENT: 5 * 1024 * 1024   // 5MB
    };

    // 图片压缩配置
    this.COMPRESSION_CONFIG = {
      quality: 0.8,
      maxWidth: 1920,
      maxHeight: 1080
    };
  }

  /**
   * 上传单个文件
   * @param {File} file - 文件对象
   * @param {Object} options - 上传选项
   * @param {Function} options.onProgress - 进度回调
   * @param {boolean} options.compress - 是否压缩图片
   * @param {string} options.category - 文件分类
   * @returns {Promise<Object>} 上传结果
   */
  async uploadFile(file, options = {}) {
    try {
      // 验证文件
      this.validateFile(file);

      // 处理文件（压缩等）
      const processedFile = await this.processFile(file, options);

      // 创建FormData
      const formData = new FormData();
      formData.append('file', processedFile);
      
      if (options.category) {
        formData.append('category', options.category);
      }

      // 上传文件
      const response = await this.uploadWithProgress('/upload', formData, options.onProgress);

      if (response.success) {
        // 触发文件上传成功事件
        this.dispatchFileEvent('uploaded', { 
          file: processedFile, 
          result: response.data 
        });
      }

      return response;
    } catch (error) {
      // 触发文件上传失败事件
      this.dispatchFileEvent('upload-failed', { 
        file, 
        error: error.message 
      });
      
      throw new Error(error.message || '文件上传失败');
    }
  }

  /**
   * 批量上传文件
   * @param {FileList|Array} files - 文件列表
   * @param {Object} options - 上传选项
   * @param {Function} options.onProgress - 总体进度回调
   * @param {Function} options.onFileProgress - 单个文件进度回调
   * @param {boolean} options.compress - 是否压缩图片
   * @param {string} options.category - 文件分类
   * @returns {Promise<Array>} 上传结果列表
   */
  async uploadMultipleFiles(files, options = {}) {
    const fileArray = Array.from(files);
    const results = [];
    let completedCount = 0;

    try {
      // 并发上传文件
      const uploadPromises = fileArray.map(async (file, index) => {
        try {
          const result = await this.uploadFile(file, {
            ...options,
            onProgress: (progress) => {
              // 单个文件进度回调
              if (options.onFileProgress) {
                options.onFileProgress(index, progress);
              }

              // 计算总体进度
              if (options.onProgress) {
                const totalProgress = ((completedCount + progress / 100) / fileArray.length) * 100;
                options.onProgress(Math.round(totalProgress));
              }
            }
          });

          completedCount++;
          return { success: true, file, result: result.data };
        } catch (error) {
          completedCount++;
          return { success: false, file, error: error.message };
        }
      });

      const uploadResults = await Promise.all(uploadPromises);
      
      // 触发批量上传完成事件
      this.dispatchFileEvent('batch-uploaded', { 
        files: fileArray, 
        results: uploadResults 
      });

      return uploadResults;
    } catch (error) {
      throw new Error(error.message || '批量上传失败');
    }
  }

  /**
   * 带进度的文件上传
   * @param {string} url - 上传URL
   * @param {FormData} formData - 表单数据
   * @param {Function} onProgress - 进度回调
   * @returns {Promise<Object>} 上传结果
   */
  uploadWithProgress(url, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // 上传进度监听
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = Math.round((e.loaded / e.total) * 100);
          onProgress(progress);
        }
      });

      // 上传完成监听
      xhr.addEventListener('load', () => {
        try {
          if (xhr.status >= 200 && xhr.status < 300) {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } else {
            reject(new Error(`上传失败: HTTP ${xhr.status}`));
          }
        } catch (error) {
          reject(new Error('响应解析失败'));
        }
      });

      // 上传错误监听
      xhr.addEventListener('error', () => {
        reject(new Error('网络错误'));
      });

      // 上传中止监听
      xhr.addEventListener('abort', () => {
        reject(new Error('上传已取消'));
      });

      // 设置请求
      xhr.open('POST', this.baseURL + url);
      
      // 添加认证头
      const token = localStorage.getItem('access_token');
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      // 发送请求
      xhr.send(formData);
    });
  }

  /**
   * 验证文件
   * @param {File} file - 文件对象
   * @throws {Error} 验证失败时抛出错误
   */
  validateFile(file) {
    if (!file) {
      throw new Error('请选择文件');
    }

    // 检查文件类型
    const fileType = this.getFileType(file.type);
    if (!fileType) {
      throw new Error('不支持的文件类型');
    }

    // 检查文件大小
    const sizeLimit = this.SIZE_LIMITS[fileType];
    if (file.size > sizeLimit) {
      const sizeMB = Math.round(sizeLimit / (1024 * 1024));
      throw new Error(`文件大小不能超过 ${sizeMB}MB`);
    }

    // 检查文件名
    if (file.name.length > 255) {
      throw new Error('文件名过长');
    }
  }

  /**
   * 处理文件（压缩、转换等）
   * @param {File} file - 原始文件
   * @param {Object} options - 处理选项
   * @returns {Promise<File>} 处理后的文件
   */
  async processFile(file, options = {}) {
    const fileType = this.getFileType(file.type);

    // 图片压缩
    if (fileType === 'IMAGE' && options.compress !== false) {
      return await this.compressImage(file);
    }

    return file;
  }

  /**
   * 压缩图片
   * @param {File} file - 图片文件
   * @returns {Promise<File>} 压缩后的文件
   */
  compressImage(file) {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        // 计算压缩后的尺寸
        const { width, height } = this.calculateCompressedSize(
          img.width, 
          img.height, 
          this.COMPRESSION_CONFIG.maxWidth, 
          this.COMPRESSION_CONFIG.maxHeight
        );

        // 设置画布尺寸
        canvas.width = width;
        canvas.height = height;

        // 绘制压缩后的图片
        ctx.drawImage(img, 0, 0, width, height);

        // 转换为Blob
        canvas.toBlob((blob) => {
          // 创建新的File对象
          const compressedFile = new File([blob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now()
          });

          resolve(compressedFile);
        }, 'image/jpeg', this.COMPRESSION_CONFIG.quality);
      };

      img.src = URL.createObjectURL(file);
    });
  }

  /**
   * 计算压缩后的尺寸
   * @param {number} originalWidth - 原始宽度
   * @param {number} originalHeight - 原始高度
   * @param {number} maxWidth - 最大宽度
   * @param {number} maxHeight - 最大高度
   * @returns {Object} 压缩后的尺寸
   */
  calculateCompressedSize(originalWidth, originalHeight, maxWidth, maxHeight) {
    let { width, height } = { width: originalWidth, height: originalHeight };

    // 如果尺寸超出限制，按比例缩放
    if (width > maxWidth || height > maxHeight) {
      const widthRatio = maxWidth / width;
      const heightRatio = maxHeight / height;
      const ratio = Math.min(widthRatio, heightRatio);

      width = Math.round(width * ratio);
      height = Math.round(height * ratio);
    }

    return { width, height };
  }

  /**
   * 获取文件类型
   * @param {string} mimeType - MIME类型
   * @returns {string|null} 文件类型
   */
  getFileType(mimeType) {
    for (const [type, mimeTypes] of Object.entries(this.SUPPORTED_TYPES)) {
      if (mimeTypes.includes(mimeType)) {
        return type;
      }
    }
    return null;
  }

  /**
   * 删除文件
   * @param {string} fileId - 文件ID
   * @returns {Promise<Object>} 删除结果
   */
  async deleteFile(fileId) {
    try {
      const response = await this.delete(`/${fileId}`);

      if (response.success) {
        // 触发文件删除事件
        this.dispatchFileEvent('deleted', { fileId });
      }

      return response;
    } catch (error) {
      throw new Error(error.message || '文件删除失败');
    }
  }

  /**
   * 获取文件信息
   * @param {string} fileId - 文件ID
   * @returns {Promise<Object>} 文件信息
   */
  async getFileInfo(fileId) {
    try {
      const response = await this.get(`/${fileId}`);
      return response;
    } catch (error) {
      throw new Error(error.message || '获取文件信息失败');
    }
  }

  /**
   * 获取文件列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.category - 文件分类
   * @param {string} params.file_type - 文件类型
   * @returns {Promise<Object>} 文件列表
   */
  async getFileList(params = {}) {
    try {
      const queryParams = {
        page: params.page || 1,
        page_size: params.page_size || 20,
        ...params
      };

      const queryString = new URLSearchParams(queryParams).toString();
      const response = await this.get(`/?${queryString}`);

      return response;
    } catch (error) {
      throw new Error(error.message || '获取文件列表失败');
    }
  }

  /**
   * 生成文件预览URL
   * @param {string} fileId - 文件ID
   * @param {Object} options - 预览选项
   * @param {number} options.width - 预览宽度
   * @param {number} options.height - 预览高度
   * @param {string} options.format - 预览格式
   * @returns {string} 预览URL
   */
  generatePreviewUrl(fileId, options = {}) {
    const params = new URLSearchParams();
    
    if (options.width) params.append('width', options.width);
    if (options.height) params.append('height', options.height);
    if (options.format) params.append('format', options.format);

    const queryString = params.toString();
    return `${this.baseURL}/${fileId}/preview${queryString ? '?' + queryString : ''}`;
  }

  /**
   * 生成文件下载URL
   * @param {string} fileId - 文件ID
   * @returns {string} 下载URL
   */
  generateDownloadUrl(fileId) {
    return `${this.baseURL}/${fileId}/download`;
  }

  /**
   * 触发文件相关的自定义事件
   * @param {string} eventType - 事件类型
   * @param {Object} data - 事件数据
   */
  dispatchFileEvent(eventType, data = {}) {
    const event = new CustomEvent(`file:${eventType}`, {
      detail: data
    });
    window.dispatchEvent(event);
  }

  /**
   * 格式化文件大小
   * @param {number} bytes - 字节数
   * @returns {string} 格式化后的大小
   */
  static formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 获取文件扩展名
   * @param {string} filename - 文件名
   * @returns {string} 扩展名
   */
  static getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
  }

  /**
   * 检查是否为图片文件
   * @param {string} mimeType - MIME类型
   * @returns {boolean} 是否为图片
   */
  static isImageFile(mimeType) {
    return mimeType.startsWith('image/');
  }

  /**
   * 检查是否为视频文件
   * @param {string} mimeType - MIME类型
   * @returns {boolean} 是否为视频
   */
  static isVideoFile(mimeType) {
    return mimeType.startsWith('video/');
  }

  /**
   * 创建文件预览元素
   * @param {File} file - 文件对象
   * @returns {Promise<HTMLElement>} 预览元素
   */
  static createPreviewElement(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        if (FileService.isImageFile(file.type)) {
          const img = document.createElement('img');
          img.src = e.target.result;
          img.style.maxWidth = '100%';
          img.style.maxHeight = '200px';
          img.style.objectFit = 'cover';
          resolve(img);
        } else if (FileService.isVideoFile(file.type)) {
          const video = document.createElement('video');
          video.src = e.target.result;
          video.controls = true;
          video.style.maxWidth = '100%';
          video.style.maxHeight = '200px';
          resolve(video);
        } else {
          const div = document.createElement('div');
          div.className = 'file-preview';
          div.innerHTML = `
            <div class="file-icon">📄</div>
            <div class="file-name">${file.name}</div>
            <div class="file-size">${FileService.formatFileSize(file.size)}</div>
          `;
          resolve(div);
        }
      };

      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }
}