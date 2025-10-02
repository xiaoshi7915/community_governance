"""
核心工具函数集合
"""
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException


class ValidationUtils:
    """数据验证工具类"""
    
    @staticmethod
    def is_valid_phone(phone: str, region: str = "CN") -> bool:
        """
        验证手机号是否有效
        
        Args:
            phone: 手机号
            region: 地区代码，默认中国
            
        Returns:
            bool: 是否有效
        """
        try:
            parsed_number = phonenumbers.parse(phone, region)
            return phonenumbers.is_valid_number(parsed_number)
        except NumberParseException:
            return False
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        验证邮箱是否有效
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, List[str]]:
        """
        检查密码强度
        
        Args:
            password: 密码
            
        Returns:
            tuple: (是否强密码, 错误信息列表)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("密码长度至少8位")
        
        if not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")
        
        if not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")
        
        if not re.search(r"\d", password):
            errors.append("密码必须包含数字")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("密码必须包含特殊字符")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除危险字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除路径分隔符和其他危险字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除控制字符
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        # 限制长度
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized or "unnamed_file"


class DateTimeUtils:
    """日期时间工具类"""
    
    @staticmethod
    def utc_now() -> datetime:
        """获取当前UTC时间"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def to_timestamp(dt: datetime) -> int:
        """将datetime转换为时间戳"""
        return int(dt.timestamp())
    
    @staticmethod
    def from_timestamp(timestamp: int) -> datetime:
        """从时间戳创建datetime"""
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """格式化日期时间"""
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """解析日期时间字符串"""
        return datetime.strptime(date_str, format_str).replace(tzinfo=timezone.utc)


class StringUtils:
    """字符串工具类"""
    
    @staticmethod
    def generate_uuid() -> str:
        """生成UUID字符串"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """生成短ID"""
        return str(uuid.uuid4()).replace('-', '')[:length]
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """截断字符串"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """
        掩码敏感数据
        
        Args:
            data: 原始数据
            mask_char: 掩码字符
            visible_chars: 可见字符数（前后各显示的字符数）
            
        Returns:
            str: 掩码后的数据
        """
        if len(data) <= visible_chars * 2:
            return mask_char * len(data)
        
        visible_start = data[:visible_chars]
        visible_end = data[-visible_chars:]
        mask_length = len(data) - visible_chars * 2
        
        return visible_start + mask_char * mask_length + visible_end


class DictUtils:
    """字典工具类"""
    
    @staticmethod
    def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并字典
        
        Args:
            dict1: 第一个字典
            dict2: 第二个字典
            
        Returns:
            Dict[str, Any]: 合并后的字典
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DictUtils.deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤掉值为None的键值对"""
        return {k: v for k, v in data.items() if v is not None}
    
    @staticmethod
    def flatten_dict(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """
        扁平化嵌套字典
        
        Args:
            data: 嵌套字典
            separator: 键分隔符
            
        Returns:
            Dict[str, Any]: 扁平化后的字典
        """
        def _flatten(obj: Any, parent_key: str = "") -> Dict[str, Any]:
            items = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{separator}{key}" if parent_key else key
                    items.extend(_flatten(value, new_key).items())
            else:
                return {parent_key: obj}
            
            return dict(items)
        
        return _flatten(data)


class ListUtils:
    """列表工具类"""
    
    @staticmethod
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """
        将列表分块
        
        Args:
            lst: 原始列表
            chunk_size: 块大小
            
        Returns:
            List[List[Any]]: 分块后的列表
        """
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def remove_duplicates(lst: List[Any], key_func: Optional[callable] = None) -> List[Any]:
        """
        移除列表中的重复项
        
        Args:
            lst: 原始列表
            key_func: 用于比较的键函数
            
        Returns:
            List[Any]: 去重后的列表
        """
        if key_func is None:
            return list(dict.fromkeys(lst))
        
        seen = set()
        result = []
        
        for item in lst:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result
    
    @staticmethod
    def safe_get(lst: List[Any], index: int, default: Any = None) -> Any:
        """
        安全获取列表元素
        
        Args:
            lst: 列表
            index: 索引
            default: 默认值
            
        Returns:
            Any: 列表元素或默认值
        """
        try:
            return lst[index]
        except (IndexError, TypeError):
            return default


# 创建工具类实例
validation_utils = ValidationUtils()
datetime_utils = DateTimeUtils()
string_utils = StringUtils()
dict_utils = DictUtils()
list_utils = ListUtils()