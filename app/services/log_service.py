"""
日志服务
提供日志搜索、过滤、分析等功能
"""
import os
import re
import json
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class LogEntry:
    """日志条目数据类"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    process_time: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "logger_name": self.logger_name,
            "message": self.message,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "process_time": self.process_time,
            "error_details": self.error_details,
            "source_file": self.source_file,
            "line_number": self.line_number
        }


@dataclass
class LogSearchFilter:
    """日志搜索过滤器"""
    query: Optional[str] = None
    level: Optional[str] = None
    logger_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    limit: int = 100
    offset: int = 0


class LogParser:
    """日志解析器"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # 日志格式正则表达式
        self.patterns = {
            # 标准日志格式
            "standard": re.compile(
                r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)'
                r'\s+\|\s+(?P<level>\w+)\s+\|\s+(?P<logger>\S+)\s+\|\s+'
                r'(?P<message>.*)'
            ),
            
            # JSON格式日志
            "json": re.compile(r'^\{.*\}$'),
            
            # 结构化日志格式
            "structured": re.compile(
                r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)'
                r'\s+-\s+(?P<logger>\S+)\s+-\s+(?P<level>\w+)\s+-\s+'
                r'(?P<message>.*)'
            )
        }
    
    def parse_log_line(self, line: str, source_file: str = None) -> Optional[LogEntry]:
        """解析单行日志"""
        try:
            line = line.strip()
            if not line:
                return None
            
            # 尝试JSON格式
            if self.patterns["json"].match(line):
                return self._parse_json_log(line, source_file)
            
            # 尝试标准格式
            match = self.patterns["standard"].match(line)
            if match:
                return self._parse_standard_log(match, source_file)
            
            # 尝试结构化格式
            match = self.patterns["structured"].match(line)
            if match:
                return self._parse_structured_log(match, source_file)
            
            # 如果都不匹配，创建简单的日志条目
            return LogEntry(
                timestamp=datetime.now(),
                level="UNKNOWN",
                logger_name="unknown",
                message=line,
                source_file=source_file
            )
            
        except Exception as e:
            self.logger.warning(f"解析日志行失败: {line[:100]}..., {e}")
            return None
    
    def _parse_json_log(self, line: str, source_file: str = None) -> Optional[LogEntry]:
        """解析JSON格式日志"""
        try:
            data = json.loads(line)
            
            # 解析时间戳
            timestamp_str = data.get("timestamp", data.get("time", ""))
            timestamp = self._parse_timestamp(timestamp_str)
            
            return LogEntry(
                timestamp=timestamp,
                level=data.get("level", "INFO"),
                logger_name=data.get("logger", data.get("name", "unknown")),
                message=data.get("message", data.get("msg", "")),
                request_id=data.get("request_id"),
                user_id=data.get("user_id"),
                endpoint=data.get("endpoint"),
                method=data.get("method"),
                status_code=data.get("status_code"),
                process_time=data.get("process_time"),
                error_details=data.get("error_details"),
                source_file=source_file
            )
            
        except Exception as e:
            self.logger.warning(f"解析JSON日志失败: {e}")
            return None
    
    def _parse_standard_log(self, match, source_file: str = None) -> LogEntry:
        """解析标准格式日志"""
        timestamp = self._parse_timestamp(match.group("timestamp"))
        
        return LogEntry(
            timestamp=timestamp,
            level=match.group("level"),
            logger_name=match.group("logger"),
            message=match.group("message"),
            source_file=source_file
        )
    
    def _parse_structured_log(self, match, source_file: str = None) -> LogEntry:
        """解析结构化格式日志"""
        timestamp = self._parse_timestamp(match.group("timestamp"))
        
        return LogEntry(
            timestamp=timestamp,
            level=match.group("level"),
            logger_name=match.group("logger"),
            message=match.group("message"),
            source_file=source_file
        )
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析时间戳"""
        if not timestamp_str:
            return datetime.now()
        
        # 尝试不同的时间格式
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S,%f",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # 如果都失败，返回当前时间
        return datetime.now()


class LogService:
    """日志服务"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.parser = LogParser()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 日志文件路径
        self.log_directory = Path("logs")
        self.log_files_pattern = ["*.log", "*.log.*"]
    
    async def search_logs(self, filter_params: LogSearchFilter) -> Tuple[List[LogEntry], int]:
        """搜索日志"""
        try:
            # 获取日志文件列表
            log_files = await self._get_log_files()
            
            # 并行搜索日志文件
            tasks = []
            for log_file in log_files:
                task = asyncio.create_task(
                    self._search_log_file(log_file, filter_params)
                )
                tasks.append(task)
            
            # 等待所有搜索任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            all_entries = []
            for result in results:
                if isinstance(result, list):
                    all_entries.extend(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"搜索日志文件失败: {result}")
            
            # 按时间排序
            all_entries.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 应用分页
            total_count = len(all_entries)
            start_idx = filter_params.offset
            end_idx = start_idx + filter_params.limit
            
            return all_entries[start_idx:end_idx], total_count
            
        except Exception as e:
            self.logger.error(f"搜索日志失败: {e}")
            raise
    
    async def _get_log_files(self) -> List[Path]:
        """获取日志文件列表"""
        log_files = []
        
        if not self.log_directory.exists():
            return log_files
        
        # 获取所有日志文件
        for pattern in self.log_files_pattern:
            log_files.extend(self.log_directory.glob(pattern))
        
        # 按修改时间排序（最新的在前）
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return log_files
    
    async def _search_log_file(self, log_file: Path, filter_params: LogSearchFilter) -> List[LogEntry]:
        """搜索单个日志文件"""
        try:
            # 在线程池中执行文件读取
            loop = asyncio.get_event_loop()
            entries = await loop.run_in_executor(
                self.executor,
                self._search_file_sync,
                log_file,
                filter_params
            )
            
            return entries
            
        except Exception as e:
            self.logger.warning(f"搜索日志文件失败: {log_file}, {e}")
            return []
    
    def _search_file_sync(self, log_file: Path, filter_params: LogSearchFilter) -> List[LogEntry]:
        """同步搜索文件"""
        entries = []
        
        try:
            # 判断是否为压缩文件
            if log_file.suffix == '.gz':
                file_opener = gzip.open
                mode = 'rt'
            else:
                file_opener = open
                mode = 'r'
            
            with file_opener(log_file, mode, encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # 解析日志行
                    entry = self.parser.parse_log_line(line, str(log_file))
                    if not entry:
                        continue
                    
                    entry.line_number = line_num
                    
                    # 应用过滤条件
                    if self._matches_filter(entry, filter_params):
                        entries.append(entry)
                        
                        # 限制单个文件的结果数量
                        if len(entries) >= filter_params.limit * 2:
                            break
            
        except Exception as e:
            self.logger.warning(f"读取日志文件失败: {log_file}, {e}")
        
        return entries
    
    def _matches_filter(self, entry: LogEntry, filter_params: LogSearchFilter) -> bool:
        """检查日志条目是否匹配过滤条件"""
        
        # 时间范围过滤
        if filter_params.start_time and entry.timestamp < filter_params.start_time:
            return False
        
        if filter_params.end_time and entry.timestamp > filter_params.end_time:
            return False
        
        # 日志级别过滤
        if filter_params.level and entry.level != filter_params.level:
            return False
        
        # 记录器名称过滤
        if filter_params.logger_name and filter_params.logger_name not in entry.logger_name:
            return False
        
        # 请求ID过滤
        if filter_params.request_id and entry.request_id != filter_params.request_id:
            return False
        
        # 用户ID过滤
        if filter_params.user_id and entry.user_id != filter_params.user_id:
            return False
        
        # 端点过滤
        if filter_params.endpoint and entry.endpoint != filter_params.endpoint:
            return False
        
        # HTTP方法过滤
        if filter_params.method and entry.method != filter_params.method:
            return False
        
        # 状态码过滤
        if filter_params.status_code and entry.status_code != filter_params.status_code:
            return False
        
        # 关键词搜索
        if filter_params.query:
            query_lower = filter_params.query.lower()
            if (query_lower not in entry.message.lower() and
                query_lower not in entry.logger_name.lower()):
                return False
        
        return True
    
    async def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            filter_params = LogSearchFilter(
                start_time=start_time,
                end_time=end_time,
                limit=10000  # 获取更多数据用于统计
            )
            
            entries, total_count = await self.search_logs(filter_params)
            
            # 统计各种指标
            level_counts = {}
            logger_counts = {}
            hourly_counts = {}
            error_messages = []
            
            for entry in entries:
                # 日志级别统计
                level_counts[entry.level] = level_counts.get(entry.level, 0) + 1
                
                # 记录器统计
                logger_counts[entry.logger_name] = logger_counts.get(entry.logger_name, 0) + 1
                
                # 按小时统计
                hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
                hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
                
                # 收集错误消息
                if entry.level in ['ERROR', 'CRITICAL']:
                    error_messages.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "message": entry.message[:200],  # 限制长度
                        "logger": entry.logger_name
                    })
            
            return {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": hours
                },
                "total_entries": total_count,
                "level_distribution": level_counts,
                "top_loggers": dict(sorted(logger_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "hourly_distribution": hourly_counts,
                "recent_errors": error_messages[:20],  # 最近20个错误
                "error_rate": level_counts.get('ERROR', 0) / max(total_count, 1) * 100
            }
            
        except Exception as e:
            self.logger.error(f"获取日志统计失败: {e}")
            raise
    
    async def export_logs(
        self, 
        filter_params: LogSearchFilter, 
        format_type: str = "json"
    ) -> str:
        """导出日志"""
        try:
            entries, _ = await self.search_logs(filter_params)
            
            # 确保导出目录存在
            export_dir = Path("exports/logs")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.{format_type}"
            filepath = export_dir / filename
            
            # 导出数据
            if format_type == "json":
                await self._export_json(entries, filepath)
            elif format_type == "csv":
                await self._export_csv(entries, filepath)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"导出日志失败: {e}")
            raise
    
    async def _export_json(self, entries: List[LogEntry], filepath: Path):
        """导出为JSON格式"""
        data = {
            "export_time": datetime.now().isoformat(),
            "total_entries": len(entries),
            "logs": [entry.to_dict() for entry in entries]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def _export_csv(self, entries: List[LogEntry], filepath: Path):
        """导出为CSV格式"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                'timestamp', 'level', 'logger_name', 'message',
                'request_id', 'user_id', 'endpoint', 'method',
                'status_code', 'process_time', 'source_file', 'line_number'
            ])
            
            # 写入数据
            for entry in entries:
                writer.writerow([
                    entry.timestamp.isoformat(),
                    entry.level,
                    entry.logger_name,
                    entry.message,
                    entry.request_id or '',
                    entry.user_id or '',
                    entry.endpoint or '',
                    entry.method or '',
                    entry.status_code or '',
                    entry.process_time or '',
                    entry.source_file or '',
                    entry.line_number or ''
                ])


# 创建全局日志服务实例
log_service = LogService()