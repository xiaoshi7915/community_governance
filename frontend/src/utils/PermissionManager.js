/**
 * 前端权限管理器
 * 基于用户角色控制前端功能访问权限
 */

// 用户角色常量
export const USER_ROLES = {
  CITIZEN: 'citizen',
  GRID_WORKER: 'grid_worker', 
  MANAGER: 'manager',
  DECISION_MAKER: 'decision_maker'
};

// 权限常量
export const PERMISSIONS = {
  // 基础权限
  VIEW_PROFILE: 'view_profile',
  EDIT_PROFILE: 'edit_profile',
  
  // 事件相关权限
  VIEW_EVENTS: 'view_events',
  CREATE_EVENT: 'create_event',
  EDIT_EVENT: 'edit_event',
  DELETE_EVENT: 'delete_event',
  ASSIGN_EVENT: 'assign_event',
  
  // 通知相关权限
  VIEW_NOTIFICATIONS: 'view_notifications',
  SEND_NOTIFICATION: 'send_notification',
  
  // 文件相关权限
  UPLOAD_FILE: 'upload_file',
  DELETE_FILE: 'delete_file',
  
  // 统计相关权限
  VIEW_STATISTICS: 'view_statistics',
  VIEW_ALL_STATISTICS: 'view_all_statistics',
  
  // 管理员权限
  MANAGE_USERS: 'manage_users',
  MANAGE_SYSTEM: 'manage_system',
  VIEW_ADMIN_PANEL: 'view_admin_panel',
  
  // 特殊功能权限
  FEEDBACK_EVALUATION: 'feedback_evaluation',
  EVENT_PROCESSING: 'event_processing',
  SITE_VERIFICATION: 'site_verification',
  RESULT_FEEDBACK: 'result_feedback',
  SYSTEM_CONFIGURATION: 'system_configuration',
  DATA_REPORTS: 'data_reports',
  DATA_ANALYSIS: 'data_analysis',
  DECISION_SUPPORT: 'decision_support',
  PERFORMANCE_EVALUATION: 'performance_evaluation',
  POLICY_MAKING: 'policy_making'
};

// 角色权限映射 - 与后端保持一致
const ROLE_PERMISSIONS = {
  // 普通市民 - 事件上报、进度查询、个人中心、反馈评价
  [USER_ROLES.CITIZEN]: [
    PERMISSIONS.VIEW_PROFILE,
    PERMISSIONS.EDIT_PROFILE,
    PERMISSIONS.VIEW_EVENTS,
    PERMISSIONS.CREATE_EVENT,
    PERMISSIONS.VIEW_NOTIFICATIONS,
    PERMISSIONS.UPLOAD_FILE,
    PERMISSIONS.FEEDBACK_EVALUATION
  ],
  
  // 网格员 - 事件处理、现场核实、进度更新、结果反馈
  [USER_ROLES.GRID_WORKER]: [
    PERMISSIONS.VIEW_PROFILE,
    PERMISSIONS.EDIT_PROFILE,
    PERMISSIONS.VIEW_EVENTS,
    PERMISSIONS.CREATE_EVENT,
    PERMISSIONS.EDIT_EVENT,
    PERMISSIONS.VIEW_NOTIFICATIONS,
    PERMISSIONS.SEND_NOTIFICATION,
    PERMISSIONS.UPLOAD_FILE,
    PERMISSIONS.VIEW_STATISTICS,
    PERMISSIONS.EVENT_PROCESSING,
    PERMISSIONS.SITE_VERIFICATION,
    PERMISSIONS.RESULT_FEEDBACK
  ],
  
  // 管理员 - 事件管理、用户管理、系统配置、数据报表
  [USER_ROLES.MANAGER]: [
    PERMISSIONS.VIEW_PROFILE,
    PERMISSIONS.EDIT_PROFILE,
    PERMISSIONS.VIEW_EVENTS,
    PERMISSIONS.CREATE_EVENT,
    PERMISSIONS.EDIT_EVENT,
    PERMISSIONS.DELETE_EVENT,
    PERMISSIONS.ASSIGN_EVENT,
    PERMISSIONS.VIEW_NOTIFICATIONS,
    PERMISSIONS.SEND_NOTIFICATION,
    PERMISSIONS.UPLOAD_FILE,
    PERMISSIONS.DELETE_FILE,
    PERMISSIONS.VIEW_STATISTICS,
    PERMISSIONS.VIEW_ALL_STATISTICS,
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.VIEW_ADMIN_PANEL,
    PERMISSIONS.SYSTEM_CONFIGURATION,
    PERMISSIONS.DATA_REPORTS
  ],
  
  // 决策者 - 数据分析、决策支持、绩效评估、政策制定
  [USER_ROLES.DECISION_MAKER]: [
    PERMISSIONS.VIEW_PROFILE,
    PERMISSIONS.EDIT_PROFILE,
    PERMISSIONS.VIEW_EVENTS,
    PERMISSIONS.VIEW_NOTIFICATIONS,
    PERMISSIONS.UPLOAD_FILE,
    PERMISSIONS.VIEW_STATISTICS,
    PERMISSIONS.VIEW_ALL_STATISTICS,
    PERMISSIONS.MANAGE_SYSTEM,
    PERMISSIONS.VIEW_ADMIN_PANEL,
    PERMISSIONS.DATA_ANALYSIS,
    PERMISSIONS.DECISION_SUPPORT,
    PERMISSIONS.PERFORMANCE_EVALUATION,
    PERMISSIONS.POLICY_MAKING
  ]
};

