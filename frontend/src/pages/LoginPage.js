/**
 * 登录页面组件
 * 实现用户登录和注册功能
 */
import { Navigation } from '../components/Navigation.js';
import { Modal } from '../components/Modal.js';
import { Notification } from '../components/Notification.js';
import { AuthService } from '../services/AuthService.js';
import { connectionStatus } from '../components/ConnectionStatus.js';
import { networkDetector } from '../utils/NetworkDetector.js';
import { mobileApiConfig } from '../utils/MobileApiConfig.js';
import UserStore from '../stores/UserStore.js';

export class LoginPage {
  constructor(options = {}) {
    this.container = null;
    this.navigation = null;
    this.currentModal = null;
    
    // 服务实例
    this.authService = new AuthService();
    
    // 状态管理
    this.userStore = UserStore;
    
    // 表单状态
    this.isLoginMode = true;
    this.isLoading = false;
    
    // 连接状态
    this.connectionStatus = connectionStatus;
    
    this.init();
  }

  /**
   * 初始化组件
   */
  init() {
    // 监听用户状态变化
    this.userStore.subscribe((state) => {
      if (state.isAuthenticated) {
        // 用户已登录，跳转到首页
        this.handleNavigation('/', 'home');
      }
    });
  }

  /**
   * 渲染页面
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'login-page min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100';
    
    this.container.innerHTML = this.getPageHTML();
    
    // 渲染子组件
    this.renderComponents();
    
    // 绑定事件
    this.bindEvents();
    
    return this.container;
  }

  /**
   * 获取页面HTML
   */
  getPageHTML() {
    return `
      <div class="flex flex-col min-h-screen">
        <!-- 头部 -->
        <div class="flex-1 flex items-center justify-center px-4 py-12">
          <div class="max-w-md w-full space-y-8">
            <!-- Logo和标题 -->
            <div class="text-center">
              <div class="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center">
                <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                </svg>
              </div>
              <h2 class="mt-6 text-3xl font-extrabold text-gray-900">
                基层治理智能体
              </h2>
              <p class="mt-2 text-sm text-gray-600">
                <span class="login-mode-text">${this.isLoginMode ? '登录您的账户' : '创建新账户'}</span>
              </p>
            </div>

            <!-- 登录/注册表单 -->
            <form class="mt-8 space-y-6" id="auth-form">
              <div class="space-y-4">
                <!-- 手机号 -->
                <div>
                  <label for="phone" class="sr-only">手机号</label>
                  <input id="phone" name="phone" type="tel" required 
                         class="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                         placeholder="手机号">
                </div>

                <!-- 密码 -->
                <div>
                  <label for="password" class="sr-only">密码</label>
                  <input id="password" name="password" type="password" required 
                         class="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                         placeholder="密码">
                </div>

                <!-- 注册时的额外字段 -->
                <div class="register-fields" style="display: ${this.isLoginMode ? 'none' : 'block'}">
                  <div>
                    <label for="name" class="sr-only">姓名</label>
                    <input id="name" name="name" type="text" 
                           class="appearance-none rounded-lg relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                           placeholder="姓名">
                  </div>
                  
                  <div class="mt-4 flex space-x-2">
                    <input id="verification-code" name="verification_code" type="text" 
                           class="flex-1 appearance-none rounded-lg relative block px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm" 
                           placeholder="验证码">
                    <button type="button" id="send-code-btn" 
                            class="px-4 py-3 border border-transparent text-sm font-medium rounded-lg text-blue-600 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                      发送验证码
                    </button>
                  </div>
                </div>
              </div>

              <!-- 登录选项 -->
              <div class="login-options" style="display: ${this.isLoginMode ? 'flex' : 'none'}">
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <input id="remember-me" name="remember-me" type="checkbox" 
                           class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                    <label for="remember-me" class="ml-2 block text-sm text-gray-900">
                      记住我
                    </label>
                  </div>

                  <div class="text-sm">
                    <a href="#" class="font-medium text-blue-600 hover:text-blue-500" id="forgot-password-link">
                      忘记密码？
                    </a>
                  </div>
                </div>
              </div>

              <!-- 提交按钮 -->
              <div>
                <button type="submit" id="submit-btn"
                        class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed">
                  <span class="absolute left-0 inset-y-0 flex items-center pl-3">
                    <svg class="h-5 w-5 text-blue-500 group-hover:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"></path>
                    </svg>
                  </span>
                  <span class="submit-text">${this.isLoginMode ? '登录' : '注册'}</span>
                  <span class="loading-spinner hidden ml-2">
                    <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </span>
                </button>
              </div>

              <!-- 切换模式 -->
              <div class="text-center">
                <button type="button" id="toggle-mode-btn" class="font-medium text-blue-600 hover:text-blue-500">
                  <span class="toggle-text">${this.isLoginMode ? '没有账户？立即注册' : '已有账户？立即登录'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- 底部导航容器 -->
        <div id="navigation-container" class="navigation-container">
          <!-- Navigation 组件将在这里渲染 -->
        </div>
      </div>
    `;
  }

