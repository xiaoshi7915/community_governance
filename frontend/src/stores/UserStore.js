import Store from './Store.js';
import { createStorageMiddleware, restoreFromStorage, clearStorage } from './StorageMiddleware.js';
import { permissionManager } from '../utils/PermissionManager.js';

/**
 * 用户状态管理
 * 管理用户信息、认证状态和权限信息
 */
class UserStore extends Store {
  constructor() {
    // 从本地存储恢复状态
    const persistedState = restoreFromStorage('userStore', {
      whitelist: ['user', 'isAuthenticated', 'permissions', 'preferences']
    });

    const initialState = {
      // 用户基本信息
      user: null,
      isAuthenticated: false,
      
      // 认证相关
      token: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
      tokenExpiry: null,
      
      // 权限信息
      permissions: [],
      roles: [],
      
      // 用户偏好设置
      preferences: {
        theme: 'light',
        language: 'zh-CN',
        notifications: true,
        autoRefresh: true
      },
      
      // 登录状态
      loginLoading: false,
      loginError: null,
      
      // 用户资料更新状态
      updateLoading: false,
      updateError: null,
      
      ...persistedState
    };

    super(initialState);

    // 添加持久化中间件
    this.addMiddleware(createStorageMiddleware('userStore', {
      whitelist: ['user', 'isAuthenticated', 'permissions', 'preferences', 'roles']
    }));

    // 检查token有效性
    this.checkTokenValidity();
  }

  /**
   * 设置用户信息
   * @param {Object} user - 用户信息
   */
  setUser(user) {
    // 更新权限管理器
    permissionManager.setUser(user);
    
    this.setState({
      user,
      isAuthenticated: true,
      loginError: null,
      permissions: permissionManager.getCurrentPermissions(),
      roles: [user?.role]
    });
  }

  /**
   * 设置认证token
   * @param {string} token - 访问token
   * @param {string} refreshToken - 刷新token
   * @param {number} expiresIn - token过期时间（秒）
   */
  setTokens(token, refreshToken, expiresIn) {
    const tokenExpiry = expiresIn ? Date.now() + (expiresIn * 1000) : null;
    
    // 存储到localStorage
    localStorage.setItem('access_token', token);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }

    this.setState({
      token,
      refreshToken,
      tokenExpiry,
      isAuthenticated: true
    });
  }

  /**
   * 清除用户信息和认证状态
   */
  clearUser() {
    // 清除localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // 清除持久化状态
    clearStorage('userStore');

    this.setState({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      tokenExpiry: null,
      permissions: [],
      roles: [],
      loginError: null,
      updateError: null
    });
  }

  /**
   * 设置用户权限
   * @param {Array} permissions - 权限列表
   * @param {Array} roles - 角色列表
   */
  setPermissions(permissions = [], roles = []) {
    this.setState({
      permissions,
      roles
    });
  }

  /**
   * 检查用户是否有特定权限
   * @param {string} permission - 权限名称
   * @returns {boolean} 是否有权限
   */
  hasPermission(permission) {
    const { permissions } = this.getState();
    return permissions.includes(permission);
  }

  /**
   * 检查用户是否有特定角色
   * @param {string} role - 角色名称
   * @returns {boolean} 是否有角色
   */
  hasRole(role) {
    const { roles } = this.getState();
    return roles.includes(role);
  }

  /**
   * 更新用户偏好设置
   * @param {Object} preferences - 偏好设置
   */
  updatePreferences(preferences) {
    this.setState(prevState => ({
      preferences: {
        ...prevState.preferences,
        ...preferences
      }
    }));
  }

  /**
   * 设置登录加载状态
   * @param {boolean} loading - 是否加载中
   * @param {string|null} error - 错误信息
   */
  setLoginLoading(loading, error = null) {
    this.setState({
      loginLoading: loading,
      loginError: error
    });
  }

  /**
   * 设置用户资料更新状态
   * @param {boolean} loading - 是否加载中
   * @param {string|null} error - 错误信息
   */
  setUpdateLoading(loading, error = null) {
    this.setState({
      updateLoading: loading,
      updateError: error
    });
  }

  /**
   * 检查token是否有效
   * @returns {boolean} token是否有效
   */
  isTokenValid() {
    const { token, tokenExpiry } = this.getState();
    
    if (!token) return false;
    if (!tokenExpiry) return true; // 如果没有过期时间，假设有效
    
    return Date.now() < tokenExpiry;
  }

  /**
   * 检查token有效性并更新状态
   */
  checkTokenValidity() {
    const { token } = this.getState();
    
    if (token && !this.isTokenValid()) {
      console.warn('Token has expired, clearing user session');
      this.clearUser();
    }
  }

  /**
   * 获取用户显示名称
   * @returns {string} 用户显示名称
   */
  getUserDisplayName() {
    const { user } = this.getState();
    if (!user) return '';
    
    return user.nickname || user.username || user.phone || '用户';
  }

  /**
   * 获取用户头像URL
   * @returns {string} 头像URL
   */
  getUserAvatar() {
    const { user } = this.getState();
    if (!user || !user.avatar) return '/assets/default-avatar.png';
    
    return user.avatar;
  }

  /**
   * 更新用户信息
   * @param {Object} updates - 要更新的用户信息
   */
  updateUser(updates) {
    this.setState(prevState => ({
      user: {
        ...prevState.user,
        ...updates
      }
    }));
  }

  /**
   * 重置错误状态
   */
  clearErrors() {
    this.setState({
      loginError: null,
      updateError: null
    });
  }
}

// 创建单例实例
const userStore = new UserStore();

export default userStore;