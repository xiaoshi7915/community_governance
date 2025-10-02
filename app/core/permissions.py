"""
权限控制模块
基于角色的访问控制 (RBAC)
"""
from typing import List, Optional
from functools import wraps
from fastapi import Depends, HTTPException, status
from app.core.auth_middleware import get_current_user
from app.models.user import User


class UserRole:
    """用户角色常量"""
    CITIZEN = "citizen"          # 市民
    GRID_WORKER = "grid_worker"  # 网格员
    MANAGER = "manager"          # 管理员
    DECISION_MAKER = "decision_maker"  # 决策者


class Permission:
    """权限常量"""
    # 基础权限
    VIEW_PROFILE = "view_profile"
    EDIT_PROFILE = "edit_profile"
    
    # 事件相关权限
    VIEW_EVENTS = "view_events"
    CREATE_EVENT = "create_event"
    EDIT_EVENT = "edit_event"
    DELETE_EVENT = "delete_event"
    ASSIGN_EVENT = "assign_event"
    
    # 通知相关权限
    VIEW_NOTIFICATIONS = "view_notifications"
    SEND_NOTIFICATION = "send_notification"
    
    # 文件相关权限
    UPLOAD_FILE = "upload_file"
    DELETE_FILE = "delete_file"
    
    # 统计相关权限
    VIEW_STATISTICS = "view_statistics"
    VIEW_ALL_STATISTICS = "view_all_statistics"
    
    # 管理员权限
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_ADMIN_PANEL = "view_admin_panel"


# 角色权限映射 - 根据系统设计图更新
ROLE_PERMISSIONS = {
    # 普通市民 - 事件上报、进度查询、个人中心、反馈评价
    UserRole.CITIZEN: [
        Permission.VIEW_PROFILE,        # 个人中心
        Permission.EDIT_PROFILE,        # 个人中心
        Permission.VIEW_EVENTS,         # 进度查询
        Permission.CREATE_EVENT,        # 事件上报
        Permission.VIEW_NOTIFICATIONS,  # 通知查看
        Permission.UPLOAD_FILE,         # 文件上传（事件相关）
        "feedback_evaluation",          # 反馈评价
    ],
    
    # 网格员 - 事件处理、现场核实、进度更新、结果反馈
    UserRole.GRID_WORKER: [
        Permission.VIEW_PROFILE,        # 个人中心
        Permission.EDIT_PROFILE,        # 个人中心
        Permission.VIEW_EVENTS,         # 查看事件
        Permission.CREATE_EVENT,        # 创建事件
        Permission.EDIT_EVENT,          # 进度更新
        Permission.VIEW_NOTIFICATIONS,  # 通知查看
        Permission.SEND_NOTIFICATION,   # 发送通知
        Permission.UPLOAD_FILE,         # 文件上传
        Permission.VIEW_STATISTICS,     # 基础统计
        "event_processing",             # 事件处理
        "site_verification",            # 现场核实
        "result_feedback",              # 结果反馈
    ],
    
    # 管理员 - 事件管理、用户管理、系统配置、数据报表
    UserRole.MANAGER: [
        Permission.VIEW_PROFILE,        # 个人中心
        Permission.EDIT_PROFILE,        # 个人中心
        Permission.VIEW_EVENTS,         # 事件管理
        Permission.CREATE_EVENT,        # 创建事件
        Permission.EDIT_EVENT,          # 编辑事件
        Permission.DELETE_EVENT,        # 删除事件
        Permission.ASSIGN_EVENT,        # 分配事件
        Permission.VIEW_NOTIFICATIONS,  # 通知查看
        Permission.SEND_NOTIFICATION,   # 发送通知
        Permission.UPLOAD_FILE,         # 文件上传
        Permission.DELETE_FILE,         # 文件删除
        Permission.VIEW_STATISTICS,     # 数据报表
        Permission.VIEW_ALL_STATISTICS, # 全部统计
        Permission.MANAGE_USERS,        # 用户管理
        Permission.VIEW_ADMIN_PANEL,    # 管理面板
        "system_configuration",         # 系统配置
        "data_reports",                 # 数据报表
    ],
    
    # 决策者 - 数据分析、决策支持、绩效评估、政策制定
    UserRole.DECISION_MAKER: [
        Permission.VIEW_PROFILE,        # 个人中心
        Permission.EDIT_PROFILE,        # 个人中心
        Permission.VIEW_EVENTS,         # 查看事件
        Permission.VIEW_NOTIFICATIONS,  # 通知查看
        Permission.UPLOAD_FILE,         # 文件上传
        Permission.VIEW_STATISTICS,     # 数据分析
        Permission.VIEW_ALL_STATISTICS, # 全部统计
        Permission.MANAGE_SYSTEM,       # 系统管理
        Permission.VIEW_ADMIN_PANEL,    # 管理面板
        "data_analysis",                # 数据分析
        "decision_support",             # 决策支持
        "performance_evaluation",       # 绩效评估
        "policy_making",                # 政策制定
    ],
}


def has_permission(user: User, permission: str) -> bool:
    """
    检查用户是否有指定权限
    
    Args:
        user: 用户对象
        permission: 权限名称
        
    Returns:
        bool: 是否有权限
    """
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[str]) -> bool:
    """
    检查用户是否有任意一个指定权限
    
    Args:
        user: 用户对象
        permissions: 权限列表
        
    Returns:
        bool: 是否有任意权限
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[str]) -> bool:
    """
    检查用户是否有所有指定权限
    
    Args:
        user: 用户对象
        permissions: 权限列表
        
    Returns:
        bool: 是否有所有权限
    """
    return all(has_permission(user, perm) for perm in permissions)


def require_permission(permission: str):
    """
    权限检查装饰器
    
    Args:
        permission: 需要的权限
        
    Returns:
        装饰器函数
    """
    def decorator(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要权限: {permission}"
            )
        return current_user
    
    return decorator


def require_any_permission(permissions: List[str]):
    """
    任意权限检查装饰器
    
    Args:
        permissions: 权限列表
        
    Returns:
        装饰器函数
    """
    def decorator(current_user: User = Depends(get_current_user)):
        if not has_any_permission(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下任意权限: {', '.join(permissions)}"
            )
        return current_user
    
    return decorator


def require_all_permissions(permissions: List[str]):
    """
    所有权限检查装饰器
    
    Args:
        permissions: 权限列表
        
    Returns:
        装饰器函数
    """
    def decorator(current_user: User = Depends(get_current_user)):
        if not has_all_permissions(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下所有权限: {', '.join(permissions)}"
            )
        return current_user
    
    return decorator


def require_role(role: str):
    """
    角色检查装饰器
    
    Args:
        role: 需要的角色
        
    Returns:
        装饰器函数
    """
    def decorator(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色: {role}"
            )
        return current_user
    
    return decorator


def require_any_role(roles: List[str]):
    """
    任意角色检查装饰器
    
    Args:
        roles: 角色列表
        
    Returns:
        装饰器函数
    """
    def decorator(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下任意角色: {', '.join(roles)}"
            )
        return current_user
    
    return decorator


# 便捷的权限检查函数
def require_admin():
    """管理员权限检查"""
    return require_any_role([UserRole.MANAGER, UserRole.DECISION_MAKER])


def require_staff():
    """工作人员权限检查（网格员及以上）"""
    return require_any_role([UserRole.GRID_WORKER, UserRole.MANAGER, UserRole.DECISION_MAKER])


def require_manager():
    """管理员权限检查"""
    return require_role(UserRole.MANAGER)


def require_decision_maker():
    """决策者权限检查"""
    return require_role(UserRole.DECISION_MAKER)