  /**
   * 渲染子组件
   */
  renderComponents() {
    // 渲染导航组件
    this.navigation = new Navigation({
      activeTab: 'login',
      onNavigate: (path, tabId) => this.handleNavigation(path, tabId)
    });

    const navContainer = this.container.querySelector('#navigation-container');
    this.navigation.mount(navContainer);
    
    // 连接状态组件已移除
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 表单提交
    const form = this.container.querySelector('#auth-form');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });

    // 切换登录/注册模式
    const toggleBtn = this.container.querySelector('#toggle-mode-btn');
    toggleBtn.addEventListener('click', () => {
      this.toggleMode();
    });

    // 发送验证码
    const sendCodeBtn = this.container.querySelector('#send-code-btn');
    sendCodeBtn.addEventListener('click', () => {
      this.sendVerificationCode();
    });

    // 忘记密码
    const forgotPasswordLink = this.container.querySelector('#forgot-password-link');
    forgotPasswordLink.addEventListener('click', (e) => {
      e.preventDefault();
      this.showForgotPasswordModal();
    });
  }

  /**
   * 切换登录/注册模式
   */
  toggleMode() {
    this.isLoginMode = !this.isLoginMode;
    
    // 更新UI
    const loginModeText = this.container.querySelector('.login-mode-text');
    const registerFields = this.container.querySelector('.register-fields');
    const loginOptions = this.container.querySelector('.login-options');
    const submitText = this.container.querySelector('.submit-text');
    const toggleText = this.container.querySelector('.toggle-text');

    loginModeText.textContent = this.isLoginMode ? '登录您的账户' : '创建新账户';
    registerFields.style.display = this.isLoginMode ? 'none' : 'block';
    loginOptions.style.display = this.isLoginMode ? 'flex' : 'none';
    submitText.textContent = this.isLoginMode ? '登录' : '注册';
    toggleText.textContent = this.isLoginMode ? '没有账户？立即注册' : '已有账户？立即登录';

    // 清空表单
    const form = this.container.querySelector('#auth-form');
    form.reset();
  }

  /**
   * 处理表单提交
   */
  async handleSubmit() {
    if (this.isLoading) return;

    const form = this.container.querySelector('#auth-form');
    const formData = new FormData(form);
    
    const phone = formData.get('phone');
    const password = formData.get('password');

    // 验证输入
    if (!this.validateInput(phone, password)) {
      return;
    }

    // 检查网络连接
    if (!navigator.onLine) {
      this.showError('网络连接已断开，请检查网络后重试');
      return;
    }

    this.setLoading(true);

    try {
      if (this.isLoginMode) {
        await this.handleLogin(phone, password);
      } else {
        const name = formData.get('name');
        const verificationCode = formData.get('verification_code');
        await this.handleRegister(phone, password, name, verificationCode);
      }
    } catch (error) {
      console.error('登录/注册失败:', error);
      
      // 根据错误类型提供不同的处理
      let errorMessage = error.message || '操作失败';
      
      if (error.message && error.message.includes('fetch')) {
        errorMessage = '无法连接到服务器，请检查网络连接';
        // 重新检测API服务器
        networkDetector.detectApiServer();
      } else if (error.message && error.message.includes('401')) {
        errorMessage = '手机号或密码错误';
      } else if (error.message && error.message.includes('500')) {
        errorMessage = '服务器内部错误，请稍后重试';
      }
      
      this.showError(errorMessage);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * 处理移动端登录
   */
  async handleMobileLogin(phone, password) {
    console.log('📱 开始移动端登录流程');
    
    try {
      // 配置移动端API
      await mobileApiConfig.configureMobileApi();
      
      // 测试移动端登录
      const result = await mobileApiConfig.testLogin(phone, password);
      
      if (result.success) {
        // 保存token到localStorage
        if (result.data.data && result.data.data.access_token) {
          localStorage.setItem('access_token', result.data.data.access_token);
          if (result.data.data.refresh_token) {
            localStorage.setItem('refresh_token', result.data.data.refresh_token);
          }
          
          // 更新UserStore
          const userStore = (await import('../stores/UserStore.js')).default;
          userStore.setUser(result.data.data.user);
          userStore.setTokens(result.data.data.access_token, result.data.data.refresh_token);
        }
        
        this.showSuccess('移动端登录成功');
        
        // 跳转到首页
        setTimeout(() => {
          this.handleNavigation('/', 'home');
        }, 1000);
      } else {
        throw new Error(result.error || '移动端登录失败');
      }
    } catch (error) {
      console.error('移动端登录失败:', error);
      // 如果移动端登录失败，尝试普通登录
      console.log('📱 移动端登录失败，尝试普通登录');
      await this.handleLogin(phone, password);
    }
  }

  /**
   * 处理登录
   */
  async handleLogin(phone, password) {
    const result = await this.authService.login({ phone, password });
    
    if (result.success) {
      // 确保用户状态已更新
      const userStore = (await import('../stores/UserStore.js')).default;
      
      // 等待一下确保状态更新完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      this.showSuccess('登录成功');
      
      // 跳转到首页
      setTimeout(() => {
        this.handleNavigation('/', 'home');
      }, 1000);
    } else {
      throw new Error(result.message || '登录失败');
    }
  }

  /**
   * 处理注册
   */
  async handleRegister(phone, password, name, verificationCode) {
    if (!name || !verificationCode) {
      throw new Error('请填写完整信息');
    }

    const result = await this.authService.register({
      phone,
      password,
      name,
      verification_code: verificationCode
    });

    if (result.success) {
      this.showSuccess('注册成功');
      // 跳转到首页
      setTimeout(() => {
        this.handleNavigation('/', 'home');
      }, 1000);
    } else {
      throw new Error(result.message || '注册失败');
    }
  }

  /**
   * 发送验证码
   */
  async sendVerificationCode() {
    const phoneInput = this.container.querySelector('#phone');
    const phone = phoneInput.value.trim();

    if (!phone) {
      this.showError('请输入手机号');
      return;
    }

    if (!AuthService.validatePhone(phone)) {
      this.showError('请输入正确的手机号');
      return;
    }

    const sendCodeBtn = this.container.querySelector('#send-code-btn');
    sendCodeBtn.disabled = true;
    sendCodeBtn.textContent = '发送中...';

    try {
      // 尝试调用后端API
      const result = await this.authService.sendVerificationCode(phone, 'register');
      
      if (result.success) {
        this.showSuccess('验证码已发送');
        this.startCountdown(sendCodeBtn);
      } else {
        throw new Error(result.message || '验证码发送失败');
      }
    } catch (error) {
      console.warn('API调用失败，使用模拟验证码:', error);
      
      // 模拟验证码发送（开发环境）
      const mockCode = Math.floor(100000 + Math.random() * 900000).toString();
      console.log(`模拟验证码: ${mockCode}`);
      
      // 存储模拟验证码到sessionStorage
      sessionStorage.setItem(`verification_code_${phone}`, mockCode);
      sessionStorage.setItem(`verification_code_time_${phone}`, Date.now().toString());
      
      this.showSuccess(`验证码已发送 (开发模式: ${mockCode})`);
      this.startCountdown(sendCodeBtn);
    }
  }

  /**
   * 开始倒计时
   */
  startCountdown(button, seconds = 60) {
    let remaining = seconds;
    
    const timer = setInterval(() => {
      button.textContent = `${remaining}秒后重发`;
      remaining--;

      if (remaining < 0) {
        clearInterval(timer);
        button.disabled = false;
        button.textContent = '发送验证码';
      }
    }, 1000);
  }

  /**
   * 验证输入
   */
  validateInput(phone, password) {
    if (!phone) {
      this.showError('请输入手机号');
      return false;
    }

    if (!AuthService.validatePhone(phone)) {
      this.showError('请输入正确的手机号');
      return false;
    }

    if (!password) {
      this.showError('请输入密码');
      return false;
    }

    if (!AuthService.validatePassword(password)) {
      this.showError('密码长度应为6-20位');
      return false;
    }

    return true;
  }

  /**
   * 设置加载状态
   */
  setLoading(loading) {
    this.isLoading = loading;
    
    // 检查容器是否存在
    if (!this.container) {
      console.warn('LoginPage container not found, skipping loading state update');
      return;
    }
    
    const submitBtn = this.container.querySelector('#submit-btn');
    const loadingSpinner = this.container.querySelector('.loading-spinner');
    
    if (submitBtn) {
      submitBtn.disabled = loading;
    }
    
    if (loadingSpinner) {
      if (loading) {
        loadingSpinner.classList.remove('hidden');
      } else {
        loadingSpinner.classList.add('hidden');
      }
    }
  }

  /**
   * 显示忘记密码模态框
   */
  showForgotPasswordModal() {
    const modal = new Modal({
      title: '重置密码',
      content: `
        <form id="reset-password-form" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">手机号</label>
            <input type="tel" name="phone" required 
                   class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                   placeholder="请输入手机号">
          </div>
          
          <div class="flex space-x-2">
            <input type="text" name="verification_code" required 
                   class="flex-1 p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                   placeholder="验证码">
            <button type="button" id="reset-send-code-btn" 
                    class="px-4 py-3 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200">
              发送验证码
            </button>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">新密码</label>
            <input type="password" name="new_password" required 
                   class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                   placeholder="请输入新密码">
          </div>
        </form>
      `,
      confirmText: '重置密码',
      onConfirm: () => this.handleResetPassword(modal)
    });

    // 绑定发送验证码事件
    const resetSendCodeBtn = modal.container.querySelector('#reset-send-code-btn');
    resetSendCodeBtn.addEventListener('click', () => {
      this.sendResetCode(modal);
    });

    this.currentModal = modal;
  }

  /**
   * 发送重置密码验证码
   */
  async sendResetCode(modal) {
    const form = modal.container.querySelector('#reset-password-form');
    const formData = new FormData(form);
    const phone = formData.get('phone');

    if (!phone || !AuthService.validatePhone(phone)) {
      this.showError('请输入正确的手机号');
      return;
    }

    const sendCodeBtn = modal.container.querySelector('#reset-send-code-btn');
    sendCodeBtn.disabled = true;
    sendCodeBtn.textContent = '发送中...';

    try {
      const result = await this.authService.sendVerificationCode(phone, 'reset_password');
      
      if (result.success) {
        this.showSuccess('验证码已发送');
        this.startCountdown(sendCodeBtn);
      } else {
        throw new Error(result.message || '验证码发送失败');
      }
    } catch (error) {
      this.showError(error.message);
      sendCodeBtn.disabled = false;
      sendCodeBtn.textContent = '发送验证码';
    }
  }

  /**
   * 处理重置密码
   */
  async handleResetPassword(modal) {
    const form = modal.container.querySelector('#reset-password-form');
    const formData = new FormData(form);
    
    const phone = formData.get('phone');
    const verificationCode = formData.get('verification_code');
    const newPassword = formData.get('new_password');

    if (!phone || !verificationCode || !newPassword) {
      this.showError('请填写完整信息');
      return false;
    }

    if (!AuthService.validatePhone(phone)) {
      this.showError('请输入正确的手机号');
      return false;
    }

    if (!AuthService.validatePassword(newPassword)) {
      this.showError('密码长度应为6-20位');
      return false;
    }

    try {
      const result = await this.authService.resetPassword({
        phone,
        verification_code: verificationCode,
        new_password: newPassword
      });

      if (result.success) {
        this.showSuccess('密码重置成功，请重新登录');
        return true;
      } else {
        throw new Error(result.message || '密码重置失败');
      }
    } catch (error) {
      this.showError(error.message);
      return false;
    }
  }

  /**
   * 显示成功消息
   */
  showSuccess(message) {
    if (window.Notification && window.Notification.success) {
      window.Notification.success(message);
    } else {
      alert(message);
    }
  }

  /**
   * 显示错误消息
   */
  showError(message) {
    if (window.Notification && window.Notification.error) {
      window.Notification.error(message);
    } else {
      alert(message);
    }
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
   * 销毁组件
   */
  destroy() {
    // 销毁子组件
    if (this.navigation) {
      this.navigation.destroy();
    }

    if (this.currentModal) {
      this.currentModal.destroy();
    }

    // 清理引用
    this.container = null;
    this.navigation = null;
    this.currentModal = null;
  }
}