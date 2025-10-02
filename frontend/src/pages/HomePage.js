/**
 * 首页组件 - 事件上报页面
 * 实现媒体采集、AI识别、事件信息编辑和提交功能
 */
import { Navigation } from '../components/Navigation.js';
import { MediaCapture } from '../components/MediaCapture.js';
import { Modal } from '../components/Modal.js';
import { Notification } from '../components/Notification.js';
import { EventService } from '../services/EventService.js';
import { AIService } from '../services/AIService.js';
import { FileService } from '../services/FileService.js';
import EventStore from '../stores/EventStore.js';
import UserStore from '../stores/UserStore.js';

export class HomePage {
  constructor() {
    this.container = null;
    this.navigation = null;
    this.mediaCapture = null;
    this.currentMedia = null;
    this.aiResult = null;
    this.isSubmitting = false;

    // 服务实例
    this.eventService = new EventService();
    this.aiService = new AIService();
    this.fileService = new FileService();

    // 状态管理
    this.eventStore = EventStore;
    this.userStore = UserStore;

    // 表单数据
    this.formData = {
      title: '',
      description: '',
      location: '',
      priority: 'medium',
      eventType: '',
      mediaFiles: []
    };

    // 用户交互标志
    this.hasUserInteracted = false;

    this.init();
  }

  /**
   * 初始化组件
   */
  async init() {
    this.bindEvents();
    await this.loadInitialData();
  }

  /**
   * 绑定事件监听器
   */
  bindEvents() {
    // 监听用户状态变化
    this.userStore.subscribe((state) => {
      if (!state.isAuthenticated) {
        this.handleUnauthenticated();
      }
    });

    // 监听事件提交状态变化
    this.eventStore.subscribe((state) => {
      this.handleEventStateChange(state);
    });
  }

  /**
   * 加载初始数据
   */
  async loadInitialData() {
    try {
      // 获取用户位置信息
      await this.getCurrentLocation();

      // 预加载AI事件类型
      await this.loadEventTypes();
    } catch (error) {
      console.warn('Failed to load initial data:', error);
    }
  }