// 角色显示名称
export const ROLE_NAMES = {
  [USER_ROLES.CITIZEN]: '普通市民',
  [USER_ROLES.GRID_WORKER]: '网格员',
  [USER_ROLES.MANAGER]: '管理员',
  [USER_ROLES.DECISION_MAKER]: '决策者'
};

// 角色描述
export const ROLE_DESCRIPTIONS = {
  [USER_ROLES.CITIZEN]: '事件上报、进度查询、个人中心、反馈评价',
  [USER_ROLES.GRID_WORKER]: '事件处理、现场核实、进度更新、结果反馈',
  [USER_ROLES.MANAGER]: '事件管理、用户管理、系统配置、数据报表',
  [USER_ROLES.DECISION_MAKER]: '数据分析、决策支持、绩效评估、政策制定'
};

/**
 * 权限管理器类
 */
export class PermissionManager {
  constructor() {
    this.currentUser = null;
    this.currentRole = null;
    this.currentPermissions = [];
  }

  /**
   * 设置当前用户
   * @param {Object} user - 用户对象
   */
  setUser(user) {
    this.currentUser = user;
    this.currentRole = user?.role;
    this.currentPermissions = this.getRolePermissions(this.currentRole);
  }

  /**
   * 获取角色权限列表
   * @param {string} role - 角色名称
   * @returns {Array} 权限列表
   */
  getRolePermissions(role) {
    return ROLE_PERMISSIONS[role] || [];
  }

  /**
   * 检查用户是否有指定权限
   * @param {string} permission - 权限名称
   * @returns {boolean} 是否有权限
   */
  hasPermission(permission) {
    return this.currentPermissions.includes(permission);
  }

  /**
   * 检查用户是否有任意一个权限
   * @param {Array} permissions - 权限列表
   * @returns {boolean} 是否有任意权限
   */
  hasAnyPermission(permissions) {
    return permissions.some(permission => this.hasPermission(permission));
  }

  /**
   * 检查用户是否有所有权限
   * @param {Array} permissions - 权限列表
   * @returns {boolean} 是否有所有权限
   */
  hasAllPermissions(permissions) {
    return permissions.every(permission => this.hasPermission(permission));
  }

  /**
   * 检查用户角色
   * @param {string} role - 角色名称
   * @returns {boolean} 是否是指定角色
   */
  hasRole(role) {
    return this.currentRole === role;
  }

