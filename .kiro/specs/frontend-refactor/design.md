# 前端重构设计文档

## 概述

本设计文档详细描述了基层治理智能体前端重构的技术架构、组件设计、API集成方案和实现细节。重构目标是将现有frontend_bak目录下的前端代码迁移到frontend目录，实现现代化的前端架构，完全对接后端API，并保持原有的用户体验。

## 架构设计

### 整体架构

```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   ├── pages/              # 页面组件
│   ├── services/           # API服务层
│   ├── utils/              # 工具函数
│   ├── stores/             # 状态管理
│   ├── styles/             # 样式文件
│   └── assets/             # 静态资源
├── public/                 # 公共资源
├── dist/                   # 构建输出
├── package.json           # 项目配置
├── vite.config.js         # 构建配置
└── index.html             # 入口文件
```

### 技术栈选择

- **构建工具**: Vite - 快速的现代化构建工具
- **JavaScript**: ES6+ 模块化开发
- **CSS框架**: Tailwind CSS - 保持原有设计风格
- **状态管理**: 原生JavaScript + LocalStorage
- **HTTP客户端**: Fetch API + 自定义封装
- **动画库**: Anime.js - 保持原有动画效果
- **图标**: Heroicons - SVG图标库

## 组件设计

### 核心组件架构

#### 1. 应用入口组件 (App)
```javascript
class App {
  constructor() {
    this.router = new Router();
    this.authService = new AuthService();
    this.init();
  }
  
  async init() {
    await this.checkAuthStatus();
    this.setupGlobalEventListeners();
    this.router.start();
  }
}
```

#### 2. 路由管理 (Router)
```javascript
class Router {
  constructor() {
    this.routes = {
      '/': () => import('./pages/HomePage.js'),
      '/tracking': () => import('./pages/TrackingPage.js'),
      '/profile': () => import('./pages/ProfilePage.js')
    };
  }
  
  async navigate(path) {
    const pageModule = await this.routes[path]();
    const page = new pageModule.default();
    page.render();
  }
}
```

#### 3. 页面组件基类 (BasePage)
```javascript
class BasePage {
  constructor() {
    this.container = null;
    this.state = {};
  }
  
  render() {
    this.container = document.createElement('div');
    this.container.innerHTML = this.template();
    this.bindEvents();
    this.mount();
  }
  
  template() {
    // 子类实现
  }
  
  bindEvents() {
    // 事件绑定
  }
  
  mount() {
    document.body.appendChild(this.container);
  }
}
```

### 页面组件设计

#### 1. 首页组件 (HomePage)
- **功能**: 事件上报、媒体采集、AI识别
- **状态管理**: 当前媒体、识别结果、表单数据
- **API集成**: 文件上传、AI分析、事件创建

#### 2. 跟踪页面组件 (TrackingPage)  
- **功能**: 事件列表、状态筛选、详情查看
- **状态管理**: 事件列表、筛选条件、分页信息
- **API集成**: 事件查询、事件详情、时间线获取

#### 3. 个人页面组件 (ProfilePage)
- **功能**: 用户信息、设置管理、统计数据
- **状态管理**: 用户信息、应用设置、统计数据
- **API集成**: 用户资料、统计查询、设置更新

### 可复用组件设计

#### 1. 导航组件 (Navigation)
```javascript
class Navigation {
  constructor(activeTab = 'home') {
    this.activeTab = activeTab;
  }
  
  render() {
    return `
      <nav class="nav-bottom">
        <div class="flex items-center justify-around py-3">
          ${this.renderNavItem('home', '上报', 'index.html')}
          ${this.renderNavItem('tracking', '跟踪', 'tracking.html')}
          ${this.renderNavItem('profile', '我的', 'profile.html')}
        </div>
      </nav>
    `;
  }
}
```

#### 2. 模态框组件 (Modal)
```javascript
class Modal {
  constructor(title, content, options = {}) {
    this.title = title;
    this.content = content;
    this.options = options;
  }
  
  show() {
    this.render();
    this.animate();
  }
  
  hide() {
    this.animateOut(() => this.destroy());
  }
}
```

#### 3. 通知组件 (Notification)
```javascript
class Notification {
  static show(message, type = 'info', duration = 3000) {
    const notification = new Notification(message, type);
    notification.render();
    setTimeout(() => notification.hide(), duration);
  }
}
```

## API服务层设计

### API客户端架构

