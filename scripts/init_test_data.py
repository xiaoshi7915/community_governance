#!/usr/bin/env python3
"""
基层治理智能体系统 - 初始化测试数据脚本
创建4个不同角色的用户账号和相关测试数据
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List
import hashlib
import uuid

# 添加项目根目录到路径
sys.path.append('/opt/community_governance')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, engine
from app.models.user import User
from app.models.event import Event, EventPriority, EventStatus
from app.models.community import Community
from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationStatus

# 用户角色定义
ROLES = {
    'citizen': '市民',
    'grid_worker': '网格员', 
    'manager': '管理员',
    'decision_maker': '决策者'
}

# 测试用户数据
TEST_USERS = [
    {
        'phone': '13800138001',
        'password': 'citizen123',
        'name': '张小民',
        'role': 'citizen',
        'avatar_url': 'https://example.com/avatars/citizen.jpg'
    },
    {
        'phone': '13800138002', 
        'password': 'grid123',
        'name': '李网格',
        'role': 'grid_worker',
        'avatar_url': 'https://example.com/avatars/grid_worker.jpg'
    },
    {
        'phone': '13800138003',
        'password': 'manager123', 
        'name': '王管理',
        'role': 'manager',
        'avatar_url': 'https://example.com/avatars/manager.jpg'
    },
    {
        'phone': '13800138004',
        'password': 'decision123',
        'name': '赵决策',
        'role': 'decision_maker',
        'avatar_url': 'https://example.com/avatars/decision_maker.jpg'
    }
]

# 社区测试数据
TEST_COMMUNITIES = [
    {
        'name': '阳光社区',
        'address': '北京市朝阳区阳光街道123号',
        'description': '阳光社区是一个现代化的居民社区，拥有完善的基础设施和服务设施。',
        'latitude': 39.9042,
        'longitude': 116.4074
    },
    {
        'name': '和谐小区',
        'address': '北京市海淀区和谐路456号',
        'description': '和谐小区注重居民生活质量，提供多样化的社区服务。',
        'latitude': 39.9826,
        'longitude': 116.3194
    },
    {
        'name': '幸福家园',
        'address': '北京市西城区幸福大道789号',
        'description': '幸福家园是一个温馨的居住环境，居民关系和睦。',
        'latitude': 39.9139,
        'longitude': 116.3883
    }
]

# 事件测试数据
TEST_EVENTS = [
    {
        'title': '小区垃圾分类设施损坏',
        'description': '阳光社区3号楼下的垃圾分类箱盖子损坏，影响正常使用，需要及时维修。',
        'event_type': 'infrastructure',
        'priority': EventPriority.MEDIUM,
        'status': EventStatus.PENDING,
        'latitude': 39.9042,
        'longitude': 116.4074,
        'address': '阳光社区3号楼下'
    },
    {
        'title': '噪音扰民投诉',
        'description': '和谐小区5号楼有住户深夜装修，严重影响邻居休息，多次沟通无效。',
        'event_type': 'complaint',
        'priority': EventPriority.HIGH,
        'status': EventStatus.PROCESSING,
        'latitude': 39.9826,
        'longitude': 116.3194,
        'address': '和谐小区5号楼'
    },
    {
        'title': '社区健身器材维护',
        'description': '幸福家园健身区的跑步机出现故障，需要专业人员检修。',
        'event_type': 'maintenance',
        'priority': EventPriority.LOW,
        'status': EventStatus.COMPLETED,
        'latitude': 39.9139,
        'longitude': 116.3883,
        'address': '幸福家园健身区'
    },
    {
        'title': '社区安全隐患排查',
        'description': '发现阳光社区部分路灯不亮，存在安全隐患，需要及时处理。',
        'event_type': 'safety',
        'priority': EventPriority.HIGH,
        'status': EventStatus.PENDING,
        'latitude': 39.9042,
        'longitude': 116.4074,
        'address': '阳光社区主干道'
    },
    {
        'title': '社区文化活动组织',
        'description': '计划在和谐小区组织中秋节文艺演出，需要协调场地和设备。',
        'event_type': 'service',
        'priority': EventPriority.MEDIUM,
        'status': EventStatus.PROCESSING,
        'latitude': 39.9826,
        'longitude': 116.3194,
        'address': '和谐小区文化广场'
    }
]

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

async def create_users(session: AsyncSession) -> List[User]:
    """创建测试用户"""
    users = []
    
    print("🔄 创建测试用户...")
    
    for user_data in TEST_USERS:
        # 检查用户是否已存在
        existing_user = await session.execute(
            text("SELECT id FROM users WHERE phone = :phone"),
            {"phone": user_data['phone']}
        )
        if existing_user.fetchone():
            print(f"  ⚠️  用户 {user_data['name']} ({user_data['phone']}) 已存在，跳过")
            continue
            
        user = User(
            phone=user_data['phone'],
            password_hash=hash_password(user_data['password']),
            name=user_data['name'],
            role=user_data['role'],
            avatar_url=user_data['avatar_url'],
            is_active=True
        )
        
        session.add(user)
        users.append(user)
        print(f"  ✅ 创建用户: {user.name} ({ROLES[user.role]}) - {user.phone}")
    
    await session.commit()
    return users

async def create_communities(session: AsyncSession) -> List[Community]:
    """创建测试社区"""
    communities = []
    
    print("🔄 创建测试社区...")
    
    for community_data in TEST_COMMUNITIES:
        # 检查社区是否已存在
        existing_community = await session.execute(
            text("SELECT id FROM communities WHERE name = :name"),
            {"name": community_data['name']}
        )
        if existing_community.fetchone():
            print(f"  ⚠️  社区 {community_data['name']} 已存在，跳过")
            continue
            
        community = Community(
            name=community_data['name'],
            address=community_data['address'],
            description=community_data['description'],
            latitude=community_data['latitude'],
            longitude=community_data['longitude']
        )
        
        session.add(community)
        communities.append(community)
        print(f"  ✅ 创建社区: {community.name}")
    
    await session.commit()
    return communities

async def create_events(session: AsyncSession, users: List[User], communities: List[Community]) -> List[Event]:
    """创建测试事件"""
    events = []
    
    print("🔄 创建测试事件...")
    
    # 获取市民用户作为事件创建者
    citizen_user = next((u for u in users if u.role == 'citizen'), None)
    if not citizen_user:
        print("  ⚠️  未找到市民用户，跳过事件创建")
        return events
    
    for i, event_data in enumerate(TEST_EVENTS):
        event = Event(
            title=event_data['title'],
            description=event_data['description'],
            event_type=event_data['event_type'],
            priority=event_data['priority'],
            status=event_data['status'],
            location_lat=event_data['latitude'],
            location_lng=event_data['longitude'],
            location_address=event_data['address'],
            user_id=citizen_user.id
        )
        
        session.add(event)
        events.append(event)
        print(f"  ✅ 创建事件: {event.title}")
    
    await session.commit()
    return events

async def create_notifications(session: AsyncSession, users: List[User], events: List[Event]):
    """创建测试通知"""
    print("🔄 创建测试通知...")
    
    # 为网格员和管理员创建事件通知
    grid_worker = next((u for u in users if u.role == 'grid_worker'), None)
    manager = next((u for u in users if u.role == 'manager'), None)
    
    notification_users = [u for u in [grid_worker, manager] if u]
    
    for user in notification_users:
        for i, event in enumerate(events[:3]):  # 只为前3个事件创建通知
            notification = Notification(
                user_id=user.id,
                title=f"新事件待处理: {event.title}",
                content=f"有新的{event.event_type}事件需要您的关注和处理。",
                notification_type=NotificationType.EVENT_ASSIGNED,
                channel=NotificationChannel.IN_APP,
                recipient=user.phone,
                status=NotificationStatus.DELIVERED,
                read_at=datetime.utcnow() - timedelta(hours=i) if i > 0 else None  # 第一个通知未读，其他已读
            )
            
            session.add(notification)
            print(f"  ✅ 创建通知: {user.name} - {notification.title}")
    
    await session.commit()

async def init_database_tables():
    """初始化数据库表"""
    print("🔄 初始化数据库表...")
    
    try:
        # 导入所有模型以确保表被创建
        from app.models import user, event, community, notification
        
        # 创建所有表
        async with engine.begin() as conn:
            from app.models import Base
            await conn.run_sync(Base.metadata.create_all)
        
        print("  ✅ 数据库表初始化完成")
        
    except Exception as e:
        print(f"  ❌ 数据库表初始化失败: {e}")
        raise

async def main():
    """主函数"""
    print("🚀 开始初始化基层治理智能体系统测试数据")
    print("=" * 50)
    
    try:
        # 初始化数据库表
        await init_database_tables()
        
        # 创建数据库会话
        async with AsyncSessionLocal() as session:
            # 创建用户
            users = await create_users(session)
            
            # 创建社区
            communities = await create_communities(session)
            
            # 创建事件
            events = await create_events(session, users, communities)
            
            # 创建通知
            await create_notifications(session, users, events)
        
        print("\n" + "=" * 50)
        print("🎉 测试数据初始化完成！")
        print("\n📋 创建的测试账号:")
        print("-" * 30)
        
        for user_data in TEST_USERS:
            role_name = ROLES.get(user_data['role'], '未知')
            print(f"👤 {role_name}: {user_data['name']}")
            print(f"   📱 手机号: {user_data['phone']}")
            print(f"   🔑 密码: {user_data['password']}")
            print()
        
        print("📍 创建的社区:")
        print("-" * 30)
        for community in TEST_COMMUNITIES:
            print(f"🏘️  {community['name']} - {community['address']}")
        
        print(f"\n📊 数据统计:")
        print(f"   👥 用户: {len(TEST_USERS)} 个")
        print(f"   🏘️  社区: {len(TEST_COMMUNITIES)} 个") 
        print(f"   📋 事件: {len(TEST_EVENTS)} 个")
        print(f"   🔔 通知: 若干条")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
