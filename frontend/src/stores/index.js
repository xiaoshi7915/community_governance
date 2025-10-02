/**
 * 状态管理模块入口文件
 * 导出所有状态管理相关的类和实例
 */

// 基础类
export { default as Store } from './Store.js';
export { 
  default as StorageMiddleware,
  createStorageMiddleware,
  restoreFromStorage,
  clearStorage
} from './StorageMiddleware.js';

// 状态管理实例
export { default as userStore } from './UserStore.js';
export { default as eventStore } from './EventStore.js';
export { default as configStore } from './ConfigStore.js';

/**
 * 全局状态管理器
 * 提供统一的状态管理接口
 */
class GlobalStateManager {
  constructor() {
    this.stores = {
      user: userStore,
      event: eventStore,
      config: configStore
    };
    
    this.subscribers = [];
  }

  /**
   * 获取指定store
   * @param {string} storeName - store名称
   * @returns {Store} store实例
   */
  getStore(storeName) {
    return this.stores[storeName];
  }

  /**
   * 获取所有store的状态
   * @returns {Object} 所有状态
   */
  getAllStates() {
    const states = {};
    Object.keys(this.stores).forEach(key => {
      states[key] = this.stores[key].getState();
    });
    return states;
  }

  /**
   * 订阅所有store的变化
   * @param {Function} callback - 回调函数
   * @returns {Function} 取消订阅函数
   */
  subscribe(callback) {
    const unsubscribers = [];
    
    Object.keys(this.stores).forEach(key => {
      const unsubscribe = this.stores[key].subscribe((state) => {
        callback(key, state, this.getAllStates());
      });
      unsubscribers.push(unsubscribe);
    });

    // 返回取消所有订阅的函数
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  }

  /**
   * 清除所有store的状态
   */
  clearAll() {
    Object.values(this.stores).forEach(store => {
      if (typeof store.reset === 'function') {
        store.reset();
      }
    });
  }

  /**
   * 批量更新多个store
   * @param {Object} updates - 更新对象，key为store名称，value为更新数据
   */
  batchUpdate(updates) {
    Object.keys(updates).forEach(storeName => {
      const store = this.stores[storeName];
      if (store && typeof store.setState === 'function') {
        store.setState(updates[storeName]);
      }
    });
  }
}

// 创建全局状态管理器实例
export const globalStateManager = new GlobalStateManager();

// 便捷的状态访问函数
export const getState = (storeName) => {
  return globalStateManager.getStore(storeName)?.getState();
};

export const setState = (storeName, newState) => {
  const store = globalStateManager.getStore(storeName);
  if (store && typeof store.setState === 'function') {
    store.setState(newState);
  }
};

// 默认导出全局状态管理器
export default globalStateManager;