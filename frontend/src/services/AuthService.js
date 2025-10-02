import { HttpClient } from './HttpClient.js';

/**
 * 认证服务类
 * 处理用户认证、登录、注册、token刷新功能
 * 集成token自动管理和过期处理
 */
export class AuthService extends HttpClient {
  constructor() {
    super('/auth');
    
    // 初始化token
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    
    // 添加请求拦截器，自动添加Authorization头
    this.addRequestInterceptor(this.addAuthHeader.bind(this));
    
    // 添加响应拦截器，处理token过期
    this.addResponseInterceptor(this.handleTokenExpiry.bind(this));
  }

  /**
   * 请求拦截器：添加认证头
   * @param {Object} config - 请求配置
   * @returns {Object} 修改后的配置
   */
  addAuthHeader(config) {
    if (this.accessToken) {
      // 确保headers对象存在
      if (!config.options) {
        config.options = {};
      }
      if (!config.options.headers) {
        config.options.headers = {};
      }
      
      // 只有在没有Authorization头时才添加
      if (!config.options.headers.Authorization) {
        config.options.headers.Authorization = `Bearer ${this.accessToken}`;
      }
    }
    return config;
  }

  /**
   * 响应拦截器：处理token过期
   * @param {*} data - 响应数据
   * @param {Response} response - 响应对象
   * @returns {*} 处理后的数据
   */
  async handleTokenExpiry(data, response) {
    if (response.status === 401) {
      console.warn('Token expired or invalid, clearing auth state');
      // 清除所有token并触发重新登录
      this.clearTokens();
      
      // 触发全局登录状态更新
      if (typeof window !== 'undefined' && window.userStore) {
        window.userStore.logout();
      }
      
      // 显示提示信息
      if (typeof window !== 'undefined' && window.Notification) {
        window.Notification.show('登录已过期，请重新登录', 'warning');
      }
      
      // 跳转到登录页
      this.redirectToLogin();
      throw new Error('登录已过期，请重新登录');
    }
    return data;
  }

  /**
   * 用户登录
   * @param {Object} credentials - 登录凭据
   * @param {string} credentials.phone - 手机号
   * @param {string} credentials.password - 密码
   * @returns {Promise<Object>} 登录结果
   */
  async login(credentials) {
    try {
      const response = await this.post('/login', credentials);
      
      // 检查响应格式 - 新的API直接返回数据
      if (response.access_token || (response.success && response.data)) {
        const { access_token, refresh_token, user } = response.access_token ? response : response.data;
        
        // 保存tokens
        this.setTokens(access_token, refresh_token);
        
        // 更新UserStore状态 - 简化逻辑
        if (typeof window !== 'undefined' && window.userStore) {
          window.userStore.setUser(user);
          window.userStore.setTokens(access_token, refresh_token);
        }
        
        // 触发登录成功事件
        this.dispatchAuthEvent('login', { user });
        
        return {
          success: true,
          data: { user },
          message: '登录成功'
        };
      }
      
      return response;
    } catch (error) {
      throw new Error(error.message || '登录失败，请检查用户名和密码');
    }
  }

  /**
   * 用户注册
   * @param {Object} userData - 用户数据
   * @param {string} userData.phone - 手机号
   * @param {string} userData.password - 密码
   * @param {string} userData.name - 姓名
   * @param {string} userData.verification_code - 验证码
   * @returns {Promise<Object>} 注册结果
   */
  async register(userData) {
    try {
      const response = await this.post('/register', userData);
      
      if (response.success) {
        // 注册成功后自动登录
        const loginResult = await this.login({
          phone: userData.phone,
          password: userData.password
        });
        
        return {
          success: true,
          data: loginResult.data,
          message: '注册成功'
        };
      }
      
      return response;
    } catch (error) {
      throw new Error(error.message || '注册失败，请稍后重试');
    }
  }

