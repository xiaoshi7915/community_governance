/**
 * 本地存储中间件
 * 提供状态持久化功能
 */
class StorageMiddleware {
  constructor(key, options = {}) {
    this.key = key;
    this.options = {
      serialize: JSON.stringify,
      deserialize: JSON.parse,
      storage: localStorage,
      whitelist: null, // 需要持久化的字段白名单
      blacklist: null, // 不需要持久化的字段黑名单
      ...options
    };
  }

  /**
   * 创建持久化中间件
   * @returns {Function} 中间件函数
   */
  create() {
    return (prevState, nextState, store) => {
      try {
        const stateToSave = this.filterState(nextState);
        const serialized = this.options.serialize(stateToSave);
        this.options.storage.setItem(this.key, serialized);
      } catch (error) {
        console.error('Failed to save state to storage:', error);
      }
    };
  }

  /**
   * 从存储中恢复状态
   * @returns {Object|null} 恢复的状态
   */
  restore() {
    try {
      const serialized = this.options.storage.getItem(this.key);
      if (serialized === null) return null;
      
      return this.options.deserialize(serialized);
    } catch (error) {
      console.error('Failed to restore state from storage:', error);
      return null;
    }
  }

  /**
   * 清除存储的状态
   */
  clear() {
    try {
      this.options.storage.removeItem(this.key);
    } catch (error) {
      console.error('Failed to clear state from storage:', error);
    }
  }

  /**
   * 过滤需要持久化的状态字段
   * @param {Object} state - 状态对象
   * @returns {Object} 过滤后的状态
   */
  filterState(state) {
    const { whitelist, blacklist } = this.options;

    if (whitelist) {
      const filtered = {};
      whitelist.forEach(key => {
        if (key in state) {
          filtered[key] = state[key];
        }
      });
      return filtered;
    }

    if (blacklist) {
      const filtered = { ...state };
      blacklist.forEach(key => {
        delete filtered[key];
      });
      return filtered;
    }

    return state;
  }
}

/**
 * 创建本地存储中间件的便捷函数
 * @param {string} key - 存储键名
 * @param {Object} options - 配置选项
 * @returns {Function} 中间件函数
 */
export function createStorageMiddleware(key, options = {}) {
  const middleware = new StorageMiddleware(key, options);
  return middleware.create();
}

/**
 * 从本地存储恢复状态的便捷函数
 * @param {string} key - 存储键名
 * @param {Object} options - 配置选项
 * @returns {Object|null} 恢复的状态
 */
export function restoreFromStorage(key, options = {}) {
  const middleware = new StorageMiddleware(key, options);
  return middleware.restore();
}

/**
 * 清除本地存储状态的便捷函数
 * @param {string} key - 存储键名
 */
export function clearStorage(key) {
  const middleware = new StorageMiddleware(key);
  middleware.clear();
}

export default StorageMiddleware;