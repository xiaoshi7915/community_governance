/**
 * 权限测试页面
 * 用于验证用户权限控制是否正确
 */
import { Navigation } from '../components/Navigation.js';
import { permissionManager, PERMISSIONS, ROLE_NAMES } from '../utils/PermissionManager.js';
import UserStore from '../stores/UserStore.js';

export class PermissionTestPage {
  constructor() {
    this.container = null;
    this.navigation = null;
    this.userStore = UserStore;
    
    this.init();
  }

  init() {
    // 监听用户状态变化
    this.userStore.subscribe((state) => {
      if (state.user) {
        permissionManager.setUser(state.user);
        this.render();
      }
    });
  }

  render() {
    const container = document.createElement('div');
    container.className = 'min-h-screen bg-gray-50';

    // 导航栏
    this.navigation = new Navigation();
    container.appendChild(this.navigation.render());

    // 主要内容
    const main = document.createElement('main');
    main.className = 'container mx-auto px-4 py-8';

    // 页面标题
    const title = document.createElement('h1');
    title.className = 'text-3xl font-bold text-gray-900 mb-8';
    title.textContent = '权限测试页面';
    main.appendChild(title);

    // 用户信息卡片
    main.appendChild(this.renderUserInfo());

    // 权限测试卡片
    main.appendChild(this.renderPermissionTests());

    // 菜单访问测试
    main.appendChild(this.renderMenuTests());

    container.appendChild(main);
    this.container = container;
    return container;
  }

  renderUserInfo() {
    const user = this.userStore.getState().user;
    if (!user) {
      const noUser = document.createElement('div');
      noUser.className = 'bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6';
      noUser.textContent = '请先登录以查看权限信息';
      return noUser;
    }

    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md p-6 mb-6';

    const cardTitle = document.createElement('h2');
    cardTitle.className = 'text-xl font-semibold text-gray-900 mb-4';
    cardTitle.textContent = '当前用户信息';
    card.appendChild(cardTitle);

    const userInfo = document.createElement('div');
    userInfo.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';

    const infoItems = [
      { label: '姓名', value: user.name },
      { label: '手机号', value: user.phone },
      { label: '角色', value: `${ROLE_NAMES[user.role]} (${user.role})` },
      { label: '状态', value: user.is_active ? '激活' : '未激活' },
      { label: '权限数量', value: permissionManager.getCurrentPermissions().length },
      { label: '是否管理员', value: permissionManager.isAdmin() ? '是' : '否' }
    ];

    infoItems.forEach(item => {
      const infoItem = document.createElement('div');
      infoItem.className = 'flex justify-between items-center p-3 bg-gray-50 rounded';
      
      const label = document.createElement('span');
      label.className = 'font-medium text-gray-700';
      label.textContent = item.label + ':';
      
      const value = document.createElement('span');
      value.className = 'text-gray-900';
      value.textContent = item.value;
      
      infoItem.appendChild(label);
      infoItem.appendChild(value);
      userInfo.appendChild(infoItem);
    });

    card.appendChild(userInfo);
    return card;
  }

  renderPermissionTests() {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md p-6 mb-6';

    const cardTitle = document.createElement('h2');
    cardTitle.className = 'text-xl font-semibold text-gray-900 mb-4';
    cardTitle.textContent = '权限测试结果';
    card.appendChild(cardTitle);

    // 权限测试项
    const permissionTests = [
      { name: '查看个人资料', permission: PERMISSIONS.VIEW_PROFILE },
      { name: '编辑个人资料', permission: PERMISSIONS.EDIT_PROFILE },
      { name: '查看事件列表', permission: PERMISSIONS.VIEW_EVENTS },
      { name: '创建事件', permission: PERMISSIONS.CREATE_EVENT },
      { name: '编辑事件', permission: PERMISSIONS.EDIT_EVENT },
      { name: '删除事件', permission: PERMISSIONS.DELETE_EVENT },
      { name: '查看通知', permission: PERMISSIONS.VIEW_NOTIFICATIONS },
      { name: '发送通知', permission: PERMISSIONS.SEND_NOTIFICATION },
      { name: '上传文件', permission: PERMISSIONS.UPLOAD_FILE },
      { name: '删除文件', permission: PERMISSIONS.DELETE_FILE },
      { name: '查看统计', permission: PERMISSIONS.VIEW_STATISTICS },
      { name: '查看全部统计', permission: PERMISSIONS.VIEW_ALL_STATISTICS },
      { name: '管理用户', permission: PERMISSIONS.MANAGE_USERS },
      { name: '系统管理', permission: PERMISSIONS.MANAGE_SYSTEM },
      { name: '管理面板', permission: PERMISSIONS.VIEW_ADMIN_PANEL }
    ];

    const testGrid = document.createElement('div');
    testGrid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3';

    permissionTests.forEach(test => {
      const hasPermission = permissionManager.hasPermission(test.permission);
      
      const testItem = document.createElement('div');
      testItem.className = `flex items-center justify-between p-3 rounded ${
        hasPermission ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
      }`;
      
      const testName = document.createElement('span');
      testName.className = 'text-sm font-medium text-gray-700';
      testName.textContent = test.name;
      
      const testResult = document.createElement('span');
      testResult.className = `text-sm font-bold ${hasPermission ? 'text-green-600' : 'text-red-600'}`;
      testResult.textContent = hasPermission ? '✅ 有权限' : '❌ 无权限';
      
      testItem.appendChild(testName);
      testItem.appendChild(testResult);
      testGrid.appendChild(testItem);
    });

    card.appendChild(testGrid);
    return card;
  }

  renderMenuTests() {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md p-6 mb-6';

    const cardTitle = document.createElement('h2');
    cardTitle.className = 'text-xl font-semibold text-gray-900 mb-4';
    cardTitle.textContent = '可访问菜单';
    card.appendChild(cardTitle);

    const accessibleMenus = permissionManager.getAccessibleMenus();
    
    if (accessibleMenus.length === 0) {
      const noMenus = document.createElement('div');
      noMenus.className = 'text-gray-500 text-center py-4';
      noMenus.textContent = '没有可访问的菜单';
      card.appendChild(noMenus);
      return card;
    }

    const menuGrid = document.createElement('div');
    menuGrid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4';

    accessibleMenus.forEach(menu => {
      const menuItem = document.createElement('div');
      menuItem.className = 'flex items-center p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer';
      
      const menuIcon = document.createElement('span');
      menuIcon.className = 'text-2xl mr-3';
      menuIcon.textContent = menu.icon;
      
      const menuInfo = document.createElement('div');
      
      const menuName = document.createElement('div');
      menuName.className = 'font-medium text-gray-900';
      menuName.textContent = menu.name;
      
      const menuPath = document.createElement('div');
      menuPath.className = 'text-sm text-gray-600';
      menuPath.textContent = menu.path;
      
      menuInfo.appendChild(menuName);
      menuInfo.appendChild(menuPath);
      
      menuItem.appendChild(menuIcon);
      menuItem.appendChild(menuInfo);
      
      // 添加点击事件
      menuItem.addEventListener('click', () => {
        if (window.router) {
          window.router.navigate(menu.path);
        }
      });
      
      menuGrid.appendChild(menuItem);
    });

    card.appendChild(menuGrid);
    return card;
  }

  /**
   * 页面销毁
   */
  destroy() {
    if (this.navigation) {
      this.navigation.destroy();
    }
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
  }
}
