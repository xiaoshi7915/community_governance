"""
用户认证服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.models.user import User
from app.core.exceptions import ValidationError, AuthenticationError, NotFoundError
from app.core.security import verify_password, create_access_token


class TestAuthService:
    """认证服务测试类"""
    
    @pytest.fixture
    def auth_service(self):
        """创建认证服务实例"""
        return AuthService()
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.exists = AsyncMock(return_value=False)
        return mock_redis
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service, db_session: AsyncSession):
        """测试创建用户成功"""
        user_data = {
            "phone": "13800138001",
            "password": "test123456",
            "name": "新用户"
        }
        
        user = await auth_service.create_user(db_session, **user_data)
        
        assert user.phone == "13800138001"
        assert user.name == "新用户"
        assert user.is_active is True
        assert verify_password("test123456", user.password_hash)
        assert user.id is not None
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_phone(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试创建重复手机号用户失败"""
        user_data = {
            "phone": test_user.phone,  # 使用已存在的手机号
            "password": "test123456",
            "name": "重复用户"
        }
        
        with pytest.raises(ValidationError, match="手机号已被注册"):
            await auth_service.create_user(db_session, **user_data)
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_phone(self, auth_service, db_session: AsyncSession):
        """测试创建用户时手机号格式无效"""
        user_data = {
            "phone": "invalid_phone",
            "password": "test123456",
            "name": "测试用户"
        }
        
        with pytest.raises(ValidationError, match="手机号格式不正确"):
            await auth_service.create_user(db_session, **user_data)
    
    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, auth_service, db_session: AsyncSession):
        """测试创建用户时密码过弱"""
        user_data = {
            "phone": "13800138002",
            "password": "123",  # 过短的密码
            "name": "测试用户"
        }
        
        with pytest.raises(ValidationError, match="密码长度至少6位"):
            await auth_service.create_user(db_session, **user_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试用户认证成功"""
        user = await auth_service.authenticate_user(db_session, test_user.phone, "test123456")
        
        assert user is not None
        assert user.id == test_user.id
        assert user.phone == test_user.phone
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试用户认证密码错误"""
        user = await auth_service.authenticate_user(db_session, test_user.phone, "wrong_password")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试用户认证用户不存在"""
        user = await auth_service.authenticate_user(db_session, "13900139000", "test123456")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试认证已禁用用户"""
        # 禁用用户
        test_user.is_active = False
        await db_session.commit()
        
        user = await auth_service.authenticate_user(db_session, test_user.phone, "test123456")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, db_session: AsyncSession, test_user: User, mock_redis):
        """测试用户登录成功"""
        with patch('app.services.auth_service.get_redis', return_value=mock_redis):
            result = await auth_service.login(db_session, test_user.phone, "test123456")
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        assert "user" in result
        assert result["user"]["id"] == str(test_user.id)
        
        # 验证Redis调用
        mock_redis.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试登录凭据无效"""
        with pytest.raises(AuthenticationError, match="手机号或密码错误"):
            await auth_service.login(db_session, test_user.phone, "wrong_password")
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试登录用户不存在"""
        with pytest.raises(AuthenticationError, match="手机号或密码错误"):
            await auth_service.login(db_session, "13900139000", "test123456")
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, db_session: AsyncSession, test_user: User, mock_redis):
        """测试刷新令牌成功"""
        # 创建刷新令牌
        refresh_token = create_access_token(
            data={"sub": str(test_user.id), "type": "refresh"},
            expires_delta=timedelta(days=7)
        )
        
        # 模拟Redis中存在该令牌
        mock_redis.exists.return_value = True
        
        with patch('app.services.auth_service.get_redis', return_value=mock_redis):
            result = await auth_service.refresh_token(db_session, refresh_token)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service, db_session: AsyncSession, mock_redis):
        """测试刷新无效令牌"""
        invalid_token = "invalid_token"
        
        with patch('app.services.auth_service.get_redis', return_value=mock_redis):
            with pytest.raises(AuthenticationError, match="无效的刷新令牌"):
                await auth_service.refresh_token(db_session, invalid_token)
    
    @pytest.mark.asyncio
    async def test_refresh_token_not_in_redis(self, auth_service, db_session: AsyncSession, test_user: User, mock_redis):
        """测试刷新令牌不在Redis中"""
        refresh_token = create_access_token(
            data={"sub": str(test_user.id), "type": "refresh"},
            expires_delta=timedelta(days=7)
        )
        
        # 模拟Redis中不存在该令牌
        mock_redis.exists.return_value = False
        
        with patch('app.services.auth_service.get_redis', return_value=mock_redis):
            with pytest.raises(AuthenticationError, match="刷新令牌已失效"):
                await auth_service.refresh_token(db_session, refresh_token)
    
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, test_user: User, mock_redis):
        """测试用户登出成功"""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        refresh_token = create_access_token(
            data={"sub": str(test_user.id), "type": "refresh"},
            expires_delta=timedelta(days=7)
        )
        
        with patch('app.services.auth_service.get_redis', return_value=mock_redis):
            result = await auth_service.logout(access_token, refresh_token)
        
        assert result is True
        # 验证Redis删除调用
        assert mock_redis.delete.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试获取当前用户成功"""
        user = await auth_service.get_current_user(db_session, test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.phone == test_user.phone
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试获取不存在的用户"""
        from uuid import uuid4
        
        with pytest.raises(NotFoundError, match="用户不存在"):
            await auth_service.get_current_user(db_session, uuid4())
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试获取已禁用用户"""
        # 禁用用户
        test_user.is_active = False
        await db_session.commit()
        
        with pytest.raises(AuthenticationError, match="用户账户已被禁用"):
            await auth_service.get_current_user(db_session, test_user.id)
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试更新用户资料成功"""
        update_data = {
            "name": "更新后的用户名",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        
        updated_user = await auth_service.update_user_profile(db_session, test_user.id, **update_data)
        
        assert updated_user.name == "更新后的用户名"
        assert updated_user.avatar_url == "https://example.com/avatar.jpg"
        assert updated_user.updated_at > test_user.updated_at
    
    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, auth_service, db_session: AsyncSession):
        """测试更新不存在用户的资料"""
        from uuid import uuid4
        
        with pytest.raises(NotFoundError, match="用户不存在"):
            await auth_service.update_user_profile(db_session, uuid4(), name="新名称")
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试修改密码成功"""
        new_password = "new_password123"
        
        result = await auth_service.change_password(
            db_session, 
            test_user.id, 
            "test123456",  # 当前密码
            new_password
        )
        
        assert result is True
        
        # 验证新密码有效
        await db_session.refresh(test_user)
        assert verify_password(new_password, test_user.password_hash)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试修改密码时当前密码错误"""
        with pytest.raises(AuthenticationError, match="当前密码错误"):
            await auth_service.change_password(
                db_session,
                test_user.id,
                "wrong_password",
                "new_password123"
            )
    
    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试修改不存在用户的密码"""
        from uuid import uuid4
        
        with pytest.raises(NotFoundError, match="用户不存在"):
            await auth_service.change_password(
                db_session,
                uuid4(),
                "current_password",
                "new_password"
            )
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试重置密码成功"""
        new_password = "reset_password123"
        
        result = await auth_service.reset_password(db_session, test_user.phone, new_password)
        
        assert result is True
        
        # 验证新密码有效
        await db_session.refresh(test_user)
        assert verify_password(new_password, test_user.password_hash)
    
    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试重置不存在用户的密码"""
        with pytest.raises(NotFoundError, match="用户不存在"):
            await auth_service.reset_password(db_session, "13900139000", "new_password")
    
    def test_validate_phone_success(self, auth_service):
        """测试手机号验证成功"""
        valid_phones = [
            "13800138000",
            "15912345678",
            "18612345678"
        ]
        
        for phone in valid_phones:
            assert auth_service._validate_phone(phone) is True
    
    def test_validate_phone_failure(self, auth_service):
        """测试手机号验证失败"""
        invalid_phones = [
            "1380013800",  # 太短
            "138001380001",  # 太长
            "12800138000",  # 不是有效前缀
            "abc12345678",  # 包含字母
            "",  # 空字符串
            None  # None值
        ]
        
        for phone in invalid_phones:
            assert auth_service._validate_phone(phone) is False
    
    def test_validate_password_success(self, auth_service):
        """测试密码验证成功"""
        valid_passwords = [
            "123456",
            "password123",
            "very_long_password_with_special_chars!@#"
        ]
        
        for password in valid_passwords:
            assert auth_service._validate_password(password) is True
    
    def test_validate_password_failure(self, auth_service):
        """测试密码验证失败"""
        invalid_passwords = [
            "12345",  # 太短
            "",  # 空字符串
            None  # None值
        ]
        
        for password in invalid_passwords:
            assert auth_service._validate_password(password) is False
    
    @pytest.mark.asyncio
    async def test_get_user_by_phone_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试通过手机号获取用户成功"""
        user = await auth_service.get_user_by_phone(db_session, test_user.phone)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.phone == test_user.phone
    
    @pytest.mark.asyncio
    async def test_get_user_by_phone_not_found(self, auth_service, db_session: AsyncSession):
        """测试通过手机号获取不存在的用户"""
        user = await auth_service.get_user_by_phone(db_session, "13900139000")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_is_phone_registered_true(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试手机号已注册"""
        result = await auth_service.is_phone_registered(db_session, test_user.phone)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_phone_registered_false(self, auth_service, db_session: AsyncSession):
        """测试手机号未注册"""
        result = await auth_service.is_phone_registered(db_session, "13900139000")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试禁用用户成功"""
        result = await auth_service.deactivate_user(db_session, test_user.id)
        
        assert result is True
        await db_session.refresh(test_user)
        assert test_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试禁用不存在的用户"""
        from uuid import uuid4
        
        with pytest.raises(NotFoundError, match="用户不存在"):
            await auth_service.deactivate_user(db_session, uuid4())
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, auth_service, db_session: AsyncSession, test_user: User):
        """测试激活用户成功"""
        # 先禁用用户
        test_user.is_active = False
        await db_session.commit()
        
        result = await auth_service.activate_user(db_session, test_user.id)
        
        assert result is True
        await db_session.refresh(test_user)
        assert test_user.is_active is True
    
    @pytest.mark.asyncio
    async def test_activate_user_not_found(self, auth_service, db_session: AsyncSession):
        """测试激活不存在的用户"""
        from uuid import uuid4
        
        with pytest.raises(NotFoundError, match="用户不存在"):
            await auth_service.activate_user(db_session, uuid4())


if __name__ == "__main__":
    pytest.main([__file__])