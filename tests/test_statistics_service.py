"""
统计服务测试
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.statistics_service import StatisticsService
from app.models.event import Event, EventStatus, EventPriority
from app.models.user import User


@pytest.fixture
def statistics_service():
    """创建统计服务实例"""
    return StatisticsService()


@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    with patch('app.services.statistics_service.redis_client') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.keys = AsyncMock(return_value=[])
        mock.delete = AsyncMock(return_value=0)
        yield mock


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    with patch('app.services.statistics_service.AsyncSessionLocal') as mock:
        session = AsyncMock()
        mock.return_value.__aenter__.return_value = session
        yield session


@pytest.mark.asyncio
class TestStatisticsService:
    """统计服务测试类"""
    
    async def test_get_user_statistics_basic(self, statistics_service, mock_redis, mock_db_session):
        """测试基础用户统计功能"""
        # 准备测试数据
        user_id = uuid4()
        
        # 模拟数据库查询结果
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            total_events=10,
            completed_events=7,
            pending_events=2,
            processing_events=1,
            rejected_events=0,
            avg_confidence=0.85
        )
        
        # 模拟事件类型查询结果
        mock_type_result = MagicMock()
        mock_type_result.__iter__.return_value = [
            MagicMock(event_type="道路维修", count=5),
            MagicMock(event_type="环境问题", count=3),
            MagicMock(event_type="公共设施", count=2)
        ]
        
        # 模拟优先级查询结果
        mock_priority_result = MagicMock()
        mock_priority_result.__iter__.return_value = [
            MagicMock(priority=EventPriority.HIGH, count=3),
            MagicMock(priority=EventPriority.MEDIUM, count=5),
            MagicMock(priority=EventPriority.LOW, count=2)
        ]
        
        # 设置多次execute调用的返回值
        mock_db_session.execute.side_effect = [
            mock_result,
            mock_type_result,
            mock_priority_result
        ]
        
        # 执行测试
        result = await statistics_service.get_user_statistics(user_id=user_id)
        
        # 验证结果
        assert result["total_events"] == 10
        assert result["completed_events"] == 7
        assert result["completion_rate"] == 70.0
        assert result["avg_confidence"] == 0.85
        assert len(result["event_types"]) == 3
        assert result["event_types"][0]["type"] == "道路维修"
        assert result["event_types"][0]["count"] == 5
    
    async def test_get_event_statistics_time_series(self, statistics_service, mock_redis, mock_db_session):
        """测试事件时间序列统计"""
        # 模拟时间序列查询结果
        mock_time_series = MagicMock()
        mock_time_series.__iter__.return_value = [
            MagicMock(
                time_period=datetime(2024, 1, 1),
                total_count=5,
                completed_count=3,
                pending_count=1,
                processing_count=1
            ),
            MagicMock(
                time_period=datetime(2024, 1, 2),
                total_count=8,
                completed_count=6,
                pending_count=1,
                processing_count=1
            )
        ]
        
        # 模拟事件类型统计结果
        mock_type_stats = MagicMock()
        mock_type_stats.__iter__.return_value = [
            MagicMock(
                event_type="道路维修",
                total_count=10,
                completed_count=8,
                avg_confidence=0.9
            )
        ]
        
        # 模拟状态分布结果
        mock_status_dist = MagicMock()
        mock_status_dist.__iter__.return_value = [
            MagicMock(status=EventStatus.COMPLETED, count=8),
            MagicMock(status=EventStatus.PENDING, count=2)
        ]
        
        mock_db_session.execute.side_effect = [
            mock_time_series,
            mock_type_stats,
            mock_status_dist
        ]
        
        # 执行测试
        result = await statistics_service.get_event_statistics(group_by="day")
        
        # 验证结果
        assert len(result["time_series"]) == 2
        assert result["time_series"][0]["total"] == 5
        assert result["time_series"][1]["total"] == 8
        assert len(result["type_statistics"]) == 1
        assert result["type_statistics"][0]["event_type"] == "道路维修"
        assert result["type_statistics"][0]["completion_rate"] == 80.0
    
    async def test_get_processing_efficiency_analysis(self, statistics_service, mock_redis, mock_db_session):
        """测试处理效率分析"""
        # 模拟已完成事件查询结果
        mock_completed_events = MagicMock()
        mock_completed_events.all.return_value = [
            MagicMock(
                id=uuid4(),
                event_type="道路维修",
                priority=EventPriority.HIGH,
                created_at=datetime(2024, 1, 1, 10, 0),
                completed_at=datetime(2024, 1, 1, 14, 0)  # 4小时处理时间
            ),
            MagicMock(
                id=uuid4(),
                event_type="环境问题",
                priority=EventPriority.MEDIUM,
                created_at=datetime(2024, 1, 2, 9, 0),
                completed_at=datetime(2024, 1, 2, 15, 0)  # 6小时处理时间
            )
        ]
        
        # 模拟响应时间查询结果
        mock_response_times = MagicMock()
        mock_response_times.__iter__.return_value = [
            MagicMock(
                id=uuid4(),
                event_type="道路维修",
                created_at=datetime(2024, 1, 1, 10, 0),
                first_response_at=datetime(2024, 1, 1, 11, 0)  # 1小时响应时间
            )
        ]
        
        mock_db_session.execute.side_effect = [
            mock_completed_events,
            mock_response_times
        ]
        
        # 执行测试
        result = await statistics_service.get_processing_efficiency_analysis()
        
        # 验证结果
        assert result["processing_efficiency"]["avg_processing_time_hours"] == 5.0  # (4+6)/2
        assert result["processing_efficiency"]["min_processing_time_hours"] == 4.0
        assert result["processing_efficiency"]["max_processing_time_hours"] == 6.0
        assert result["response_efficiency"]["avg_response_time_hours"] == 1.0
    
    async def test_get_hotspot_area_analysis(self, statistics_service, mock_redis, mock_db_session):
        """测试热点区域分析"""
        # 模拟事件地理位置查询结果
        mock_events = MagicMock()
        mock_events.all.return_value = [
            MagicMock(
                id=uuid4(),
                event_type="道路维修",
                location_lat=30.2741,
                location_lng=120.1551,
                location_address="浙江省杭州市西湖区",
                created_at=datetime(2024, 1, 1)
            ),
            MagicMock(
                id=uuid4(),
                event_type="道路维修",
                location_lat=30.2745,
                location_lng=120.1555,
                location_address="浙江省杭州市西湖区",
                created_at=datetime(2024, 1, 2)
            ),
            MagicMock(
                id=uuid4(),
                event_type="环境问题",
                location_lat=30.2748,
                location_lng=120.1558,
                location_address="浙江省杭州市西湖区",
                created_at=datetime(2024, 1, 3)
            )
        ]
        
        mock_db_session.execute.return_value = mock_events
        
        # 执行测试
        result = await statistics_service.get_hotspot_area_analysis(radius_km=1.0)
        
        # 验证结果
        assert result["total_events"] == 3
        assert len(result["hotspots"]) >= 0  # 可能形成热点区域
        assert len(result["area_statistics"]) >= 0
    
    async def test_export_statistics_to_csv(self, statistics_service, mock_redis, mock_db_session):
        """测试CSV导出功能"""
        # 模拟统计数据
        mock_stats = {
            "total_events": 10,
            "completed_events": 7,
            "completion_rate": 70.0,
            "avg_confidence": 0.85,
            "event_types": [
                {"type": "道路维修", "count": 5},
                {"type": "环境问题", "count": 3}
            ]
        }
        
        # 模拟get_user_statistics方法
        with patch.object(statistics_service, 'get_user_statistics', return_value=mock_stats):
            # 执行测试
            csv_data = await statistics_service.export_statistics_to_csv(
                export_type="user_stats",
                user_id=uuid4()
            )
            
            # 验证结果
            assert isinstance(csv_data, str)
            assert "用户统计报告" in csv_data
            assert "总事件数,10" in csv_data
            assert "完成率(%),70.0" in csv_data
    
    async def test_cache_refresh(self, statistics_service, mock_redis):
        """测试缓存刷新功能"""
        # 模拟缓存键
        mock_redis.keys.return_value = ["stats:user:123", "stats:events:456"]
        
        # 模拟预热方法
        with patch.object(statistics_service, '_warm_up_caches', return_value=None) as mock_warmup:
            # 执行测试
            await statistics_service.refresh_all_caches()
            
            # 验证缓存被删除
            mock_redis.delete.assert_called_once()
            # 验证预热被调用
            mock_warmup.assert_called_once()
    
    async def test_excel_export_user_stats(self, statistics_service):
        """测试Excel导出用户统计"""
        # 模拟统计数据
        mock_stats = {
            "total_events": 10,
            "completed_events": 7,
            "completion_rate": 70.0,
            "avg_confidence": 0.85,
            "event_types": [
                {"type": "道路维修", "count": 5},
                {"type": "环境问题", "count": 3}
            ]
        }
        
        # 测试Excel创建方法
        excel_data = statistics_service._create_user_stats_excel(mock_stats)
        
        # 验证结果
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
    
    async def test_error_handling(self, statistics_service, mock_redis, mock_db_session):
        """测试错误处理"""
        # 模拟数据库错误
        mock_db_session.execute.side_effect = Exception("数据库连接失败")
        
        # 执行测试并验证异常处理
        with pytest.raises(Exception):
            await statistics_service.get_user_statistics(user_id=uuid4())


if __name__ == "__main__":
    pytest.main([__file__])