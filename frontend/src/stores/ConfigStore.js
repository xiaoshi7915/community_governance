import Store from './Store.js';
import { createStorageMiddleware, restoreFromStorage, clearStorage } from './StorageMiddleware.js';

/**
 * 应用配置状态管理
 * 管理用户偏好设置、应用配置和临时数据
 */
class ConfigStore extends Store {
  constructor() {
    // 从本地存储恢复状态
    const persistedState = restoreFromStorage('configStore', {
      whitelist: ['settings', 'preferences', 'cache']
    });

    const initialState = {
      // 应用设置
      settings: {
        // 通知设置
        statusNotifications: true,
        pushNotifications: true,
        emailNotifications: false,
        
        // 隐私设置
        locationServices: true,
        dataCollection: true,
        
        // 应用设置
        language: 'zh-CN',
        theme: 'light',
        autoRefresh: true,
        cacheEnabled: true
      },
      
      // 用户偏好
      preferences: {
        defaultEventType: '',
        defaultPriority: 'medium',
        autoLocation: true,
        compressImages: true,
        maxImageSize: 5 * 1024 * 1024, // 5MB
        uploadQuality: 0.8
      },
      
      // 缓存配置
      cache: {
        maxAge: 5 * 60 * 1000, // 5分钟
        maxSize: 50 * 1024 * 1024, // 50MB
        currentSize: 0
      },
      
      // 表单状态
      formStates: {},
      
      // 临时数据
      tempData: {},
      
      // 加载状态
      loading: false,
      error: null,
      
      ...persistedState
    };

    super(initialState);

    // 添加持久化中间件
    this.addMiddleware(createStorageMiddleware('configStore', {
      whitelist: ['settings', 'preferences', 'cache']
    }));
  }

  /**
   * 更新单个设置
   * @param {string} key - 设置键
   * @param {*} value - 设置值
   */
  updateSetting(key, value) {
    this.setState(prevState => ({
      settings: {
        ...prevState.settings,
        [key]: value
      }
    }));
  }

  /**
   * 批量更新设置
   * @param {Object} settings - 设置对象
   */
  updateSettings(settings) {
    this.setState(prevState => ({
      settings: {
        ...prevState.settings,
        ...settings
      }
    }));
  }

  /**
   * 更新用户偏好
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
   * 获取设置值
   * @param {string} key - 设置键
   * @param {*} defaultValue - 默认值
   * @returns {*} 设置值
   */
  getSetting(key, defaultValue = null) {
    const { settings } = this.getState();
    return settings[key] !== undefined ? settings[key] : defaultValue;
  }

  /**
   * 获取偏好设置值
   * @param {string} key - 偏好键
   * @param {*} defaultValue - 默认值
   * @returns {*} 偏好值
   */
  getPreference(key, defaultValue = null) {
    const { preferences } = this.getState();
    return preferences[key] !== undefined ? preferences[key] : defaultValue;
  }

  /**
   * 保存表单状态
   * @param {string} formId - 表单ID
   * @param {Object} formData - 表单数据
   */
  saveFormState(formId, formData) {
    this.setState(prevState => ({
      formStates: {
        ...prevState.formStates,
        [formId]: {
          data: formData,
          timestamp: Date.now()
        }
      }
    }));
  }

  /**
   * 获取表单状态
   * @param {string} formId - 表单ID
   * @returns {Object|null} 表单数据
   */
  getFormState(formId) {
    const { formStates } = this.getState();
    const formState = formStates[formId];
    
    if (!formState) return null;
    
    // 检查是否过期（24小时）
    const maxAge = 24 * 60 * 60 * 1000;
    if (Date.now() - formState.timestamp > maxAge) {
      this.clearFormState(formId);
      return null;
    }
    
    return formState.data;
  }

  /**
   * 清除表单状态
   * @param {string} formId - 表单ID
   */
  clearFormState(formId) {
    this.setState(prevState => {
      const newFormStates = { ...prevState.formStates };
      delete newFormStates[formId];
      return { formStates: newFormStates };
    });
  }

  /**
   * 清除所有表单状态
   */
  clearAllFormStates() {
    this.setState({ formStates: {} });
  }

  /**
   * 设置临时数据
   * @param {string} key - 数据键
   * @param {*} value - 数据值
   * @param {number} ttl - 生存时间（毫秒）
   */
  setTempData(key, value, ttl = 60000) {
    this.setState(prevState => ({
      tempData: {
        ...prevState.tempData,
        [key]: {
          value,
          expires: Date.now() + ttl
        }
      }
    }));
  }

