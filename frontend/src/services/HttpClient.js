/**
 * HTTP客户端基础类
 * 封装fetch API，提供请求和响应拦截器机制，错误处理和重试逻辑
 */
import { API_BASE_URL } from '../config/api.js';

export class HttpClient {
  constructor(baseURL = '') {
    // 如果baseURL以/开头，说明是相对路径，需要拼接完整的API基础URL
    if (baseURL.startsWith('/')) {
      this.baseURL = API_BASE_URL + baseURL;
    } else if (baseURL) {
      this.baseURL = baseURL;
    } else {
      this.baseURL = API_BASE_URL;
    }
    this.interceptors = {
      request: [],
      response: []
    };
    this.defaultOptions = {
      headers: {
        'Content-Type': 'application/json'
      }
    };
  }

  /**
   * 添加请求拦截器
   * @param {Function} interceptor - 拦截器函数
   */
  addRequestInterceptor(interceptor) {
    this.interceptors.request.push(interceptor);
  }

  /**
   * 添加响应拦截器
   * @param {Function} interceptor - 拦截器函数
   */
  addResponseInterceptor(interceptor) {
    this.interceptors.response.push(interceptor);
  }

  /**
   * 应用请求拦截器
   * @param {string} url - 请求URL
   * @param {Object} options - 请求选项
   * @returns {Object} 处理后的配置
   */
  applyRequestInterceptors(url, options) {
    let config = {
      url: this.baseURL + url,
      options: { ...this.defaultOptions, ...options }
    };

    // 应用所有请求拦截器
    for (const interceptor of this.interceptors.request) {
      config = interceptor(config) || config;
    }

    return config;
  }

  /**
   * 应用响应拦截器
   * @param {*} data - 响应数据
   * @param {Response} response - 原始响应对象
   * @returns {*} 处理后的数据
   */
  applyResponseInterceptors(data, response) {
    let result = data;

    // 应用所有响应拦截器
    for (const interceptor of this.interceptors.response) {
      result = interceptor(result, response) || result;
    }

    return result;
  }

  /**
   * 错误处理
   * @param {Error} error - 错误对象
   * @returns {Error} 处理后的错误
   */
  handleError(error) {
    // 网络错误
    if (!navigator.onLine) {
      return new Error('网络连接失败，请检查网络设置');
    }

    // HTTP错误
    if (error.response) {
      const { status } = error.response;
      switch (status) {
        case 401:
          return new Error('未授权访问，请重新登录');
        case 403:
          return new Error('权限不足，无法访问');
        case 404:
          return new Error('请求的资源不存在');
        case 500:
          return new Error('服务器内部错误，请稍后重试');
        default:
          return new Error(`请求失败 (${status})`);
      }
    }

    // 其他错误
    return error;
  }

  /**
   * 重试逻辑
   * @param {Function} requestFn - 请求函数
   * @param {number} maxRetries - 最大重试次数
   * @param {number} delay - 重试延迟(ms)
   * @returns {Promise} 请求结果
   */
  async retry(requestFn, maxRetries = 3, delay = 1000) {
    let lastError;

    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        
        // 如果是最后一次重试或者是不可重试的错误，直接抛出
        if (i === maxRetries || this.isNonRetryableError(error)) {
          throw error;
        }

        // 等待后重试
        await this.sleep(delay * Math.pow(2, i)); // 指数退避
      }
    }

    throw lastError;
  }

  /**
   * 判断是否为不可重试的错误
   * @param {Error} error - 错误对象
   * @returns {boolean} 是否不可重试
   */
  isNonRetryableError(error) {
    if (error.response) {
      const { status } = error.response;
      // 4xx错误通常不需要重试
      return status >= 400 && status < 500;
    }
    return false;
  }

  /**
   * 延迟函数
   * @param {number} ms - 延迟时间(毫秒)
   * @returns {Promise} Promise对象
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 基础请求方法
   * @param {string} url - 请求URL
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async request(url, options = {}) {
    const requestFn = async () => {
      // 应用请求拦截器
      const config = this.applyRequestInterceptors(url, options);

      try {
        const response = await fetch(config.url, config.options);
        
        // 检查响应状态
        if (!response.ok) {
          const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
          error.response = response;
          throw error;
        }

        // 解析响应数据
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
          data = await response.json();
        } else {
          data = await response.text();
        }

        // 应用响应拦截器
        return this.applyResponseInterceptors(data, response);
      } catch (error) {
        throw this.handleError(error);
      }
    };

    // 使用重试机制
    return await this.retry(requestFn);
  }

  /**
   * GET请求
   * @param {string} url - 请求URL
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async get(url, options = {}) {
    return await this.request(url, {
      ...options,
      method: 'GET'
    });
  }

  /**
   * POST请求
   * @param {string} url - 请求URL
   * @param {*} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async post(url, data, options = {}) {
    return await this.request(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * PUT请求
   * @param {string} url - 请求URL
   * @param {*} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async put(url, data, options = {}) {
    return await this.request(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  /**
   * DELETE请求
   * @param {string} url - 请求URL
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async delete(url, options = {}) {
    return await this.request(url, {
      ...options,
      method: 'DELETE'
    });
  }

  /**
   * PATCH请求
   * @param {string} url - 请求URL
   * @param {*} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async patch(url, data, options = {}) {
    return await this.request(url, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
}