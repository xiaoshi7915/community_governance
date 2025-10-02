/**
 * API配置
 * 统一管理API端点和配置
 */

// 根据环境确定API基础URL
const getApiBaseUrl = () => {
  // 首先检查是否已经通过网络检测设置了API地址
  if (typeof window !== 'undefined' && window.API_BASE_URL) {
    return window.API_BASE_URL;
  }
  
  // 检查localStorage中保存的地址
  if (typeof window !== 'undefined') {
    const savedHost = localStorage.getItem('detected_api_host');
    if (savedHost) {
      return savedHost;
    }
  }
  
  // 检查当前页面的host，如果不是localhost，使用当前host
  if (typeof window !== 'undefined') {
    const currentHost = window.location.hostname;
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
      // 使用当前host，但端口改为8000
      return `http://${currentHost}:8000`;
    }
  }
  
  // 开发环境
  if (import.meta && import.meta.env && import.meta.env.DEV) {
    return 'http://localhost:8000';
  }
  
  // 生产环境
  if (import.meta && import.meta.env && import.meta.env.PROD) {
    return window.location.origin;
  }
  
  // 默认
  return 'http://localhost:8000';
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  API_VERSION: '/api/v1',
  TIMEOUT: 10000,
  
  // 端点配置
  ENDPOINTS: {
    AUTH: '/auth',
    USERS: '/users',
    EVENTS: '/events',
    FILES: '/files',
    AI: '/ai',
    NOTIFICATIONS: '/notifications',
    STATISTICS: '/statistics'
  }
};

// 完整的API URL
export const API_BASE_URL = `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}`;

// 具体端点URL
export const API_ENDPOINTS = {
  // 认证相关
  AUTH_LOGIN: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/login`,
  AUTH_REGISTER: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/register`,
  AUTH_REFRESH: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/refresh`,
  AUTH_LOGOUT: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/logout`,
  AUTH_SEND_CODE: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/send-code`,
  AUTH_RESET_PASSWORD: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/reset-password`,
  AUTH_ME: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}/me`,
  
  // 用户相关
  USERS_PROFILE: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.USERS}/profile`,
  
  // 事件相关
  EVENTS_LIST: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.EVENTS}`,
  EVENTS_CREATE: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.EVENTS}`,
  EVENTS_DETAIL: (id) => `${API_BASE_URL}${API_CONFIG.ENDPOINTS.EVENTS}/${id}`,
  
  // 文件相关
  FILES_UPLOAD: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.FILES}/upload`,
  FILES_DOWNLOAD: (id) => `${API_BASE_URL}${API_CONFIG.ENDPOINTS.FILES}/${id}/download`,
  
  // AI相关
  AI_ANALYZE: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AI}/analyze`,
  AI_EVENT_TYPES: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.AI}/event-types`,
  
  // 通知相关
  NOTIFICATIONS_LIST: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.NOTIFICATIONS}`,
  
  // 统计相关
  STATISTICS_OVERVIEW: `${API_BASE_URL}${API_CONFIG.ENDPOINTS.STATISTICS}/overview`
};

export default API_CONFIG;