  /**
   * 刷新访问token
   * @returns {Promise<Object>} 刷新结果
   */
  async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('没有刷新token');
    }

    try {
      const response = await this.post('/refresh', {
        refresh_token: this.refreshToken
      });

      if (response.success) {
        const { access_token, refresh_token } = response.data;
        this.setTokens(access_token, refresh_token);
        return response;
      }

      throw new Error(response.message || 'Token刷新失败');
    } catch (error) {
      // 刷新失败，清除所有token
      this.clearTokens();
      throw error;
    }
  }

  /**
   * 用户登出
   * @returns {Promise<Object>} 登出结果
   */
  async logout() {
    try {
      // 调用后端登出接口
      if (this.accessToken) {
        await this.post('/logout');
      }
    } catch (error) {
      // 即使后端登出失败，也要清除本地token
      console.warn('后端登出失败:', error.message);
    } finally {
      // 清除本地token和用户信息
      this.clearTokens();
      
      // 触发登出事件
      this.dispatchAuthEvent('logout');
      
      // 跳转到登录页
      this.redirectToLogin();
    }

    return {
      success: true,
      message: '已退出登录'
    };
  }

  /**
   * 发送验证码
   * @param {string} phone - 手机号
   * @param {string} type - 验证码类型 (register|reset_password)
   * @returns {Promise<Object>} 发送结果
   */
  async sendVerificationCode(phone, type = 'register') {
    try {
      const response = await this.post('/send-code', { phone, type });
      return response;
    } catch (error) {
      throw new Error(error.message || '验证码发送失败');
    }
  }

  /**
   * 重置密码
   * @param {Object} resetData - 重置数据
   * @param {string} resetData.phone - 手机号
   * @param {string} resetData.verification_code - 验证码
   * @param {string} resetData.new_password - 新密码
   * @returns {Promise<Object>} 重置结果
   */
  async resetPassword(resetData) {
    try {
      const response = await this.post('/reset-password', resetData);
      
      if (response.success) {
        // 密码重置成功，清除当前token
        this.clearTokens();
      }
      
      return response;
    } catch (error) {
      throw new Error(error.message || '密码重置失败');
    }
  }

  /**
   * 修改密码
   * @param {Object} changeData - 修改数据
   * @param {string} changeData.old_password - 旧密码
   * @param {string} changeData.new_password - 新密码
   * @returns {Promise<Object>} 修改结果
   */
  async changePassword(changeData) {
    try {
      const response = await this.post('/change-password', changeData);
      return response;
    } catch (error) {
      throw new Error(error.message || '密码修改失败');
    }
  }

  /**
   * 验证token有效性
   * @param {string} token - 要验证的token
   * @returns {Promise<boolean>} token是否有效
   */
  async validateToken(token) {
    if (!token || this.isTokenExpired(token)) {
      return false;
    }

    try {
      // 通过调用需要认证的接口来验证token
      const response = await this.get('/me');
      return response.success;
    } catch (error) {
      return false;
    }
  }

  /**
   * 获取当前用户信息
   * @returns {Promise<Object>} 用户信息
   */
  async getCurrentUser() {
    try {
      const response = await this.get('/me');
      if (response.success) {
        return response.data;
      }
      throw new Error(response.message || '获取用户信息失败');
    } catch (error) {
      throw new Error(error.message || '获取用户信息失败');
    }
  }

  /**
   * 更新用户信息
   * @param {Object} userData - 用户数据
   * @returns {Promise<Object>} 更新结果
   */
  async updateProfile(userData) {
    try {
      const response = await this.put('/profile', userData);
      
      if (response.success) {
        // 触发用户信息更新事件
        this.dispatchAuthEvent('profile-updated', { user: response.data });
      }
      
      return response;
    } catch (error) {
      throw new Error(error.message || '用户信息更新失败');
    }
  }

  /**
   * 设置tokens
   * @param {string} accessToken - 访问token
   * @param {string} refreshToken - 刷新token
   */
  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  }

  /**
   * 清除所有tokens
   */
  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
  }

  /**
   * 检查是否已登录
   * @returns {boolean} 是否已登录
   */
  isAuthenticated() {
    return !!this.accessToken && !this.isTokenExpired(this.accessToken);
  }

  /**
   * 检查token是否过期
   * @param {string} token - JWT token
   * @returns {boolean} 是否过期
   */
  isTokenExpired(token) {
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      
      // 提前5分钟判断为过期，避免请求时才发现过期
      return payload.exp < (currentTime + 300);
    } catch (error) {
      return true;
    }
  }

  /**
   * 获取当前访问token
   * @returns {string|null} 访问token
   */
  getAccessToken() {
    return this.accessToken;
  }

  /**
   * 获取当前刷新token
   * @returns {string|null} 刷新token
   */
  getRefreshToken() {
    return this.refreshToken;
  }

  /**
   * 跳转到登录页
   */
  redirectToLogin() {
    // 如果是SPA应用，使用路由跳转
    if (window.router) {
      window.router.navigate('/login');
    } else {
      // 否则直接跳转
      window.location.href = '/login.html';
    }
  }

  /**
   * 触发认证相关事件
   * @param {string} eventType - 事件类型
   * @param {Object} data - 事件数据
   */
  dispatchAuthEvent(eventType, data = {}) {
    const event = new CustomEvent(`auth:${eventType}`, {
      detail: data
    });
    window.dispatchEvent(event);
  }

  /**
   * 验证手机号格式
   * @param {string} phone - 手机号
   * @returns {boolean} 是否有效
   */
  static validatePhone(phone) {
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
  }

  /**
   * 验证密码格式
   * @param {string} password - 密码
   * @returns {boolean} 是否有效
   */
  static validatePassword(password) {
    return password && password.length >= 6 && password.length <= 20;
  }
}