  /**
   * 获取当前位置
   */
  async getCurrentLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        console.warn('浏览器不支持地理定位');
        this.setDefaultLocation();
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.formData.location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            address: '正在获取地址...'
          };
          this.reverseGeocode(position.coords.latitude, position.coords.longitude);
          resolve(position);
        },
        (error) => {
          console.warn('Geolocation error:', error);
          let errorMessage = '定位失败';

          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = '定位权限被拒绝';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = '位置信息不可用';
              break;
            case error.TIMEOUT:
              errorMessage = '定位请求超时';
              break;
          }

          console.warn(errorMessage);
          this.setDefaultLocation();
          resolve(null);
        },
        {
          enableHighAccuracy: false, // 降低精度要求以提高成功率
          timeout: 8000, // 增加超时时间
          maximumAge: 600000 // 10分钟内的缓存位置可用
        }
      );
    });
  }

  /**
   * 设置默认位置
   */
  setDefaultLocation() {
    this.formData.location = {
      latitude: null,
      longitude: null,
      address: '请手动输入位置信息'
    };
    this.updateLocationDisplay();
  }

  /**
   * 反向地理编码
   */
  async reverseGeocode(lat, lng) {
    try {
      // 使用浏览器的地理编码API或第三方服务
      // 这里实现一个简单的地址解析逻辑
      const address = await this.getAddressFromCoordinates(lat, lng);
      this.formData.location.address = address;
      this.updateLocationDisplay();
    } catch (error) {
      console.warn('Reverse geocoding failed:', error);
      // 降级到坐标显示
      this.formData.location.address = `纬度: ${lat.toFixed(6)}, 经度: ${lng.toFixed(6)}`;
      this.updateLocationDisplay();
    }
  }

  /**
   * 从坐标获取地址
   */
  async getAddressFromCoordinates(lat, lng) {
    try {
      // 使用百度地图API进行反向地理编码
      const apiKey = 'DtlfzaQIvZYuPq3l4QpUUffmqT7mCRzA';
      
      // 先将GPS坐标转换为百度坐标系
      const convertUrl = `https://api.map.baidu.com/geoconv/v2/?coords=${lng},${lat}&from=1&to=5&ak=${apiKey}`;
      
      try {
        const convertResponse = await fetch(convertUrl);
        const convertData = await convertResponse.json();
        
        if (convertData.status === 0 && convertData.result && convertData.result.length > 0) {
          const bdLng = convertData.result[0].x;
          const bdLat = convertData.result[0].y;
          
          // 使用转换后的百度坐标进行反向地理编码
          const geocodeUrl = `https://api.map.baidu.com/reverse_geocoding/v3/?ak=${apiKey}&output=json&coordtype=bd09ll&location=${bdLat},${bdLng}`;
          
          const geocodeResponse = await fetch(geocodeUrl);
          const geocodeData = await geocodeResponse.json();
          
          if (geocodeData.status === 0 && geocodeData.result) {
            const address = geocodeData.result.formatted_address;
            console.log('百度地图地址解析成功:', address);
            return address;
          }
        }
      } catch (baiduError) {
        console.warn('百度地图API调用失败，尝试备用方案:', baiduError);
      }
      
      // 备用方案：使用简化的地址格式
      throw new Error('地址解析失败');
      
    } catch (error) {
      console.warn('地址解析失败:', error);
      // 降级处理：返回格式化的坐标信息
      const latStr = lat.toFixed(4);
      const lngStr = lng.toFixed(4);
      return `位置: ${latStr}, ${lngStr}`;
    }
  }

  /**
   * 加载事件类型
   */
  async loadEventTypes() {
    // 先设置默认事件类型，确保下拉框有选项
    this.eventTypes = [
      { id: 'traffic', name: '交通问题', confidence: 0 },
      { id: 'environment', name: '环境问题', confidence: 0 },
      { id: 'infrastructure', name: '基础设施', confidence: 0 },
      { id: 'safety', name: '安全问题', confidence: 0 },
      { id: 'public_service', name: '公共服务', confidence: 0 },
      { id: 'community', name: '社区管理', confidence: 0 },
      { id: 'other', name: '其他问题', confidence: 0 }
    ];

    try {
      // 尝试从API加载更多事件类型
      const userState = this.userStore.getState();
      if (userState.isAuthenticated) {
        const response = await this.aiService.getEventTypes();
        if (response.success && response.data && response.data.length > 0) {
          this.eventTypes = response.data;
          console.log('从API加载事件类型成功:', this.eventTypes);
        } else {
          console.log('API返回空数据，使用默认事件类型');
        }
      } else {
        console.log('用户未登录，使用默认事件类型');
      }
    } catch (error) {
      console.error('Failed to load event types from API:', error);
      console.log('使用默认事件类型');
    }

    // 确保事件类型已填充到下拉框
    this.populateEventTypes();
  }

  /**
   * 显示警告消息
   */
  showWarning(message) {
    // 创建简单的警告提示
    const warning = document.createElement('div');
    warning.className = 'fixed top-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded z-50';
    warning.innerHTML = `
      <div class="flex items-center">
        <span class="mr-2">⚠️</span>
        <span>${message}</span>
        <button class="ml-4 text-yellow-700 hover:text-yellow-900" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;
    
    document.body.appendChild(warning);
    
    // 3秒后自动移除
    setTimeout(() => {
      if (warning.parentNode) {
        warning.parentNode.removeChild(warning);
      }
    }, 3000);
  }

  /**
   * 渲染页面
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'home-page min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100';
    
    this.container.innerHTML = this.getTemplate();

    // 渲染子组件
    this.renderComponents();

    // 绑定页面事件
    this.bindPageEvents();

    // 添加页面加载动画
    this.animatePageLoad();

    return this.container;
  }

  /**
   * 获取页面模板
   */
  getTemplate() {
    return `
      <!-- 页面头部 -->
      <header class="page-header bg-white shadow-sm">
        <div class="flex items-center justify-between px-4 py-3">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
            </div>
            <div>
              <h1 class="text-lg font-semibold text-gray-900">事件上报</h1>
              <p class="text-sm text-gray-500">记录和上报社区问题</p>
            </div>
          </div>
          <div class="user-info flex items-center space-x-2">
            <div class="w-8 h-8 bg-gray-300 rounded-full"></div>
          </div>
        </div>
      </header>

      <!-- 主要内容区域 -->
      <main class="page-content px-4 py-6 pb-24">
        <!-- 媒体采集区域 -->
        <section class="media-section mb-6">
          <div class="glass-card p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">添加媒体</h2>
            <div id="media-capture-container" class="media-capture-container">
              <!-- MediaCapture 组件将在这里渲染 -->
            </div>
            
            <!-- 媒体预览区域 -->
            <div id="media-preview" class="media-preview mt-4 hidden">
              <div class="relative">
                <img id="preview-image" class="w-full h-48 object-cover rounded-lg" style="display: none;">
                <video id="preview-video" class="w-full h-48 object-cover rounded-lg" controls style="display: none;"></video>
                <button id="remove-media" class="absolute top-2 right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- AI识别结果区域 -->
        <section id="ai-result-section" class="ai-result-section mb-6 hidden">
          <div class="glass-card p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">AI识别结果</h2>
            <div id="ai-result-content" class="ai-result-content">
              <!-- AI识别结果将在这里显示 -->
            </div>
          </div>
        </section>

        <!-- 事件信息编辑区域 -->
        <section class="event-form-section">
          <div class="glass-card p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">事件信息</h2>
            
            <form id="event-form" class="space-y-4">
              <!-- 事件标题 -->
              <div class="form-group">
                <label for="event-title" class="block text-sm font-medium text-gray-700 mb-2">事件标题</label>
                <input 
                  type="text" 
                  id="event-title" 
                  name="title"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="请输入事件标题"
                  maxlength="100"
                >
              </div>

              <!-- 事件类型 -->
              <div class="form-group">
                <label for="event-type" class="block text-sm font-medium text-gray-700 mb-2">事件类型</label>
                <select 
                  id="event-type" 
                  name="eventType"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">请选择事件类型</option>
                </select>
              </div>

              <!-- 优先�?-->
              <div class="form-group">
                <label class="block text-sm font-medium text-gray-700 mb-2">优先级</label>
                <div class="flex space-x-4">
                  <label class="flex items-center">
                    <input type="radio" name="priority" value="low" class="mr-2">
                    <span class="text-sm text-green-600">低</span>
                  </label>
                  <label class="flex items-center">
                    <input type="radio" name="priority" value="medium" class="mr-2" checked>
                    <span class="text-sm text-yellow-600">中</span>
                  </label>
                  <label class="flex items-center">
                    <input type="radio" name="priority" value="high" class="mr-2">
                    <span class="text-sm text-red-600">高</span>
                  </label>
                </div>
              </div>

              <!-- 位置信息 -->
              <div class="form-group">
                <label for="event-location" class="block text-sm font-medium text-gray-700 mb-2">位置信息</label>
                <div class="space-y-2">
                  <div class="flex space-x-2">
                    <input 
                      type="text" 
                      id="event-location" 
                      name="location"
                      class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="正在获取位置..."
                    >
                    <button 
                      type="button" 
                      id="refresh-location"
                      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-1"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      </svg>
                      <span id="refresh-location-text">定位</span>
                    </button>
                  </div>
                  
                  <!-- 位置精度指示器 -->
                  <div id="location-accuracy" class="hidden text-xs text-gray-500 flex items-center space-x-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span id="location-accuracy-text">定位精度: 未知</span>
                  </div>
                  
                  <!-- 手动编辑提示 -->
                  <div class="text-xs text-gray-500">
                    <span>💡 您可以手动编辑位置信息或点击定位按钮获取当前位置</span>
                  </div>
                </div>
              </div>

              <!-- 事件描述 -->
              <div class="form-group">
                <label for="event-description" class="block text-sm font-medium text-gray-700 mb-2">详细描述</label>
                <textarea 
                  id="event-description" 
                  name="description"
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="请详细描述事件情况..."
                  maxlength="500"
                ></textarea>
                <div class="text-right text-sm text-gray-500 mt-1">
                  <span id="description-count">0</span>/500
                </div>
              </div>

              <!-- 提交按钮 -->
              <div class="form-actions pt-4">
                <button 
                  type="submit" 
                  id="submit-event"
                  class="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  <span id="submit-text">提交事件</span>
                  <div id="submit-loading" class="hidden flex items-center justify-center">
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    提交中...
                  </div>
                </button>
              </div>
            </form>
          </div>
        </section>
      </main>

      <!-- 底部导航容器 -->
      <div id="navigation-container" class="navigation-container">
        <!-- Navigation 组件将在这里渲染 -->
      </div>
    `;
  }

  /**
   * 渲染子组件
   */
  renderComponents() {
    // 渲染导航组件
    this.navigation = new Navigation({
      activeTab: 'home',
      onNavigate: (path, tabId) => this.handleNavigation(path, tabId)
    });

    const navContainer = this.container.querySelector('#navigation-container');
    this.navigation.mount(navContainer);

    // 渲染媒体采集组件
    this.mediaCapture = new MediaCapture({
      onMediaCapture: (media) => this.handleMediaCapture(media),
      onError: (error) => this.handleMediaError(error)
    });

    const mediaCaptureContainer = this.container.querySelector('#media-capture-container');
    mediaCaptureContainer.appendChild(this.mediaCapture.render());

    // 确保事件类型已加载后再填充选项
    if (this.eventTypes && this.eventTypes.length > 0) {
      this.populateEventTypes();
    } else {
      // 如果还没加载，等待加载完成后填充
      setTimeout(() => {
        this.populateEventTypes();
      }, 1000);
    }
  }

  /**
   * 填充事件类型选项
   */
  populateEventTypes() {
    const eventTypeSelect = this.container.querySelector('#event-type');
    if (!eventTypeSelect) {
      console.warn('事件类型选择框未找到');
      return;
    }

    // 清空现有选项（保留默认选项）
    const defaultOption = eventTypeSelect.querySelector('option[value=""]');
    eventTypeSelect.innerHTML = '';
    
    // 添加默认选项
    if (defaultOption) {
      eventTypeSelect.appendChild(defaultOption);
    } else {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = '请选择事件类型';
      option.disabled = true;
      option.selected = true;
      eventTypeSelect.appendChild(option);
    }

    // 添加事件类型选项
    if (this.eventTypes && Array.isArray(this.eventTypes) && this.eventTypes.length > 0) {
      this.eventTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type.id;
        option.textContent = type.name;
        eventTypeSelect.appendChild(option);
      });
      console.log(`✅ 已填充 ${this.eventTypes.length} 个事件类型选项`);
    } else {
      console.warn('⚠️ 没有可用的事件类型，eventTypes:', this.eventTypes);
      // 如果eventTypes不是数组，重新初始化
      if (!Array.isArray(this.eventTypes)) {
        this.eventTypes = [
          { id: 'traffic', name: '交通问题' },
          { id: 'environment', name: '环境问题' },
          { id: 'infrastructure', name: '基础设施' },
          { id: 'safety', name: '安全问题' },
          { id: 'other', name: '其他问题' }
        ];
        // 重新调用填充方法
        this.populateEventTypes();
      }
    }
  }

  /**
   * 绑定页面事件
   */
  bindPageEvents() {
    const form = this.container.querySelector('#event-form');
    const removeMediaBtn = this.container.querySelector('#remove-media');
    const refreshLocationBtn = this.container.querySelector('#refresh-location');
    const descriptionTextarea = this.container.querySelector('#event-description');

    // 表单提交事件
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleFormSubmit();
    });

    // 移除媒体事件
    removeMediaBtn.addEventListener('click', () => {
      this.removeCurrentMedia();
    });

    // 刷新位置事件
    refreshLocationBtn.addEventListener('click', () => {
      this.refreshLocation();
    });

    // 描述字数统计
    descriptionTextarea.addEventListener('input', (e) => {
      this.updateDescriptionCount(e.target.value.length);
    });

    // 表单字段变化事件
    form.addEventListener('input', (e) => {
      this.handleFormFieldChange(e.target);
    });
  }

  /**
   * 页面加载动画
   */
  animatePageLoad() {
    // 添加页面淡入动画
    this.container.classList.add('animate-fade-in');

    // 依次显示各个区域
    const sections = this.container.querySelectorAll('section');
    sections.forEach((section, index) => {
      setTimeout(() => {
        section.classList.add('animate-slide-up');
      }, index * 100);
    });
  }

  /**
   * 处理导航
   */
  handleNavigation(path, tabId) {
    // 使用路由系统进行导航
    if (window.router) {
      window.router.navigate(path);
    } else {
      // 降级处理：触发自定义导航事件
      const navigationEvent = new CustomEvent('navigate', {
        detail: { path, tabId }
      });
      document.dispatchEvent(navigationEvent);
    }
  }

  /**
   * 处理媒体采集
   */
  async handleMediaCapture(media) {
    this.currentMedia = media;
    this.showMediaPreview(media);

    // 如果是图片，自动进行AI识别
    if (media.type.startsWith('image/')) {
      await this.performAIAnalysis(media);
    }
  }

  /**
   * 显示媒体预览
   */
  showMediaPreview(media) {
    const previewContainer = this.container.querySelector('#media-preview');
    const previewImage = this.container.querySelector('#preview-image');
    const previewVideo = this.container.querySelector('#preview-video');

    // 隐藏所有预览元素
    previewImage.style.display = 'none';
    previewVideo.style.display = 'none';

    if (media.type.startsWith('image/')) {
      previewImage.src = media.url;
      previewImage.style.display = 'block';
    } else if (media.type.startsWith('video/')) {
      previewVideo.src = media.url;
      previewVideo.style.display = 'block';
    }

    previewContainer.classList.remove('hidden');
    previewContainer.classList.add('animate-slide-up');
  }

  /**
   * 移除当前媒体
   */
  removeCurrentMedia() {
    this.currentMedia = null;
    this.aiResult = null;

    const previewContainer = this.container.querySelector('#media-preview');
    const aiResultSection = this.container.querySelector('#ai-result-section');

    previewContainer.classList.add('hidden');
    aiResultSection.classList.add('hidden');

    // 重置媒体采集组件
    if (this.mediaCapture) {
      this.mediaCapture.reset();
    }
  }

  /**
   * 执行AI分析
   */
  async performAIAnalysis(media) {
    try {
      // 显示分析中状态
      this.showAIAnalyzing();

      // 检查用户是否已登录
      const userState = this.userStore.getState();
      if (!userState.isAuthenticated) {
        throw new Error('请先登录后再使用AI分析功能');
      }

      // 上传文件并获取URL
      const uploadResult = await this.fileService.uploadFile(media.file, (progress) => {
        this.updateUploadProgress(progress);
      });

      if (!uploadResult.success) {
        throw new Error('文件上传失败: ' + (uploadResult.message || '未知错误'));
      }

      // 根据媒体类型选择分析方法
      let analysisResult;
      if (media.type.startsWith('image/')) {
        // 调用图片分析API
        analysisResult = await this.aiService.analyzeImage(uploadResult.data.url);
      } else if (media.type.startsWith('video/')) {
        // 调用视频分析API
        analysisResult = await this.aiService.analyzeVideo(uploadResult.data.url);
      } else {
        throw new Error('不支持的媒体类型');
      }

      if (analysisResult.success) {
        this.aiResult = analysisResult.data;
        this.showAIResult(this.aiResult);
        this.autoFillFormFromAI(this.aiResult);

        // 存储媒体URL用于后续提交
        this.currentMedia.uploadedUrl = uploadResult.data.url;
      } else {
        throw new Error(analysisResult.message || 'AI分析失败');
      }

    } catch (error) {
      console.error('AI analysis failed:', error);
      this.showAIError(error.message);
    }
  }

  /**
   * 显示AI分析中状态
   */
  showAIAnalyzing() {
    const aiResultSection = this.container.querySelector('#ai-result-section');
    const aiResultContent = this.container.querySelector('#ai-result-content');

    aiResultContent.innerHTML = `
      <div class="flex items-center justify-center py-8">
        <div class="text-center">
          <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-gray-600">AI正在分析图像...</p>
        </div>
      </div>
    `;

    aiResultSection.classList.remove('hidden');
    aiResultSection.classList.add('animate-slide-up');
  }

  /**
   * 显示AI分析结果
   */
  showAIResult(result) {
    const aiResultContent = this.container.querySelector('#ai-result-content');

    // 格式化结果用于显示
    const formattedResult = this.aiService.constructor.formatResultForDisplay(result);

    aiResultContent.innerHTML = `
      <div class="ai-result-display">
        <!-- 分析摘要 -->
        <div class="mb-4 p-3 bg-blue-50 rounded-lg">
          <div class="flex items-start space-x-2">
            <svg class="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            <div>
              <h3 class="text-sm font-medium text-blue-900 mb-1">AI分析摘要</h3>
              <p class="text-sm text-blue-800">${result.summary || '分析完成'}</p>
            </div>
          </div>
        </div>

        <!-- 检测结�?-->
        ${result.detections && result.detections.length > 0 ? `
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 mb-2">检测结果</h3>
            <div class="space-y-2">
              ${result.detections.slice(0, 3).map(detection => `
                <div class="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                  <div class="flex items-center space-x-2">
                    <span class="w-2 h-2 rounded-full ${detection.confidence_level === 'high' ? 'bg-green-500' :
        detection.confidence_level === 'medium' ? 'bg-yellow-500' :
          'bg-gray-500'
      }"></span>
                    <span class="text-sm font-medium text-gray-900">${detection.label}</span>
                  </div>
                  <span class="text-xs text-gray-500">${detection.confidence_text}</span>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <!-- 推荐事件类型 -->
        ${result.recommended_event_types && result.recommended_event_types.length > 0 ? `
          <div class="mb-4">
            <h3 class="text-sm font-medium text-gray-700 mb-2">推荐事件类型</h3>
            <div class="flex flex-wrap gap-2">
              ${result.recommended_event_types.map(type => `
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${type.confidence_level === 'high' ? 'bg-green-100 text-green-800' :
          type.confidence_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
        }">
                  ${type.name}
                  <span class="ml-1 text-xs opacity-75">${Math.round(type.confidence * 100)}%</span>
                </span>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <!-- 可靠性指示器 -->
        <div class="mb-4 p-3 rounded-lg ${formattedResult.isReliable ? 'bg-green-50' : 'bg-yellow-50'}">
          <div class="flex items-center space-x-2">
            <svg class="w-4 h-4 ${formattedResult.isReliable ? 'text-green-600' : 'text-yellow-600'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${formattedResult.isReliable ? 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' : 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z'}"></path>
            </svg>
            <span class="text-sm ${formattedResult.isReliable ? 'text-green-800' : 'text-yellow-800'}">
              ${formattedResult.isReliable ? '分析结果可信度较高' : '分析结果仅供参考，建议人工确认'}
            </span>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center justify-between">
          <div class="text-xs text-gray-500">
            <span>分析完成 - ${formattedResult.detectionCount} 项检测</span>
          </div>
          <div class="flex space-x-2">
            <button id="retry-ai-analysis" class="text-gray-600 hover:text-gray-800 text-xs font-medium">
              重新分析
            </button>
            <button id="apply-ai-result" class="text-blue-600 hover:text-blue-800 text-xs font-medium">
              应用到表单
            </button>
          </div>
        </div>
      </div>
    `;

    // 绑定按钮事件
    const applyBtn = aiResultContent.querySelector('#apply-ai-result');
    const retryBtn = aiResultContent.querySelector('#retry-ai-analysis');

    applyBtn.addEventListener('click', () => {
      this.autoFillFormFromAI(result);
    });

    retryBtn.addEventListener('click', () => {
      if (this.currentMedia) {
        this.performAIAnalysis(this.currentMedia);
      }
    });
  }

  /**
   * 显示AI分析错误
   */
  showAIError(errorMessage) {
    const aiResultContent = this.container.querySelector('#ai-result-content');

    // 分析错误类型并提供相应的建议
    let errorType = 'general';
    let suggestion = '请检查网络连接后重试';

    if (errorMessage.includes('上传')) {
      errorType = 'upload';
      suggestion = '文件上传失败，请检查文件大小和网络连接';
    } else if (errorMessage.includes('不支持')) {
      errorType = 'format';
      suggestion = '请选择支持的图片或视频格式';
    } else if (errorMessage.includes('超时')) {
      errorType = 'timeout';
      suggestion = '分析超时，请稍后重试或选择较小的文件';
    } else if (errorMessage.includes('服务')) {
      errorType = 'service';
      suggestion = 'AI服务暂时不可用，您可以手动填写事件信息';
    }

    aiResultContent.innerHTML = `
      <div class="ai-error-display">
        <div class="text-center py-6">
          <div class="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <svg class="h-8 w-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          
          <h3 class="text-lg font-medium text-gray-900 mb-2">AI分析失败</h3>
          <p class="text-gray-600 mb-1">${errorMessage}</p>
          <p class="text-sm text-gray-500 mb-6">${suggestion}</p>
          
          <div class="flex flex-col space-y-3">
            <button id="retry-ai-analysis" class="px-6 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
              重试分析
            </button>
            
            ${errorType !== 'format' ? `
              <button id="skip-ai-analysis" class="px-6 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors">
                跳过AI分析
              </button>
            ` : ''}
          </div>
        </div>
        
        <!-- 降级处理建议 -->
        <div class="mt-6 p-4 bg-yellow-50 rounded-lg">
          <div class="flex items-start space-x-3">
            <svg class="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div>
              <h4 class="text-sm font-medium text-yellow-800 mb-1">手动填写建议</h4>
              <p class="text-sm text-yellow-700">
                您可以根据图片内容手动选择事件类型和填写描述。常见类型包括：交通问题、环境问题、基础设施问题、安全问题等。
              </p>
            </div>
          </div>
        </div>
      </div>
    `;

    // 绑定按钮事件
    const retryBtn = aiResultContent.querySelector('#retry-ai-analysis');
    const skipBtn = aiResultContent.querySelector('#skip-ai-analysis');

    retryBtn.addEventListener('click', () => {
      if (this.currentMedia) {
        this.performAIAnalysis(this.currentMedia);
      }
    });

    if (skipBtn) {
      skipBtn.addEventListener('click', () => {
        this.hideAIResult();
        Notification.show('已跳过AI分析，请手动填写事件信息', 'info');
      });
    }
  }

  /**
   * 隐藏AI结果区域
   */
  hideAIResult() {
    const aiResultSection = this.container.querySelector('#ai-result-section');
    if (aiResultSection) {
      aiResultSection.classList.add('hidden');
    }
    this.aiResult = null;
  }

  /**
   * 根据AI结果自动填充表单
   */
  autoFillFormFromAI(result) {
    const form = this.container.querySelector('#event-form');

    // 填充事件类型（选择置信度最高的推荐类型）
    if (result.recommended_event_types && result.recommended_event_types.length > 0) {
      const bestType = result.recommended_event_types[0];
      const eventTypeSelect = form.querySelector('#event-type');

      // 尝试匹配事件类型选项
      const options = Array.from(eventTypeSelect.options);
      const matchingOption = options.find(option =>
        option.value === bestType.id ||
        option.textContent.includes(bestType.name)
      );

      if (matchingOption) {
        eventTypeSelect.value = matchingOption.value;
      }
    }

    // 生成智能描述
    const descriptionTextarea = form.querySelector('#event-description');
    if (!descriptionTextarea.value.trim()) {
      let description = '';

      // 基于检测结果生成描述
      if (result.detections && result.detections.length > 0) {
        const topDetections = result.detections.slice(0, 2);
        const detectionTexts = topDetections.map(d =>
          `检测到${d.label}（置信度${Math.round(d.confidence * 100)}%）`
        );
        description = detectionTexts.join('，');
      }

      // 添加AI摘要
      if (result.summary && result.summary !== '未检测到明确的事件类型') {
        if (description) description += '。';
        description += result.summary;
      }

      // 如果有原始描述，优先使用
      if (result.description) {
        description = result.description;
      }

      if (description) {
        descriptionTextarea.value = description;
        this.updateDescriptionCount(description.length);
      }
    }

    // 智能生成标题
    const titleInput = form.querySelector('#event-title');
    if (!titleInput.value.trim()) {
      let title = '';

      if (result.recommended_event_types && result.recommended_event_types.length > 0) {
        const bestType = result.recommended_event_types[0];
        title = `${bestType.name}问题上报`;
      } else if (result.detections && result.detections.length > 0) {
        const topDetection = result.detections[0];
        title = `${topDetection.label}问题上报`;
      } else {
        title = '问题上报';
      }

      titleInput.value = title;
    }

    // 根据检测结果智能设置优先级
    if (result.detections && result.detections.length > 0) {
      const topDetection = result.detections[0];
      let priority = 'medium';

      if (topDetection.confidence >= 0.8) {
        // 高置信度检测，根据类型设置优先级
        if (topDetection.label.includes('安全') || topDetection.label.includes('危险')) {
          priority = 'high';
        }
      }

      const priorityRadio = form.querySelector(`input[name="priority"][value="${priority}"]`);
      if (priorityRadio) {
        priorityRadio.checked = true;
        this.formData.priority = priority;
      }
    }

    // 触发表单验证
    this.validateForm();

    Notification.show('AI分析结果已应用到表单', 'success');
  }

  /**
   * 更新上传进度
   */
  updateUploadProgress(progress) {
    // 可以在这里显示上传进�?    console.log(`Upload progress: ${progress}%`);
  }

  /**
   * 刷新位置信息
   */
  async refreshLocation() {
    const locationInput = this.container.querySelector('#event-location');
    const refreshBtn = this.container.querySelector('#refresh-location');
    const refreshText = this.container.querySelector('#refresh-location-text');
    const accuracyDiv = this.container.querySelector('#location-accuracy');
    const accuracyText = this.container.querySelector('#location-accuracy-text');

    // 更新UI状态
    refreshBtn.disabled = true;
    refreshText.textContent = '定位中...';
    locationInput.value = '正在获取位置...';
    locationInput.readOnly = true;
    accuracyDiv.classList.add('hidden');

    try {
      const position = await this.getCurrentLocationWithAccuracy();

      if (position) {
        // 显示定位精度
        const accuracy = position.coords.accuracy;
        accuracyText.textContent = `定位精度: ${Math.round(accuracy)}米`;
        accuracyDiv.classList.remove('hidden');

        Notification.show('位置获取成功', 'success');
      }
    } catch (error) {
      console.error('Location refresh failed:', error);

      // 错误处理
      let errorMessage = '获取位置失败';
      if (error.code === 1) {
        errorMessage = '位置访问被拒绝，请允许位置权限';
      } else if (error.code === 2) {
        errorMessage = '位置信息不可用';
      } else if (error.code === 3) {
        errorMessage = '获取位置超时';
      }

      Notification.show(errorMessage + '，请手动输入', 'warning');

      // 允许手动编辑
      locationInput.readOnly = false;
      locationInput.value = '';
      locationInput.placeholder = '请手动输入位置信息（如：XX街道XX号）';
      locationInput.focus();

    } finally {
      refreshBtn.disabled = false;
      refreshText.textContent = '定位';
    }
  }

  /**
   * 获取带精度信息的当前位置
   */
  async getCurrentLocationWithAccuracy() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          this.formData.location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            address: '正在解析地址...'
          };

          // 异步解析地址
          try {
            await this.reverseGeocode(position.coords.latitude, position.coords.longitude);
          } catch (error) {
            console.warn('Address resolution failed:', error);
          }

          resolve(position);
        },
        (error) => {
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 300000
        }
      );
    });
  }

  /**
   * 更新位置显示
   */
  updateLocationDisplay() {
    const locationInput = this.container.querySelector('#event-location');
    if (this.formData.location && locationInput) {
      locationInput.value = this.formData.location.address;
    }
  }

  /**
   * 更新描述字数统计
   */
  updateDescriptionCount(count) {
    const countElement = this.container.querySelector('#description-count');
    if (countElement) {
      countElement.textContent = count;

      // 字数接近限制时改变颜色
      if (count > 450) {
        countElement.className = 'text-red-500';
      } else if (count > 400) {
        countElement.className = 'text-yellow-500';
      } else {
        countElement.className = 'text-gray-500';
      }
    }
  }

  /**
   * 处理表单字段变化
   */
  handleFormFieldChange(field) {
    const { name, value, type } = field;

    // 标记用户已交互
    this.hasUserInteracted = true;

    if (type === 'radio') {
      if (field.checked) {
        this.formData[name] = value;
      }
    } else {
      this.formData[name] = value;
    }

    // 特殊处理位置字段
    if (name === 'location') {
      if (this.formData.location && typeof this.formData.location === 'object') {
        this.formData.location.address = value;
      } else {
        this.formData.location = { address: value };
      }
    }

    // 验证表单
    this.validateForm();

    // 提供实时反馈
    this.provideFieldFeedback(field);
  }

  /**
   * 提供字段级反馈
   */
  provideFieldFeedback(field) {
    const { name, value } = field;

    // 移除之前的反馈
    const existingFeedback = field.parentNode.querySelector('.field-feedback');
    if (existingFeedback) {
      existingFeedback.remove();
    }

    let feedback = null;

    switch (name) {
      case 'title':
        if (value.length > 0 && value.length < 2) {
          feedback = { type: 'warning', message: '标题太短' };
        } else if (value.length > 90) {
          feedback = { type: 'warning', message: `还可输入${100 - value.length}个字符` };
        } else if (value.length >= 2) {
          feedback = { type: 'success', message: '标题格式正确' };
        }
        break;

      case 'description':
        if (value.length > 0 && value.length < 10) {
          feedback = { type: 'warning', message: `至少需要${10 - value.length}个字符` };
        } else if (value.length >= 10) {
          feedback = { type: 'success', message: '描述详细度良好' };
        }
        break;

      case 'location':
        if (value.length >= 2) {
          feedback = { type: 'success', message: '位置信息已填好' };
        }
        break;
    }

    if (feedback) {
      this.showFieldFeedback(field, feedback);
    }
  }

  /**
   * 显示字段反馈
   */
  showFieldFeedback(field, feedback) {
    const feedbackElement = document.createElement('div');
    feedbackElement.className = `field-feedback text-xs mt-1 ${feedback.type === 'success' ? 'text-green-600' :
      feedback.type === 'warning' ? 'text-yellow-600' :
        'text-red-600'
      }`;
    feedbackElement.textContent = feedback.message;

    field.parentNode.appendChild(feedbackElement);

    // 自动移除成功反馈
    if (feedback.type === 'success') {
      setTimeout(() => {
        if (feedbackElement.parentNode) {
          feedbackElement.remove();
        }
      }, 3000);
    }
  }

  /**
   * 验证表单
   */
  validateForm() {
    const submitBtn = this.container.querySelector('#submit-event');
    const form = this.container.querySelector('#event-form');

    const title = form.querySelector('#event-title').value.trim();
    const eventType = form.querySelector('#event-type').value;
    const description = form.querySelector('#event-description').value.trim();
    const location = form.querySelector('#event-location').value.trim();

    // 验证规则
    const validations = {
      title: {
        valid: title.length >= 2 && title.length <= 100,
        message: '标题长度应在2-100字符之间'
      },
      eventType: {
        valid: eventType !== '',
        message: '请选择事件类型'
      },
      description: {
        valid: description.length >= 10 && description.length <= 500,
        message: '描述长度应在10-500字符之间'
      },
      location: {
        valid: location.length >= 2,
        message: '请提供位置信息'
      },
      media: {
        valid: this.currentMedia || description.length >= 20,
        message: '请上传媒体文件或提供详细描述（至少20个字符）'
      }
    };

    // 检查所有验证规则
    const failedValidations = Object.entries(validations).filter(([key, rule]) => !rule.valid);
    const isValid = failedValidations.length === 0;

    // 更新提交按钮状态
    submitBtn.disabled = !isValid || this.isSubmitting;

    // 显示验证提示（可选）
    if (failedValidations.length > 0 && this.hasUserInteracted) {
      const firstFailure = failedValidations[0][1];
      this.showValidationHint(firstFailure.message);
    } else {
      this.hideValidationHint();
    }

    return isValid;
  }

  /**
   * 显示验证提示
   */
  showValidationHint(message) {
    let hintElement = this.container.querySelector('#validation-hint');

    if (!hintElement) {
      hintElement = document.createElement('div');
      hintElement.id = 'validation-hint';
      hintElement.className = 'validation-hint mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800';

      const submitBtn = this.container.querySelector('#submit-event');
      submitBtn.parentNode.insertBefore(hintElement, submitBtn);
    }

    hintElement.textContent = message;
    hintElement.style.display = 'block';
  }

  /**
   * 隐藏验证提示
   */
  hideValidationHint() {
    const hintElement = this.container.querySelector('#validation-hint');
    if (hintElement) {
      hintElement.style.display = 'none';
    }
  }

  /**
   * 处理表单提交
   */
  async handleFormSubmit() {
    if (this.isSubmitting) return;

    try {
      this.isSubmitting = true;
      this.showSubmitLoading(true);

      // 收集表单数据
      const formData = this.collectFormData();

      // 验证数据
      if (!this.validateFormData(formData)) {
        return;
      }

      // 显示提交进度
      this.showSubmitProgress('正在上传数据...');

      // 如果有媒体文件但还没上传，先上传
      if (this.currentMedia && !this.currentMedia.uploadedUrl) {
        this.showSubmitProgress('正在上传媒体文件...');
        const uploadResult = await this.fileService.uploadFile(this.currentMedia.file, (progress) => {
          this.showSubmitProgress(`上传中.. ${progress}%`);
        });

        if (!uploadResult.success) {
          throw new Error('媒体文件上传失败');
        }

        this.currentMedia.uploadedUrl = uploadResult.data.url;
        formData.mediaFiles = [{
          url: uploadResult.data.url,
          type: this.currentMedia.type,
          name: this.currentMedia.name,
          size: this.currentMedia.size
        }];
      }

      // 提交事件
      this.showSubmitProgress('正在创建事件...');
      const result = await this.eventService.createEvent(formData);

      if (result.success) {
        // 更新事件存储
        this.eventStore.addEvent(result.data);

        // 显示成功反馈
        this.showSubmitSuccess(result.data);

        // 重置表单
        setTimeout(() => {
          this.resetForm();
        }, 2000);

      } else {
        throw new Error(result.message || '提交失败');
      }

    } catch (error) {
      console.error('Submit event failed:', error);
      this.showSubmitError(error);
    } finally {
      this.isSubmitting = false;
      this.showSubmitLoading(false);
    }
  }

  /**
   * 显示提交进度
   */
  showSubmitProgress(message) {
    const submitText = this.container.querySelector('#submit-text');
    if (submitText) {
      submitText.textContent = message;
    }
  }

  /**
   * 显示提交成功
   */
  showSubmitSuccess(eventData) {
    // 显示成功通知
    Notification.show('事件提交成功', 'success');

    // 创建成功反馈模态框
    const successModal = this.createSuccessModal(eventData);
    document.body.appendChild(successModal);

    // 自动关闭模态框
    setTimeout(() => {
      this.closeSuccessModal(successModal);
    }, 5000);
  }

  /**
   * 创建成功反馈模态框
   */
  createSuccessModal(eventData) {
    const modal = document.createElement('div');
    modal.className = 'success-modal fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';

    modal.innerHTML = `
      <div class="success-content bg-white rounded-2xl p-6 max-w-sm w-full animate-bounce-in">
        <div class="text-center">
          <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          
          <h3 class="text-lg font-semibold text-gray-900 mb-2">提交成功</h3>
          <p class="text-gray-600 mb-4">您的事件已成功提交，我们会尽快处理</p>
          
          <div class="bg-gray-50 rounded-lg p-3 mb-4 text-left">
            <div class="text-sm text-gray-600">
              <div class="flex justify-between mb-1">
                <span>事件编号:</span>
                <span class="font-mono">${eventData.id || 'N/A'}</span>
              </div>
              <div class="flex justify-between mb-1">
                <span>提交时间:</span>
                <span>${new Date().toLocaleString()}</span>
              </div>
              <div class="flex justify-between">
                <span>预计处理:</span>
                <span>24小时</span>
              </div>
            </div>
          </div>
          
          <div class="flex space-x-3">
            <button class="close-success-modal flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors">
              继续上报
            </button>
            <button class="view-tracking flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
              查看跟踪
            </button>
          </div>
        </div>
      </div>
    `;

    // 绑定事件
    const closeBtn = modal.querySelector('.close-success-modal');
    const trackingBtn = modal.querySelector('.view-tracking');

    closeBtn.addEventListener('click', () => {
      this.closeSuccessModal(modal);
    });

    trackingBtn.addEventListener('click', () => {
      this.closeSuccessModal(modal);
      // 跳转到跟踪页面
      const navigationEvent = new CustomEvent('navigate', {
        detail: { path: '/tracking', tabId: 'tracking' }
      });
      document.dispatchEvent(navigationEvent);
    });

    // 点击背景关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        this.closeSuccessModal(modal);
      }
    });

    return modal;
  }

  /**
   * 关闭成功模态框
   */
  closeSuccessModal(modal) {
    if (modal && modal.parentNode) {
      modal.classList.add('animate-fade-out');
      setTimeout(() => {
        modal.parentNode.removeChild(modal);
      }, 300);
    }
  }

  /**
   * 显示提交错误
   */
  showSubmitError(error) {
    let errorMessage = '提交失败，请重试';
    let suggestion = '';

    if (error.message) {
      if (error.message.includes('网络')) {
        errorMessage = '网络连接失败';
        suggestion = '请检查网络连接后重试';
      } else if (error.message.includes('上传')) {
        errorMessage = '文件上传失败';
        suggestion = '请检查文件大小和格式';
      } else if (error.message.includes('验证')) {
        errorMessage = '数据验证失败';
        suggestion = '请检查填写的信息是否完整';
      } else {
        errorMessage = error.message;
      }
    }

    // 显示错误通知
    Notification.show(errorMessage, 'error');

    // 如果有建议，显示额外提示
    if (suggestion) {
      setTimeout(() => {
        Notification.show(suggestion, 'info');
      }, 1000);
    }
  }

  /**
   * 收集表单数据
   */
  collectFormData() {
    const form = this.container.querySelector('#event-form');

    // 基础表单数据
    const formData = {
      title: form.querySelector('#event-title').value.trim(),
      description: form.querySelector('#event-description').value.trim(),
      event_type: form.querySelector('#event-type').value,
      priority: form.querySelector('input[name="priority"]:checked').value,
      timestamp: new Date().toISOString()
    };

    // 位置信息 - 后端API期望latitude, longitude, address作为直接字段
    if (this.formData.location) {
      if (typeof this.formData.location === 'object') {
        formData.address = this.formData.location.address || '';
        formData.latitude = this.formData.location.latitude || null;
        formData.longitude = this.formData.location.longitude || null;
      } else {
        formData.address = this.formData.location;
        formData.latitude = null;
        formData.longitude = null;
      }
    } else {
      formData.address = form.querySelector('#event-location').value.trim();
      formData.latitude = null;
      formData.longitude = null;
    }

    // 媒体文件信息
    formData.media_files = [];
    if (this.currentMedia) {
      formData.media_files.push({
        url: this.currentMedia.uploadedUrl || '',
        type: this.currentMedia.type,
        name: this.currentMedia.name,
        size: this.currentMedia.size,
        capture_type: this.currentMedia.captureType || 'unknown'
      });
    }

    // AI分析结果
    if (this.aiResult) {
      formData.ai_analysis = {
        detections: this.aiResult.detections || [],
        recommended_event_types: this.aiResult.recommended_event_types || [],
        summary: this.aiResult.summary || '',
        confidence_score: this.aiResult.detections && this.aiResult.detections.length > 0
          ? this.aiResult.detections[0].confidence
          : 0,
        analysis_type: this.aiResult.analysis_type || 'image',
        processed_at: this.aiResult.processed_at || new Date().toISOString()
      };
    }

    // 用户信息（从用户存储获取）
    const userState = this.userStore.getState();
    if (userState.user) {
      formData.reporter_id = userState.user.id;
      formData.reporter_name = userState.user.name || userState.user.username;
    }

    // 设备信息
    formData.device_info = {
      user_agent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      screen_resolution: `${screen.width}x${screen.height}`,
      timestamp: new Date().toISOString()
    };

    return formData;
  }

  /**
   * 验证表单数据
   */
  validateFormData(data) {
    if (!data.title) {
      Notification.show('请输入事件标题', 'error');
      return false;
    }

    if (!data.eventType) {
      Notification.show('请选择事件类型', 'error');
      return false;
    }

    if (!data.description) {
      Notification.show('请输入事件描述', 'error');
      return false;
    }

    if (data.description.length < 10) {
      Notification.show('事件描述至少需要10个字符', 'error');
      return false;
    }

    return true;
  }

  /**
   * 显示/隐藏提交加载状态
   */
  showSubmitLoading(show) {
    const submitText = this.container.querySelector('#submit-text');
    const submitLoading = this.container.querySelector('#submit-loading');
    const submitBtn = this.container.querySelector('#submit-event');

    if (show) {
      submitText.classList.add('hidden');
      submitLoading.classList.remove('hidden');
      submitBtn.disabled = true;
    } else {
      submitText.classList.remove('hidden');
      submitLoading.classList.add('hidden');
      submitBtn.disabled = false;
    }
  }

  /**
   * 重置表单
   */
  resetForm() {
    const form = this.container.querySelector('#event-form');
    form.reset();

    // 重置表单数据
    const currentLocation = this.formData.location; // 保留位置信息
    this.formData = {
      title: '',
      description: '',
      location: currentLocation,
      priority: 'medium',
      eventType: '',
      mediaFiles: []
    };

    // 重置用户交互标志
    this.hasUserInteracted = false;

    // 重置媒体和AI结果
    this.removeCurrentMedia();

    // 重置字数统计
    this.updateDescriptionCount(0);

    // 清除验证提示
    this.hideValidationHint();

    // 清除字段反馈
    const fieldFeedbacks = this.container.querySelectorAll('.field-feedback');
    fieldFeedbacks.forEach(feedback => feedback.remove());

    // 重置优先级为中等
    const mediumPriorityRadio = form.querySelector('input[name="priority"][value="medium"]');
    if (mediumPriorityRadio) {
      mediumPriorityRadio.checked = true;
    }

    // 如果没有位置信息，重新获取
    if (!currentLocation || !currentLocation.address) {
      this.getCurrentLocation();
    }

    // 重新验证表单
    setTimeout(() => {
      this.validateForm();
    }, 100);

    // 显示重置成功提示
    Notification.show('表单已重置，可以继续上报新事件', 'info');
  }

  /**
   * 处理媒体错误
   */
  handleMediaError(error) {
    console.error('Media capture error:', error);
    Notification.show(error.message || '媒体采集失败', 'error');
  }

  /**
   * 处理未认证状态
   */
  handleUnauthenticated() {
    Notification.show('请先登录', 'warning');
    // 跳转到登录页面
    setTimeout(() => {
      const navigationEvent = new CustomEvent('navigate', {
        detail: { path: '/login', tabId: 'login' }
      });
      document.dispatchEvent(navigationEvent);
    }, 1500);
  }

  /**
   * 处理事件状态变化
   */
  handleEventStateChange(state) {
    // 可以在这里处理事件状态的变化
    // 比如更新UI显示最新的事件数据
  }

  /**
   * 挂载到DOM
   */
  mount(parent = document.body) {
    if (!this.container) {
      this.render();
    }
    parent.appendChild(this.container);
    return this;
  }

  /**
   * 从DOM卸载
   */
  unmount() {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    return this;
  }

  /**
   * 销毁组件
   */
  destroy() {
    // 清理事件监听器
    if (this.navigation) {
      this.navigation.destroy();
    }

    if (this.mediaCapture) {
      this.mediaCapture.destroy();
    }

    // 卸载组件
    this.unmount();

    // 清理引用
    this.container = null;
    this.navigation = null;
    this.mediaCapture = null;
    this.currentMedia = null;
    this.aiResult = null;
  }
}