#### 1. 基础HTTP客户端 (HttpClient)
```javascript
class HttpClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.interceptors = {
      request: [],
      response: []
    };
  }
  
  async request(url, options = {}) {
    // 请求拦截器
    const config = this.applyRequestInterceptors(url, options);
    
    try {
      const response = await fetch(config.url, config.options);
      const data = await response.json();
      
      // 响应拦截器
      return this.applyResponseInterceptors(data, response);
    } catch (error) {
      throw this.handleError(error);
    }
  }
}
```

#### 2. 认证服务 (AuthService)
```javascript
class AuthService extends HttpClient {
  constructor() {
    super('/api/v1/auth');
    this.token = localStorage.getItem('access_token');
  }
  
  async login(credentials) {
    const response = await this.post('/login', credentials);
    if (response.success) {
      this.setToken(response.data.access_token);
    }
    return response;
  }
  
  async register(userData) {
    return await this.post('/register', userData);
  }
  
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    return await this.post('/refresh', { refresh_token: refreshToken });
  }
}
```

#### 3. 事件服务 (EventService)
```javascript
class EventService extends HttpClient {
  constructor() {
    super('/api/v1/events');
  }
  
  async createEvent(eventData) {
    return await this.post('/', eventData);
  }
  
  async getEvents(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return await this.get(`/?${queryString}`);
  }
  
  async getEventDetail(eventId) {
    return await this.get(`/${eventId}`);
  }
  
  async getEventTimeline(eventId) {
    return await this.get(`/${eventId}/timeline`);
  }
}
```

#### 4. AI服务 (AIService)
```javascript
class AIService extends HttpClient {
  constructor() {
    super('/api/v1/ai');
  }
  
  async analyzeImage(imageUrl) {
    return await this.post('/analyze-image', { image_url: imageUrl });
  }
  
  async analyzeVideo(videoUrl) {
    return await this.post('/analyze-video', { video_url: videoUrl });
  }
  
  async getEventTypes() {
    return await this.get('/event-types');
  }
}
```

#### 5. 文件服务 (FileService)
```javascript
class FileService extends HttpClient {
  constructor() {
    super('/api/v1/files');
  }
  
  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);
    
    return await this.upload('/upload', formData, onProgress);
  }
  
  async upload(url, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
      
      xhr.onload = () => {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error('Upload failed'));
        }
      };
      
      xhr.open('POST', this.baseURL + url);
      xhr.setRequestHeader('Authorization', `Bearer ${this.getToken()}`);
      xhr.send(formData);
    });
  }
}
```

## 状态管理设计

### 状态管理架构

#### 1. 状态存储 (Store)
```javascript
class Store {
  constructor(initialState = {}) {
    this.state = initialState;
    this.listeners = [];
  }
  
  getState() {
    return { ...this.state };
  }
  
  setState(newState) {
    this.state = { ...this.state, ...newState };
    this.notifyListeners();
  }
  
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
  
  notifyListeners() {
    this.listeners.forEach(listener => listener(this.state));
  }
}
```

#### 2. 用户状态管理 (UserStore)
```javascript
class UserStore extends Store {
  constructor() {
    super({
      user: null,
      isAuthenticated: false,
      token: localStorage.getItem('access_token')
    });
  }
  
  setUser(user) {
    this.setState({ 
      user, 
      isAuthenticated: true 
    });
  }
  
  clearUser() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.setState({ 
      user: null, 
      isAuthenticated: false, 
      token: null 
    });
  }
}
```

#### 3. 事件状态管理 (EventStore)
```javascript
class EventStore extends Store {
  constructor() {
    super({
      events: [],
      currentEvent: null,
      filters: { status: 'all' },
      pagination: { page: 1, pageSize: 20 }
    });
  }
  
  setEvents(events) {
    this.setState({ events });
  }
  
  addEvent(event) {
    const events = [event, ...this.state.events];
    this.setState({ events });
  }
  
  updateEvent(eventId, updates) {
    const events = this.state.events.map(event => 
      event.id === eventId ? { ...event, ...updates } : event
    );
    this.setState({ events });
  }
}
```

## 用户界面设计

### 响应式设计

#### 1. 移动优先设计
- 基础设计针对移动设备（320px-768px）
- 使用Tailwind CSS的响应式类
- 触摸友好的交互元素（最小44px点击区域）

