/**
 * 角色权限管理器
 * 管理不同用户角色的权限和界面显示
 */
export class RoleManager {
  constructor() {
    this.roles = {
      'citizen': {
        name: '普通市民',
        permissions: [
          'event.create',
          'event.view_own',
          'profile.view',
          'profile.edit'
        ],
        navigation: ['home', 'tracking', 'profile'],
        features: {
          canCreateEvent: true,
          canViewAllEvents: false,
          canAssignEvents: false,
          canViewStatistics: false,
          canManageUsers: false
        }
      },
      'grid_worker': {
        name: '网格员',
        permissions: [
          'event.create',
          'event.view',
          'event.assign',
          'event.update',
          'event.comment',
          'profile.view',
          'profile.edit'
        ],
        navigation: ['home', 'tracking', 'history', 'profile'],
        features: {
          canCreateEvent: true,
          canViewAllEvents: true,
          canAssignEvents: true,
          canViewStatistics: true,
          canManageUsers: false
        }
      },
      'manager': {
        name: '管理员',
        permissions: [
          'event.*',
          'user.view',
          'statistics.view',
          'profile.view',
          'profile.edit'
        ],
        navigation: ['home', 'tracking', 'history', 'profile'],
        features: {
          canCreateEvent: true,
          canViewAllEvents: true,
          canAssignEvents: true,
          canViewStatistics: true,
          canManageUsers: true
        }
      },
      'decision_maker': {
        name: '决策者',
        permissions: ['*'],
        navigation: ['home', 'tracking', 'history', 'profile'],
        features: {
          canCreateEvent: true,
          canViewAllEvents: true,
          canAssignEvents: true,
          canViewStatistics: true,
          canManageUsers: true,
          canViewAnalytics: true
        }
      }
    };
  }

  /**
   * 获取用户角色信息
   * @param {string} role - 用户角色
   * @returns {Object} 角色信息
   */
  getRoleInfo(role) {
    return this.roles[role] || this.roles['citizen'];
  }

  /**
   * 检查用户是否有特定权限
   * @param {string} userRole - 用户角色
   * @param {string} permission - 权限名称
   * @returns {boolean} 是否有权限
   */
  hasPermission(userRole, permission) {
    const roleInfo = this.getRoleInfo(userRole);
    
    // 超级权限
    if (roleInfo.permissions.includes('*')) {
      return true;
    }
    
    // 通配符权限
    for (const perm of roleInfo.permissions) {
      if (perm.endsWith('*')) {
        const prefix = perm.slice(0, -1);
        if (permission.startsWith(prefix)) {
          return true;
        }
      }
    }
    
    // 精确匹配
    return roleInfo.permissions.includes(permission);
  }

  /**
   * 获取用户可访问的导航项
   * @param {string} userRole - 用户角色
   * @returns {Array} 导航项列表
   */
  getNavigationItems(userRole) {
    const roleInfo = this.getRoleInfo(userRole);
    return roleInfo.navigation || ['home', 'profile'];
  }

  /**
   * 检查用户是否可以访问特定功能
   * @param {string} userRole - 用户角色
   * @param {string} feature - 功能名称
   * @returns {boolean} 是否可以访问
   */
  canAccessFeature(userRole, feature) {
    const roleInfo = this.getRoleInfo(userRole);
    return roleInfo.features[feature] || false;
  }

  /**
   * 根据角色过滤界面元素
   * @param {string} userRole - 用户角色
   * @param {Array} elements - 界面元素列表
   * @returns {Array} 过滤后的元素列表
   */
  filterUIElements(userRole, elements) {
    return elements.filter(element => {
      if (!element.requiredPermission) return true;
      return this.hasPermission(userRole, element.requiredPermission);
    });
  }

  /**
   * 获取角色特定的首页配置
   * @param {string} userRole - 用户角色
   * @returns {Object} 首页配置
   */
  getHomePageConfig(userRole) {
    const configs = {
      'citizen': {
        showCreateEvent: true,
        showMyEvents: true,
        showAllEvents: false,
        showStatistics: false,
        showManagement: false
      },
      'grid_worker': {
        showCreateEvent: true,
        showMyEvents: true,
        showAllEvents: true,
        showStatistics: true,
        showManagement: false
      },
      'manager': {
        showCreateEvent: true,
        showMyEvents: true,
        showAllEvents: true,
        showStatistics: true,
        showManagement: true
      },
      'decision_maker': {
        showCreateEvent: true,
        showMyEvents: true,
        showAllEvents: true,
        showStatistics: true,
        showManagement: true,
        showAnalytics: true
      }
    };
    
    return configs[userRole] || configs['citizen'];
  }

  /**
   * 获取角色特定的事件列表配置
   * @param {string} userRole - 用户角色
   * @returns {Object} 事件列表配置
   */
  getEventListConfig(userRole) {
    const configs = {
      'citizen': {
        showOnlyOwn: true,
        canAssign: false,
        canChangeStatus: false,
        canDelete: false
      },
      'grid_worker': {
        showOnlyOwn: false,
        canAssign: true,
        canChangeStatus: true,
        canDelete: false
      },
      'manager': {
        showOnlyOwn: false,
        canAssign: true,
        canChangeStatus: true,
        canDelete: true
      },
      'decision_maker': {
        showOnlyOwn: false,
        canAssign: true,
        canChangeStatus: true,
        canDelete: true
      }
    };
    
    return configs[userRole] || configs['citizen'];
  }

  /**
   * 获取角色显示名称
   * @param {string} role - 角色代码
   * @returns {string} 角色显示名称
   */
  getRoleName(role) {
    const roleInfo = this.getRoleInfo(role);
    return roleInfo.name;
  }

  /**
   * 获取所有角色列表
   * @returns {Array} 角色列表
   */
  getAllRoles() {
    return Object.keys(this.roles).map(key => ({
      code: key,
      name: this.roles[key].name,
      permissions: this.roles[key].permissions.length
    }));
  }
}

// 创建全局实例
export const roleManager = new RoleManager();

// 设置全局引用
if (typeof window !== 'undefined') {
  window.roleManager = roleManager;
}