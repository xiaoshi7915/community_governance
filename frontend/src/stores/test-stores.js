/**
 * 状态管理系统测试文件
 * 用于验证状态管理功能是否正常工作
 */

import { userStore, eventStore, configStore, globalStateManager } from './index.js';

/**
 * 测试基础Store功能
 */
function testBaseStore() {
  console.log('Testing Base Store functionality...');
  
  // 测试用户状态管理
  console.log('Initial user state:', userStore.getState());
  
  // 测试状态订阅
  const unsubscribe = userStore.subscribe((state) => {
    console.log('User state changed:', state);
  });
  
  // 测试状态更新
  userStore.setUser({
    id: '1',
    username: 'testuser',
    nickname: '测试用户',
    phone: '13800138000'
  });
  
  userStore.setTokens('test-token', 'test-refresh-token', 3600);
  
  console.log('User display name:', userStore.getUserDisplayName());
  console.log('Token valid:', userStore.isTokenValid());
  
  // 取消订阅
  unsubscribe();
}

/**
 * 测试事件状态管理
 */
function testEventStore() {
  console.log('\nTesting Event Store functionality...');
  
  // 添加测试事件
  const testEvents = [
    {
      id: '1',
      title: '测试事件1',
      description: '这是一个测试事件',
      status: 'pending',
      priority: 'high',
      type: 'incident',
      created_at: new Date().toISOString()
    },
    {
      id: '2',
      title: '测试事件2',
      description: '这是另一个测试事件',
      status: 'processing',
      priority: 'medium',
      type: 'request',
      created_at: new Date().toISOString()
    }
  ];
  
  eventStore.setEvents(testEvents, 2);
  console.log('Events loaded:', eventStore.getState().events.length);
  
  // 测试筛选
  eventStore.updateFilters({ status: 'pending' });
  console.log('Filter applied:', eventStore.getState().filters);
  
  // 测试统计
  console.log('Event stats:', eventStore.getEventStats());
  
  // 测试添加新事件
  eventStore.addEvent({
    id: '3',
    title: '新事件',
    description: '动态添加的事件',
    status: 'pending',
    priority: 'low',
    type: 'feedback',
    created_at: new Date().toISOString()
  });
  
  console.log('Events after adding:', eventStore.getState().events.length);
}

/**
 * 测试配置状态管理
 */
function testConfigStore() {
  console.log('\nTesting Config Store functionality...');
  
  // 测试应用设置
  configStore.updateAppSettings({ theme: 'dark' });
  console.log('Theme updated:', configStore.getState().app.theme);
  
  // 测试表单草稿
  configStore.saveFormDraft('eventReport', {
    title: '草稿标题',
    description: '草稿描述',
    location: '草稿位置'
  });
  
  const draft = configStore.getFormDraft('eventReport');
  console.log('Form draft saved:', draft);
  
  // 测试临时数据
  configStore.setTempData('testKey', 'testValue');
  console.log('Temp data:', configStore.getTempData('testKey'));
  
  // 测试缓存
  configStore.setCache('testCache', { data: 'cached data' }, 60000);
  console.log('Cached data:', configStore.getCache('testCache'));
}

/**
 * 测试全局状态管理器
 */
function testGlobalStateManager() {
  console.log('\nTesting Global State Manager...');
  
  // 获取所有状态
  const allStates = globalStateManager.getAllStates();
  console.log('All states keys:', Object.keys(allStates));
  
  // 测试全局订阅
  const unsubscribe = globalStateManager.subscribe((storeName, state, allStates) => {
    console.log(`Store ${storeName} changed`);
  });
  
  // 批量更新
  globalStateManager.batchUpdate({
    user: { loginLoading: true },
    event: { loading: true }
  });
  
  console.log('Batch update completed');
  
  // 取消订阅
  unsubscribe();
}

/**
 * 测试持久化功能
 */
function testPersistence() {
  console.log('\nTesting Persistence functionality...');
  
  // 检查localStorage中的数据
  const userStoreData = localStorage.getItem('userStore');
  const eventStoreData = localStorage.getItem('eventStore');
  const configStoreData = localStorage.getItem('configStore');
  
  console.log('User store persisted:', !!userStoreData);
  console.log('Event store persisted:', !!eventStoreData);
  console.log('Config store persisted:', !!configStoreData);
  
  if (userStoreData) {
    console.log('User store data sample:', JSON.parse(userStoreData));
  }
}

/**
 * 运行所有测试
 */
function runAllTests() {
  console.log('=== State Management System Tests ===');
  
  try {
    testBaseStore();
    testEventStore();
    testConfigStore();
    testGlobalStateManager();
    testPersistence();
    
    console.log('\n✅ All tests completed successfully!');
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// 如果直接运行此文件，执行测试
if (typeof window !== 'undefined') {
  // 在浏览器环境中，将测试函数暴露到全局
  window.testStores = runAllTests;
  console.log('State management tests loaded. Run window.testStores() to execute tests.');
} else {
  // 在Node.js环境中直接运行
  runAllTests();
}

export { runAllTests };