  /**
   * 获取临时数据
   * @param {string} key - 数据键
   * @returns {*} 数据值
   */
  getTempData(key) {
    const { tempData } = this.getState();
    const item = tempData[key];
    
    if (!item) return null;
    
    if (Date.now() > item.expires) {
      this.clearTempData(key);
      return null;
    }
    
    return item.value;
  }

  /**
   * 清除临时数据
   * @param {string} key - 数据键
   */
  clearTempData(key) {
    this.setState(prevState => {
      const newTempData = { ...prevState.tempData };
      delete newTempData[key];
      return { tempData: newTempData };
    });
  }

  /**
   * 清除过期的临时数据
   */
  cleanupTempData() {
    const { tempData } = this.getState();
    const now = Date.now();
    const cleanedData = {};
    
    Object.keys(tempData).forEach(key => {
      if (tempData[key].expires > now) {
        cleanedData[key] = tempData[key];
      }
    });
    
    this.setState({ tempData: cleanedData });
  }

  /**
   * 更新缓存大小
   * @param {number} size - 缓存大小（字节）
   */
  updateCacheSize(size) {
    this.setState(prevState => ({
      cache: {
        ...prevState.cache,
        currentSize: size
      }
    }));
  }

  /**
   * 检查缓存是否超出限制
   * @returns {boolean} 是否超出限制
   */
  isCacheOverLimit() {
    const { cache } = this.getState();
    return cache.currentSize > cache.maxSize;
  }

  /**
   * 重置所有设置为默认值
   */
  resetToDefaults() {
    const defaultSettings = {
      statusNotifications: true,
      pushNotifications: true,
      emailNotifications: false,
      locationServices: true,
      dataCollection: true,
      language: 'zh-CN',
      theme: 'light',
      autoRefresh: true,
      cacheEnabled: true
    };

    const defaultPreferences = {
      defaultEventType: '',
      defaultPriority: 'medium',
      autoLocation: true,
      compressImages: true,
      maxImageSize: 5 * 1024 * 1024,
      uploadQuality: 0.8
    };

    this.setState({
      settings: defaultSettings,
      preferences: defaultPreferences,
      formStates: {},
      tempData: {}
    });
  }

  /**
   * 导出配置
   * @returns {Object} 配置数据
   */
  exportConfig() {
    const { settings, preferences } = this.getState();
    return {
      settings,
      preferences,
      exportTime: new Date().toISOString(),
      version: '1.0'
    };
  }

  /**
   * 导入配置
   * @param {Object} config - 配置数据
   */
  importConfig(config) {
    if (!config || !config.settings) {
      throw new Error('Invalid config data');
    }

    this.setState({
      settings: { ...this.getState().settings, ...config.settings },
      preferences: { ...this.getState().preferences, ...config.preferences }
    });
  }

  /**
   * 清除所有配置数据
   */
  clearAll() {
    clearStorage('configStore');
    this.resetToDefaults();
  }

  /**
   * 设置加载状态
   * @param {boolean} loading - 是否加载中
   * @param {string|null} error - 错误信息
   */
  setLoading(loading, error = null) {
    this.setState({ loading, error });
  }

  /**
   * 获取语言配置
   * @returns {string} 语言代码
   */
  getLanguage() {
    return this.getSetting('language', 'zh-CN');
  }

  /**
   * 设置语言
   * @param {string} language - 语言代码
   */
  setLanguage(language) {
    this.updateSetting('language', language);
  }

  /**
   * 获取主题配置
   * @returns {string} 主题名称
   */
  getTheme() {
    return this.getSetting('theme', 'light');
  }

  /**
   * 设置主题
   * @param {string} theme - 主题名称
   */
  setTheme(theme) {
    this.updateSetting('theme', theme);
  }

  /**
   * 检查是否启用了某个功能
   * @param {string} feature - 功能名称
   * @returns {boolean} 是否启用
   */
  isFeatureEnabled(feature) {
    return this.getSetting(feature, false);
  }

  /**
   * 启用或禁用功能
   * @param {string} feature - 功能名称
   * @param {boolean} enabled - 是否启用
   */
  setFeatureEnabled(feature, enabled) {
    this.updateSetting(feature, enabled);
  }
}

// 创建单例实例
const configStore = new ConfigStore();

// 定期清理过期的临时数据
setInterval(() => {
  configStore.cleanupTempData();
}, 5 * 60 * 1000); // 每5分钟清理一次

export default configStore;