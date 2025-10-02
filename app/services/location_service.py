"""
地理位置服务
集成百度地图API进行地址解析和坐标转换
"""
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LocationInfo:
    """地理位置信息数据类"""
    latitude: float
    longitude: float
    address: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None
    formatted_address: Optional[str] = None
    confidence: float = 0.0


@dataclass
class GeocodingResult:
    """地理编码结果数据类"""
    success: bool
    location_info: Optional[LocationInfo] = None
    error_message: Optional[str] = None


class LocationService:
    """地理位置服务类"""
    
    def __init__(self):
        self.api_key = settings.AMAP_API_KEY
        self.base_url = "https://api.map.baidu.com"
        self.timeout = 10.0
        
        if not self.api_key:
            logger.warning("百度地图API密钥未配置，地理位置服务可能无法正常工作")
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> GeocodingResult:
        """
        逆地理编码：将GPS坐标转换为详细地址
        
        Args:
            latitude: 纬度
            longitude: 经度
            
        Returns:
            GeocodingResult: 地理编码结果
        """
        if not self.api_key:
            return GeocodingResult(
                success=False,
                error_message="百度地图API密钥未配置"
            )
        
        try:
            # 百度地图逆地理编码API
            url = f"{self.base_url}/reverse_geocoding/v3/"
            params = {
                "ak": self.api_key,
                "output": "json",
                "coordtype": "wgs84ll",  # GPS坐标系
                "location": f"{latitude},{longitude}",
                "extensions_poi": "0",  # 不返回POI信息
                "extensions_road": "true",  # 返回道路信息
                "extensions_town": "true"  # 返回乡镇信息
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") == 0:  # 成功
                result = data.get("result", {})
                addressComponent = result.get("addressComponent", {})
                
                location_info = LocationInfo(
                    latitude=latitude,
                    longitude=longitude,
                    address=result.get("formatted_address", ""),
                    province=addressComponent.get("province", ""),
                    city=addressComponent.get("city", ""),
                    district=addressComponent.get("district", ""),
                    street=addressComponent.get("street", ""),
                    street_number=addressComponent.get("street_number", ""),
                    formatted_address=result.get("formatted_address", ""),
                    confidence=result.get("confidence", 0) / 100.0  # 转换为0-1范围
                )
                
                logger.info(f"逆地理编码成功: ({latitude}, {longitude}) -> {location_info.formatted_address}")
                
                return GeocodingResult(
                    success=True,
                    location_info=location_info
                )
            else:
                error_msg = f"百度地图API错误: {data.get('message', '未知错误')}"
                logger.error(error_msg)
                return GeocodingResult(
                    success=False,
                    error_message=error_msg
                )
                
        except httpx.TimeoutException:
            error_msg = "百度地图API请求超时"
            logger.error(error_msg)
            return GeocodingResult(
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"逆地理编码失败: {str(e)}"
            logger.error(error_msg)
            return GeocodingResult(
                success=False,
                error_message=error_msg
            )
    
    async def geocode(self, address: str) -> GeocodingResult:
        """
        地理编码：将地址转换为GPS坐标
        
        Args:
            address: 地址字符串
            
        Returns:
            GeocodingResult: 地理编码结果
        """
        if not self.api_key:
            return GeocodingResult(
                success=False,
                error_message="百度地图API密钥未配置"
            )
        
        if not address or not address.strip():
            return GeocodingResult(
                success=False,
                error_message="地址不能为空"
            )
        
        try:
            # 百度地图地理编码API
            url = f"{self.base_url}/geocoding/v3/"
            params = {
                "ak": self.api_key,
                "output": "json",
                "address": address.strip(),
                "city": ""  # 全国范围搜索
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") == 0:  # 成功
                result = data.get("result", {})
                location = result.get("location", {})
                
                if not location:
                    return GeocodingResult(
                        success=False,
                        error_message="未找到匹配的地址"
                    )
                
                latitude = location.get("lat")
                longitude = location.get("lng")
                
                if latitude is None or longitude is None:
                    return GeocodingResult(
                        success=False,
                        error_message="坐标信息不完整"
                    )
                
                location_info = LocationInfo(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    address=address,
                    formatted_address=address,
                    confidence=result.get("confidence", 0) / 100.0  # 转换为0-1范围
                )
                
                logger.info(f"地理编码成功: {address} -> ({latitude}, {longitude})")
                
                return GeocodingResult(
                    success=True,
                    location_info=location_info
                )
            else:
                error_msg = f"百度地图API错误: {data.get('message', '未知错误')}"
                logger.error(error_msg)
                return GeocodingResult(
                    success=False,
                    error_message=error_msg
                )
                
        except httpx.TimeoutException:
            error_msg = "百度地图API请求超时"
            logger.error(error_msg)
            return GeocodingResult(
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"地理编码失败: {str(e)}"
            logger.error(error_msg)
            return GeocodingResult(
                success=False,
                error_message=error_msg
            )
    
    async def validate_address(self, address: str) -> Dict[str, Any]:
        """
        验证地址有效性
        
        Args:
            address: 地址字符串
            
        Returns:
            Dict: 验证结果，包含is_valid, confidence, suggestions等字段
        """
        if not address or not address.strip():
            return {
                "is_valid": False,
                "confidence": 0.0,
                "error": "地址不能为空",
                "suggestions": []
            }
        
        # 先尝试地理编码
        geocode_result = await self.geocode(address)
        
        if not geocode_result.success:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "error": geocode_result.error_message,
                "suggestions": []
            }
        
        location_info = geocode_result.location_info
        
        # 再进行逆地理编码验证
        reverse_result = await self.reverse_geocode(
            location_info.latitude, 
            location_info.longitude
        )
        
        if reverse_result.success:
            reverse_location = reverse_result.location_info
            # 计算地址相似度（简单的字符串匹配）
            similarity = self._calculate_address_similarity(
                address, 
                reverse_location.formatted_address
            )
            
            is_valid = similarity > 0.6  # 相似度阈值
            
            return {
                "is_valid": is_valid,
                "confidence": min(location_info.confidence, reverse_location.confidence),
                "original_address": address,
                "formatted_address": reverse_location.formatted_address,
                "coordinates": {
                    "latitude": location_info.latitude,
                    "longitude": location_info.longitude
                },
                "similarity": similarity,
                "suggestions": [reverse_location.formatted_address] if not is_valid else []
            }
        else:
            return {
                "is_valid": True,  # 地理编码成功就认为有效
                "confidence": location_info.confidence,
                "original_address": address,
                "formatted_address": address,
                "coordinates": {
                    "latitude": location_info.latitude,
                    "longitude": location_info.longitude
                },
                "suggestions": []
            }
    
    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """
        计算两个地址的相似度
        
        Args:
            addr1: 地址1
            addr2: 地址2
            
        Returns:
            float: 相似度 (0-1)
        """
        if not addr1 or not addr2:
            return 0.0
        
        # 简单的字符串相似度计算
        addr1 = addr1.strip().lower()
        addr2 = addr2.strip().lower()
        
        if addr1 == addr2:
            return 1.0
        
        # 计算最长公共子序列长度
        def lcs_length(s1: str, s2: str) -> int:
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(addr1, addr2)
        max_len = max(len(addr1), len(addr2))
        
        return lcs_len / max_len if max_len > 0 else 0.0
    
    async def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        计算两点间的距离（米）
        使用Haversine公式
        
        Args:
            lat1, lng1: 第一个点的纬度和经度
            lat2, lng2: 第二个点的纬度和经度
            
        Returns:
            float: 距离（米）
        """
        import math
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine公式
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半径（米）
        earth_radius = 6371000
        
        return earth_radius * c
    
    async def find_nearby_coordinates(
        self, 
        center_lat: float, 
        center_lng: float, 
        radius_meters: float
    ) -> Dict[str, float]:
        """
        计算指定半径范围内的边界坐标
        
        Args:
            center_lat: 中心点纬度
            center_lng: 中心点经度
            radius_meters: 半径（米）
            
        Returns:
            Dict: 包含min_lat, max_lat, min_lng, max_lng的边界坐标
        """
        import math
        
        # 地球半径（米）
        earth_radius = 6371000
        
        # 纬度变化
        lat_change = radius_meters / earth_radius * (180 / math.pi)
        
        # 经度变化（考虑纬度影响）
        lng_change = radius_meters / (earth_radius * math.cos(math.radians(center_lat))) * (180 / math.pi)
        
        return {
            "min_lat": center_lat - lat_change,
            "max_lat": center_lat + lat_change,
            "min_lng": center_lng - lng_change,
            "max_lng": center_lng + lng_change
        }


# 创建全局服务实例
location_service = LocationService()