#### 2. 布局系统
```css
/* 容器布局 */
.container {
  @apply max-w-md mx-auto bg-gray-50 min-h-screen;
}

/* 页面布局 */
.page-content {
  @apply px-4 pb-20; /* 底部导航高度 */
}

/* 卡片布局 */
.glass-card {
  @apply bg-white bg-opacity-95 backdrop-blur-sm border border-white border-opacity-20 rounded-2xl shadow-lg;
}
```

### 动画设计

#### 1. 页面转场动画
```javascript
class PageTransition {
  static fadeIn(element) {
    return anime({
      targets: element,
      opacity: [0, 1],
      translateY: [30, 0],
      duration: 600,
      easing: 'easeOutQuart'
    });
  }
  
  static slideUp(element) {
    return anime({
      targets: element,
      translateY: [100, 0],
      opacity: [0, 1],
      duration: 400,
      easing: 'easeOutQuart'
    });
  }
}
```

#### 2. 交互反馈动画
```javascript
class InteractionAnimations {
  static buttonPress(button) {
    anime({
      targets: button,
      scale: [1, 0.95, 1],
      duration: 200,
      easing: 'easeOutQuart'
    });
  }
  
  static cardHover(card) {
    anime({
      targets: card,
      translateY: [-2, 0],
      boxShadow: ['0 4px 6px rgba(0,0,0,0.1)', '0 10px 25px rgba(0,0,0,0.15)'],
      duration: 300,
      easing: 'easeOutQuart'
    });
  }
}
```

## 性能优化设计

### 1. 代码分割
```javascript
// 动态导入页面组件
const HomePage = () => import('./pages/HomePage.js');
const TrackingPage = () => import('./pages/TrackingPage.js');
const ProfilePage = () => import('./pages/ProfilePage.js');
```

### 2. 图片优化
```javascript
class ImageOptimizer {
  static compress(file, quality = 0.8) {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob(resolve, 'image/jpeg', quality);
      };
      
      img.src = URL.createObjectURL(file);
    });
  }
}
```

### 3. 缓存策略
```javascript
class CacheManager {
  constructor() {
    this.cache = new Map();
    this.maxAge = 5 * 60 * 1000; // 5分钟
  }
  
  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > this.maxAge) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
}
```

## 错误处理设计

### 1. 全局错误处理
```javascript
class ErrorHandler {
  static init() {
    window.addEventListener('error', this.handleError);
    window.addEventListener('unhandledrejection', this.handlePromiseRejection);
  }
  
  static handleError(event) {
    console.error('Global error:', event.error);
    this.showErrorNotification('应用发生错误，请刷新页面重试');
  }
  
  static handlePromiseRejection(event) {
    console.error('Unhandled promise rejection:', event.reason);
    this.showErrorNotification('网络请求失败，请检查网络连接');
  }
}
```

### 2. API错误处理
```javascript
class APIErrorHandler {
  static handle(error, context) {
    switch (error.status) {
      case 401:
        this.handleUnauthorized();
        break;
      case 403:
        this.handleForbidden();
        break;
      case 404:
        this.handleNotFound(context);
        break;
      case 500:
        this.handleServerError();
        break;
      default:
        this.handleGenericError(error);
    }
  }
}
```

## 安全设计

### 1. Token管理
```javascript
class TokenManager {
  static setToken(token) {
    localStorage.setItem('access_token', token);
  }
  
  static getToken() {
    return localStorage.getItem('access_token');
  }
  
  static clearToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
  
  static isTokenExpired(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return Date.now() >= payload.exp * 1000;
    } catch {
      return true;
    }
  }
}
```

### 2. 输入验证
```javascript
class Validator {
  static validatePhone(phone) {
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
  }
  
  static validatePassword(password) {
    return password.length >= 6 && password.length <= 20;
  }
  
  static sanitizeInput(input) {
    return input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  }
}
```

## 测试策略

### 1. 单元测试
- 工具函数测试
- 组件逻辑测试
- API服务测试

### 2. 集成测试
- 页面功能测试
- API集成测试
- 用户流程测试

### 3. 端到端测试
- 完整用户场景测试
- 跨浏览器兼容性测试
- 性能测试

## 部署配置

### 1. 构建配置 (vite.config.js)
```javascript
export default {
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['anime'],
          utils: ['./src/utils/index.js']
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
};
```

### 2. 环境配置
```javascript
const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000/api/v1',
    DEBUG: true
  },
  production: {
    API_BASE_URL: '/api/v1',
    DEBUG: false
  }
};
```

这个设计文档提供了完整的技术架构和实现方案，确保重构后的前端代码具有良好的可维护性、性能和用户体验。