  /**
   * 检查用户是否有任意一个角色
   * @param {Array} roles - 角色列表
   * @returns {boolean} 是否有任意角色
   */
  hasAnyRole(roles) {
    return roles.includes(this.currentRole);
  }

  /**
   * 获取当前用户信息
   * @returns {Object} 用户信息
   */
  getCurrentUser() {
    return this.currentUser;
  }

  /**
   * 获取当前用户角色
   * @returns {string} 角色名称
   */
  getCurrentRole() {
    return this.currentRole;
  }

  /**
   * 获取当前用户权限列表
   * @returns {Array} 权限列表
   */
  getCurrentPermissions() {
    return this.currentPermissions;
  }

  /**
   * 获取角色显示名称
   * @param {string} role - 角色名称
   * @returns {string} 显示名称
   */
  getRoleName(role = this.currentRole) {
    return ROLE_NAMES[role] || role;
  }

  /**
   * 获取角色描述
   * @param {string} role - 角色名称
   * @returns {string} 角色描述
   */
  getRoleDescription(role = this.currentRole) {
    return ROLE_DESCRIPTIONS[role] || '';
  }

  /**
   * 检查是否是管理员角色
   * @returns {boolean} 是否是管理员
   */
  isAdmin() {
    return this.hasAnyRole([USER_ROLES.MANAGER, USER_ROLES.DECISION_MAKER]);
  }

  /**
   * 检查是否是工作人员角色
   * @returns {boolean} 是否是工作人员
   */
  isStaff() {
    return this.hasAnyRole([USER_ROLES.GRID_WORKER, USER_ROLES.MANAGER, USER_ROLES.DECISION_MAKER]);
  }

  /**
   * 检查是否是普通用户
   * @returns {boolean} 是否是普通用户
   */
  isCitizen() {
    return this.hasRole(USER_ROLES.CITIZEN);
  }

  /**
   * 清除用户信息
   */
  clear() {
    this.currentUser = null;
    this.currentRole = null;
    this.currentPermissions = [];
  }

  /**
   * 获取用户可访问的菜单项
   * @returns {Array} 菜单项列表
   */
  getAccessibleMenus() {
    const menus = [];

    // 基础菜单 - 所有用户都可访问
    menus.push({
      id: 'home',
      name: '首页',
      icon: '🏠',
      path: '/',
      permission: null
    });

    menus.push({
      id: 'profile',
      name: '个人中心',
      icon: '👤',
      path: '/profile',
      permission: PERMISSIONS.VIEW_PROFILE
    });

    // 事件相关菜单
    if (this.hasPermission(PERMISSIONS.VIEW_EVENTS)) {
      menus.push({
        id: 'events',
        name: '事件管理',
        icon: '📋',
        path: '/events',
        permission: PERMISSIONS.VIEW_EVENTS
      });
    }

    // 通知菜单
    if (this.hasPermission(PERMISSIONS.VIEW_NOTIFICATIONS)) {
      menus.push({
        id: 'notifications',
        name: '通知中心',
        icon: '🔔',
        path: '/notifications',
        permission: PERMISSIONS.VIEW_NOTIFICATIONS
      });
    }

    // 统计菜单
    if (this.hasPermission(PERMISSIONS.VIEW_STATISTICS)) {
      menus.push({
        id: 'statistics',
        name: '数据统计',
        icon: '📊',
        path: '/statistics',
        permission: PERMISSIONS.VIEW_STATISTICS
      });
    }

    // 管理菜单
    if (this.hasPermission(PERMISSIONS.VIEW_ADMIN_PANEL)) {
      menus.push({
        id: 'admin',
        name: '系统管理',
        icon: '🛠️',
        path: '/admin',
        permission: PERMISSIONS.VIEW_ADMIN_PANEL
      });
    }

    return menus;
  }
}

// 创建全局权限管理器实例
export const permissionManager = new PermissionManager();

// 将权限管理器挂载到全局对象
if (typeof window !== 'undefined') {
  window.permissionManager = permissionManager;
}

export default permissionManager;
