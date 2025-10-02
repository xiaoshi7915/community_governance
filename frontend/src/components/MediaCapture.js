/**
 * 媒体采集组件
 * 实现拍照、录像、相册选择功能
 */
export class MediaCapture {
  constructor(options = {}) {
    this.onMediaCapture = options.onMediaCapture || null;
    this.onError = options.onError || null;
    this.className = options.className || '';
    this.enablePreview = options.showPreview !== false;
    this.maxDuration = options.maxDuration || 30; // 录像最大时长（秒）
    this.quality = options.quality || 0.8;
    this.maxFileSize = options.maxFileSize || 50 * 1024 * 1024; // 50MB
    
    this.container = null;
    this.stream = null;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isRecording = false;
    this.recordingStartTime = null;
    this.recordingTimer = null;
    
    // 绑定方法
    this.handlePhotoCapture = this.handlePhotoCapture.bind(this);
    this.handleVideoCapture = this.handleVideoCapture.bind(this);
    this.handleGallerySelect = this.handleGallerySelect.bind(this);
    this.handleStopRecording = this.handleStopRecording.bind(this);
  }

  /**
   * 创建媒体采集HTML结构
   */
  createCaptureHTML() {
    return `
      <div class="media-capture-container ${this.className}">
        <div class="capture-buttons grid grid-cols-3 gap-4 mb-6">
          <button class="capture-btn photo-btn flex flex-col items-center p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors">
            <div class="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mb-2">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
            </div>
            <span class="text-sm font-medium text-gray-700">拍照</span>
          </button>
          
          <button class="capture-btn video-btn flex flex-col items-center p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-colors">
            <div class="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mb-2">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
              </svg>
            </div>
            <span class="text-sm font-medium text-gray-700">录像</span>
          </button>
          
          <button class="capture-btn gallery-btn flex flex-col items-center p-4 bg-purple-50 rounded-xl hover:bg-purple-100 transition-colors">
            <div class="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center mb-2">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2-2v12a2 2 0 002 2z"></path>
              </svg>
            </div>
            <span class="text-sm font-medium text-gray-700">相册</span>
          </button>
        </div>
        
        <!-- 隐藏的文件输入 -->
        <input type="file" class="gallery-input hidden" accept="image/*,video/*" multiple>
        
        <!-- 录像控制 -->
        <div class="recording-controls hidden">
          <div class="recording-status flex items-center justify-center mb-4">
            <div class="recording-indicator w-3 h-3 bg-red-500 rounded-full animate-pulse mr-2"></div>
            <span class="recording-time text-lg font-mono">00:00</span>
          </div>
          
          <div class="recording-buttons flex justify-center space-x-4">
            <button class="stop-recording-btn bg-red-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-red-700 transition-colors">
              停止录制
            </button>
          </div>
        </div>
        
        <!-- 预览区域 -->
        ${this.enablePreview ? `
          <div class="preview-area mt-6 hidden">
            <h3 class="text-lg font-semibold mb-4">预览</h3>
            <div class="preview-content"></div>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * 渲染媒体采集组件
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'media-capture-wrapper';
    this.container.innerHTML = this.createCaptureHTML();
    
    this.bindEvents();
    return this.container;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    if (!this.container) return;
    
    // 拍照按钮
    const photoBtn = this.container.querySelector('.photo-btn');
    if (photoBtn) {
      photoBtn.addEventListener('click', this.handlePhotoCapture);
    }
    
    // 录像按钮
    const videoBtn = this.container.querySelector('.video-btn');
    if (videoBtn) {
      videoBtn.addEventListener('click', this.handleVideoCapture);
    }
    
    // 相册按钮
    const galleryBtn = this.container.querySelector('.gallery-btn');
    if (galleryBtn) {
      galleryBtn.addEventListener('click', this.handleGallerySelect);
    }
    
    // 相册文件输入
    const galleryInput = this.container.querySelector('.gallery-input');
    if (galleryInput) {
      galleryInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        this.handleFilesSelected(files);
      });
    }
    
    // 停止录制按钮
    const stopBtn = this.container.querySelector('.stop-recording-btn');
    if (stopBtn) {
      stopBtn.addEventListener('click', this.handleStopRecording);
    }
  }

  /**
   * 处理拍照
   */
  async handlePhotoCapture() {
    try {
      // 检查浏览器支持
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('您的浏览器不支持摄像头功能');
      }

      // 检查权限
      try {
        const permissions = await navigator.permissions.query({ name: 'camera' });
        if (permissions.state === 'denied') {
          throw new Error('摄像头权限被拒绝，请在浏览器设置中允许摄像头访问');
        }
      } catch (permError) {
        console.warn('无法检查摄像头权限:', permError);
      }
      
      // 获取摄像头权限
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment', // 后置摄像头
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      // 创建视频元素进行预览
      const video = document.createElement('video');
      video.srcObject = stream;
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      
      // 创建拍照界面
      const captureModal = this.createCaptureModal(video, stream, 'photo');
      document.body.appendChild(captureModal);
      
    } catch (error) {
      this.handleError('拍照失败', error);
    }
  }

  /**
   * 处理录像
   */
  async handleVideoCapture() {
    try {
      // 检查浏览器支持
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('您的浏览器不支持摄像头功能');
      }

      // 检查权限
      try {
        const permissions = await navigator.permissions.query({ name: 'camera' });
        if (permissions.state === 'denied') {
          throw new Error('摄像头权限被拒绝，请在浏览器设置中允许摄像头访问');
        }
      } catch (permError) {
        console.warn('无法检查摄像头权限:', permError);
      }
      
      // 获取摄像头和麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: true
      });
      
      // 创建视频元素进行预览
      const video = document.createElement('video');
      video.srcObject = stream;
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      
      // 创建录像界面
      const captureModal = this.createCaptureModal(video, stream, 'video');
      document.body.appendChild(captureModal);
      
    } catch (error) {
      this.handleError('录像失败', error);
    }
  }

  /**
   * 处理停止录制
   */
  handleStopRecording() {
    if (this.isRecording && this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      
      // 更新UI
      const modal = document.querySelector('.capture-modal');
      if (modal) {
        this.updateRecordingUI(modal, false);
      }
      
      this.stopRecordingTimer();
    }
  }

  /**
   * 处理相册选择
   */
  handleGallerySelect() {
    const galleryInput = this.container.querySelector('.gallery-input');
    if (galleryInput) {
      galleryInput.click();
    }
  }

  /**
   * 创建拍照/录像模态框
   */
  createCaptureModal(video, stream, mode) {
    const modal = document.createElement('div');
    modal.className = 'capture-modal fixed inset-0 bg-black z-50 flex flex-col';
    
    modal.innerHTML = `
      <div class="capture-header flex items-center justify-between p-4 text-white">
        <button class="close-capture text-white hover:text-gray-300">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
        <h2 class="text-lg font-semibold">${mode === 'photo' ? '拍照' : '录像'}</h2>
        <div class="w-6"></div>
      </div>
      
      <div class="capture-preview flex-1 flex items-center justify-center p-4">
        <div class="video-container relative max-w-full max-h-full">
          <!-- 视频元素将被插入这里 -->
        </div>
      </div>
      
      <div class="capture-controls p-6 text-center">
        ${mode === 'photo' ? `
          <button class="capture-photo-btn w-16 h-16 bg-white rounded-full border-4 border-gray-300 hover:border-gray-400 transition-colors">
            <div class="w-full h-full bg-white rounded-full"></div>
          </button>
        ` : `
          <div class="recording-info mb-4 ${this.isRecording ? '' : 'hidden'}">
            <div class="recording-time text-white text-xl font-mono">00:00</div>
          </div>
          <button class="capture-video-btn w-16 h-16 ${this.isRecording ? 'bg-red-600' : 'bg-white'} rounded-full border-4 border-gray-300 hover:border-gray-400 transition-colors">
            ${this.isRecording ? `
              <div class="w-6 h-6 bg-white rounded mx-auto"></div>
            ` : `
              <div class="w-full h-full bg-red-600 rounded-full"></div>
            `}
          </button>
        `}
      </div>
    `;
    
    // 插入视频元素
    const videoContainer = modal.querySelector('.video-container');
    video.className = 'max-w-full max-h-full rounded-lg';
    videoContainer.appendChild(video);
    
    // 绑定事件
    this.bindCaptureModalEvents(modal, video, stream, mode);
    
    return modal;
  }

  /**
   * 绑定拍照/录像模态框事件
   */
  bindCaptureModalEvents(modal, video, stream, mode) {
    // 关闭按钮
    const closeBtn = modal.querySelector('.close-capture');
    closeBtn.addEventListener('click', () => {
      this.closeCaptureModal(modal, stream);
    });
    
    if (mode === 'photo') {
      // 拍照按钮
      const captureBtn = modal.querySelector('.capture-photo-btn');
      captureBtn.addEventListener('click', () => {
        this.capturePhoto(video, modal, stream);
      });
    } else {
      // 录像按钮
      const captureBtn = modal.querySelector('.capture-video-btn');
      captureBtn.addEventListener('click', () => {
        if (this.isRecording) {
          this.stopVideoRecording(modal, stream);
        } else {
          this.startVideoRecording(stream, modal);
        }
      });
    }
  }

  /**
   * 拍照
   */
  capturePhoto(video, modal, stream) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // 设置画布尺寸
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // 绘制当前帧
    ctx.drawImage(video, 0, 0);
    
    // 转换为Blob
    canvas.toBlob((blob) => {
      const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
      
      // 关闭模态框
      this.closeCaptureModal(modal, stream);
      
      // 触发回调
      if (this.onMediaCapture) {
        this.onMediaCapture({
          file: file,
          type: file.type,
          url: URL.createObjectURL(file),
          size: file.size,
          name: file.name,
          captureType: 'photo'
        });
      }
      
      // 显示预览
      if (this.enablePreview) {
        this.showPreview([file]);
      }
    }, 'image/jpeg', this.quality);
  }

  /**
   * 开始录像
   */
  startVideoRecording(stream, modal) {
    try {
      this.recordedChunks = [];
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9'
      });
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };
      
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        const file = new File([blob], `video_${Date.now()}.webm`, { type: 'video/webm' });
        
        // 关闭模态框
        this.closeCaptureModal(modal, stream);
        
        // 触发回调
        if (this.onMediaCapture) {
          this.onMediaCapture({
            file: file,
            type: file.type,
            url: URL.createObjectURL(file),
            size: file.size,
            name: file.name,
            captureType: 'video'
          });
        }
        
        // 显示预览
        if (this.enablePreview) {
          this.showPreview([file]);
        }
      };
      
      this.mediaRecorder.start();
      this.isRecording = true;
      this.recordingStartTime = Date.now();
      
      // 更新UI
      this.updateRecordingUI(modal, true);
      
      // 开始计时
      this.startRecordingTimer(modal);
      
      // 设置最大录制时长
      setTimeout(() => {
        if (this.isRecording) {
          this.stopVideoRecording(modal, stream);
        }
      }, this.maxDuration * 1000);
      
    } catch (error) {
      this.handleError('开始录像失败', error);
    }
  }

  /**
   * 停止录像
   */
  stopVideoRecording(modal, stream) {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      
      // 停止计时
      this.stopRecordingTimer();
      
      // 更新UI
      this.updateRecordingUI(modal, false);
    }
  }

  /**
   * 更新录像UI
   */
  updateRecordingUI(modal, isRecording) {
    const captureBtn = modal.querySelector('.capture-video-btn');
    const recordingInfo = modal.querySelector('.recording-info');
    
    if (isRecording) {
      captureBtn.className = 'capture-video-btn w-16 h-16 bg-red-600 rounded-full border-4 border-gray-300 hover:border-gray-400 transition-colors';
      captureBtn.innerHTML = '<div class="w-6 h-6 bg-white rounded mx-auto"></div>';
      recordingInfo.classList.remove('hidden');
    } else {
      captureBtn.className = 'capture-video-btn w-16 h-16 bg-white rounded-full border-4 border-gray-300 hover:border-gray-400 transition-colors';
      captureBtn.innerHTML = '<div class="w-full h-full bg-red-600 rounded-full"></div>';
      recordingInfo.classList.add('hidden');
    }
  }

  /**
   * 开始录制计时
   */
  startRecordingTimer(modal) {
    const timeDisplay = modal.querySelector('.recording-time');
    
    this.recordingTimer = setInterval(() => {
      if (this.recordingStartTime) {
        const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      }
    }, 1000);
  }

  /**
   * 停止录制计时
   */
  stopRecordingTimer() {
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
      this.recordingTimer = null;
    }
  }

  /**
   * 关闭拍照/录像模态框
   */
  closeCaptureModal(modal, stream) {
    // 停止摄像头流
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    
    // 停止录制
    if (this.isRecording) {
      this.stopVideoRecording(modal, stream);
    }
    
    // 移除模态框
    if (modal.parentNode) {
      modal.parentNode.removeChild(modal);
    }
  }

  /**
   * 处理文件选择
   */
  handleFilesSelected(files) {
    if (files.length === 0) return;
    
    // 验证文件
    const validFiles = [];
    for (const file of files) {
      if (this.validateFile(file)) {
        validFiles.push(file);
      }
    }
    
    if (validFiles.length === 0) return;
    
    // 只处理第一个文件（单文件上传）
    const file = validFiles[0];
    
    // 触发回调
    if (this.onMediaCapture) {
      this.onMediaCapture({
        file: file,
        type: file.type,
        url: URL.createObjectURL(file),
        size: file.size,
        name: file.name,
        captureType: 'gallery'
      });
    }
    
    // 显示预览
    if (this.enablePreview) {
      this.showPreview([file]);
    }
  }

  /**
   * 验证文件
   */
  validateFile(file) {
    // 检查文件大小
    if (file.size > this.maxFileSize) {
      this.handleError(`文件大小超过限制（${this.formatFileSize(this.maxFileSize)}）`);
      return false;
    }
    
    // 检查文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/webm', 'video/quicktime'];
    if (!allowedTypes.includes(file.type)) {
      this.handleError('不支持的文件类型');
      return false;
    }
    
    return true;
  }

  /**
   * 显示预览
   */
  showPreview(files) {
    if (!this.enablePreview || !this.container) return;
    
    const previewArea = this.container.querySelector('.preview-area');
    const previewContent = this.container.querySelector('.preview-content');
    
    if (!previewArea || !previewContent) return;
    
    previewArea.classList.remove('hidden');
    
    previewContent.innerHTML = files.map((file, index) => {
      const url = URL.createObjectURL(file);
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');
      
      return `
        <div class="preview-item mb-4" data-index="${index}">
          ${isImage ? `
            <img src="${url}" alt="预览图片" class="w-full max-w-sm rounded-lg shadow-md">
          ` : isVideo ? `
            <video src="${url}" controls class="w-full max-w-sm rounded-lg shadow-md"></video>
          ` : `
            <div class="w-full max-w-sm p-4 bg-gray-100 rounded-lg shadow-md">
              <p class="text-gray-600">${file.name}</p>
              <p class="text-sm text-gray-500">${this.formatFileSize(file.size)}</p>
            </div>
          `}
        </div>
      `;
    }).join('');
  }

  /**
   * 处理错误
   */
  handleError(message, error) {
    console.error('MediaCapture Error:', message, error);
    
    if (this.onError) {
      this.onError(message, error, this);
    } else {
      // 这里可以集成通知组件
      if (window.Notification && window.Notification.error) {
        window.Notification.error(message);
      } else {
        alert(message);
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
   * 获取DOM元素
   */
  getElement() {
    return this.container;
  }

  /**
   * 重置组件
   */
  reset() {
    // 清除预览
    if (this.enablePreview && this.container) {
      const previewArea = this.container.querySelector('.preview-area');
      if (previewArea) {
        previewArea.classList.add('hidden');
      }
    }
    
    // 重置文件输入
    const galleryInput = this.container.querySelector('.gallery-input');
    if (galleryInput) {
      galleryInput.value = '';
    }
    
    // 停止任何正在进行的录制
    if (this.isRecording && this.mediaRecorder) {
      this.mediaRecorder.stop();
    }
    
    this.isRecording = false;
    this.recordedChunks = [];
    this.recordingStartTime = null;
    this.stopRecordingTimer();
  }

  /**
   * 销毁组件
   */
  destroy() {
    // 停止录制
    if (this.isRecording && this.mediaRecorder) {
      this.mediaRecorder.stop();
    }
    
    // 停止计时器
    this.stopRecordingTimer();
    
    // 停止摄像头流
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }
    
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.container = null;
    this.stream = null;
    this.mediaRecorder = null;
    this.onMediaCapture = null;
    this.onError = null;
  }
}