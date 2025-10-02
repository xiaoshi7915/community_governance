/**
 * 基础状态管理类
 * 实现观察者模式，提供状态订阅和通知机制
 */
class Store {
  constructor(initialState = {}) {
    this.state = { ...initialState };
    this.listeners = [];
    this.middlewares = [];
  }

  /**
   * 获取当前状态的副本
   * @returns {Object} 状态副本
   */
  getState() {
    return { ...this.state };
  }

  /**
   * 更新状态（不可变更新）
   * @param {Object|Function} newState - 新状态或状态更新函数
   */
  setState(newState) {
    const prevState = { ...this.state };
    
    // 支持函数式更新
    if (typeof newState === 'function') {
      this.state = { ...this.state, ...newState(prevState) };
    } else {
      this.state = { ...this.state, ...newState };
    }

    // 应用中间件
    this.applyMiddlewares(prevState, this.state);
    
    // 通知所有监听器
    this.notifyListeners();
  }

  /**
   * 订阅状态变化
   * @param {Function} listener - 监听器函数
   * @returns {Function} 取消订阅函数
   */
  subscribe(listener) {
    if (typeof listener !== 'function') {
      throw new Error('Listener must be a function');
    }

    this.listeners.push(listener);
    
    // 返回取消订阅函数
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * 通知所有监听器
   */
  notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.state);
      } catch (error) {
        console.error('Error in state listener:', error);
      }
    });
  }

  /**
   * 添加中间件
   * @param {Function} middleware - 中间件函数
   */
  addMiddleware(middleware) {
    if (typeof middleware !== 'function') {
      throw new Error('Middleware must be a function');
    }
    this.middlewares.push(middleware);
  }

  /**
   * 应用中间件
   * @param {Object} prevState - 之前的状态
   * @param {Object} nextState - 新的状态
   */
  applyMiddlewares(prevState, nextState) {
    this.middlewares.forEach(middleware => {
      try {
        middleware(prevState, nextState, this);
      } catch (error) {
        console.error('Error in middleware:', error);
      }
    });
  }

  /**
   * 重置状态到初始状态
   */
  reset() {
    this.state = {};
    this.notifyListeners();
  }

  /**
   * 批量更新状态（减少通知次数）
   * @param {Function} updater - 批量更新函数
   */
  batch(updater) {
    const originalNotify = this.notifyListeners;
    this.notifyListeners = () => {}; // 临时禁用通知

    try {
      updater();
    } finally {
      this.notifyListeners = originalNotify;
      this.notifyListeners(); // 执行一次通知
    }
  }
}

export default Store;