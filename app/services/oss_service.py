"""
阿里云OSS文件存储服务
提供文件上传、下载、删除等功能
"""
import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
import oss2
from oss2.exceptions import OssError, NoSuchKey, AccessDenied
from fastapi import UploadFile
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from app.core.config import settings
from app.core.exceptions import (
    FileUploadError,
    ValidationError,
    NotFoundError,
    ExternalServiceError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class OSSService:
    """阿里云OSS文件存储服务类"""
    
    def __init__(self):
        """初始化OSS客户端"""
        self._validate_config()
        
        # 创建OSS认证对象
        self.auth = oss2.Auth(
            settings.ALIYUN_OSS_ACCESS_KEY_ID,
            settings.ALIYUN_OSS_ACCESS_KEY_SECRET
        )
        
        # 创建OSS Bucket对象
        self.bucket = oss2.Bucket(
            self.auth,
            settings.ALIYUN_OSS_ENDPOINT,
            settings.ALIYUN_OSS_BUCKET_NAME
        )
        
        logger.info(f"OSS服务初始化成功，Bucket: {settings.ALIYUN_OSS_BUCKET_NAME}")
    
    def _validate_config(self) -> None:
        """验证OSS配置"""
        required_configs = [
            "ALIYUN_OSS_ACCESS_KEY_ID",
            "ALIYUN_OSS_ACCESS_KEY_SECRET", 
            "ALIYUN_OSS_BUCKET_NAME",
            "ALIYUN_OSS_ENDPOINT"
        ]
        
        for config in required_configs:
            if not getattr(settings, config):
                raise ValidationError(f"OSS配置缺失: {config}")
    
    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "uploads",
        user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        上传文件到OSS
        
        Args:
            file: 上传的文件对象
            folder: 存储文件夹
            user_id: 用户ID（可选，用于组织文件结构）
            
        Returns:
            Dict[str, str]: 包含文件信息的字典
            
        Raises:
            FileUploadError: 文件上传失败
            ValidationError: 文件验证失败
        """
        try:
            # 验证文件
            await self._validate_file(file)
            
            # 生成文件路径和名称
            file_key = self._generate_file_key(file.filename, folder, user_id)
            
            # 读取文件内容
            file_content = await file.read()
            
            # 上传文件到OSS
            result = self.bucket.put_object(file_key, file_content)
            
            # 生成文件URL
            file_url = self._generate_file_url(file_key)
            
            # 获取文件信息
            file_info = {
                "file_key": file_key,
                "file_url": file_url,
                "file_name": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type,
                "etag": result.etag,
                "upload_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"文件上传成功: {file_key}")
            return file_info
            
        except OssError as e:
            logger.error(f"OSS上传失败: {str(e)}")
            raise FileUploadError(f"文件上传失败: {str(e)}")
        except Exception as e:
            logger.error(f"文件上传异常: {str(e)}")
            raise FileUploadError(f"文件上传失败: {str(e)}")
    
    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        folder: str = "uploads",
        user_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        批量上传文件
        
        Args:
            files: 文件列表
            folder: 存储文件夹
            user_id: 用户ID
            
        Returns:
            List[Dict[str, str]]: 上传结果列表
        """
        results = []
        failed_files = []
        
        for file in files:
            try:
                result = await self.upload_file(file, folder, user_id)
                results.append(result)
            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
                logger.error(f"批量上传文件失败: {file.filename}, 错误: {str(e)}")
        
        if failed_files:
            logger.warning(f"批量上传部分失败，失败文件数: {len(failed_files)}")
        
        return results
    
    def generate_presigned_url(
        self,
        file_key: str,
        expires: int = 3600,
        method: str = "GET"
    ) -> str:
        """
        生成预签名URL
        
        Args:
            file_key: 文件键
            expires: 过期时间（秒）
            method: HTTP方法
            
        Returns:
            str: 预签名URL
            
        Raises:
            ExternalServiceError: OSS服务错误
        """
        try:
            url = self.bucket.sign_url(method, file_key, expires)
            logger.debug(f"生成预签名URL成功: {file_key}")
            return url
        except OssError as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            raise ExternalServiceError(f"生成文件访问URL失败: {str(e)}")
    
    def generate_upload_presigned_url(
        self,
        file_key: str,
        expires: int = 3600,
        content_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        生成上传预签名URL
        
        Args:
            file_key: 文件键
            expires: 过期时间（秒）
            content_type: 内容类型
            
        Returns:
            Dict[str, str]: 包含上传URL和相关信息
        """
        try:
            # 生成上传URL
            upload_url = self.bucket.sign_url("PUT", file_key, expires)
            
            # 构建响应
            result = {
                "upload_url": upload_url,
                "file_key": file_key,
                "expires_in": expires,
                "method": "PUT"
            }
            
            if content_type:
                result["content_type"] = content_type
            
            logger.debug(f"生成上传预签名URL成功: {file_key}")
            return result
            
        except OssError as e:
            logger.error(f"生成上传预签名URL失败: {str(e)}")
            raise ExternalServiceError(f"生成上传URL失败: {str(e)}")
    
    def delete_file(self, file_key: str) -> bool:
        """
        删除单个文件
        
        Args:
            file_key: 文件键
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            NotFoundError: 文件不存在
            ExternalServiceError: OSS服务错误
        """
        try:
            self.bucket.delete_object(file_key)
            logger.info(f"文件删除成功: {file_key}")
            return True
        except NoSuchKey:
            logger.warning(f"删除文件不存在: {file_key}")
            raise NotFoundError(f"文件不存在: {file_key}")
        except OssError as e:
            logger.error(f"删除文件失败: {str(e)}")
            raise ExternalServiceError(f"删除文件失败: {str(e)}")
    
    def delete_multiple_files(self, file_keys: List[str]) -> Dict[str, List[str]]:
        """
        批量删除文件
        
        Args:
            file_keys: 文件键列表
            
        Returns:
            Dict[str, List[str]]: 删除结果，包含成功和失败的文件列表
        """
        if not file_keys:
            return {"success": [], "failed": []}
        
        try:
            # OSS批量删除
            result = self.bucket.batch_delete_objects(file_keys)
            
            success_files = [obj.key for obj in result.deleted_objects]
            failed_files = []
            
            # 检查是否有删除失败的文件
            for file_key in file_keys:
                if file_key not in success_files:
                    failed_files.append(file_key)
            
            logger.info(f"批量删除完成，成功: {len(success_files)}, 失败: {len(failed_files)}")
            
            return {
                "success": success_files,
                "failed": failed_files
            }
            
        except OssError as e:
            logger.error(f"批量删除文件失败: {str(e)}")
            raise ExternalServiceError(f"批量删除文件失败: {str(e)}")
    
    def get_file_info(self, file_key: str) -> Dict[str, Union[str, int]]:
        """
        获取文件信息
        
        Args:
            file_key: 文件键
            
        Returns:
            Dict[str, Union[str, int]]: 文件信息
            
        Raises:
            NotFoundError: 文件不存在
            ExternalServiceError: OSS服务错误
        """
        try:
            # 获取文件元数据
            metadata = self.bucket.head_object(file_key)
            
            file_info = {
                "file_key": file_key,
                "file_size": metadata.content_length,
                "content_type": metadata.content_type,
                "etag": metadata.etag,
                "last_modified": metadata.last_modified.isoformat() if hasattr(metadata.last_modified, 'isoformat') else str(metadata.last_modified) if metadata.last_modified else None,
                "file_url": self._generate_file_url(file_key)
            }
            
            # 添加自定义元数据
            if hasattr(metadata, 'metadata') and metadata.metadata:
                file_info["custom_metadata"] = metadata.metadata
            
            logger.debug(f"获取文件信息成功: {file_key}")
            return file_info
            
        except NoSuchKey:
            logger.warning(f"获取文件信息失败，文件不存在: {file_key}")
            raise NotFoundError(f"文件不存在: {file_key}")
        except OssError as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            raise ExternalServiceError(f"获取文件信息失败: {str(e)}")
    
    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 100,
        marker: str = ""
    ) -> Dict[str, Union[List[Dict], str, bool]]:
        """
        列出文件
        
        Args:
            prefix: 文件前缀
            max_keys: 最大返回数量
            marker: 分页标记
            
        Returns:
            Dict: 文件列表和分页信息
        """
        try:
            result = self.bucket.list_objects(
                prefix=prefix,
                max_keys=max_keys,
                marker=marker
            )
            
            files = []
            for obj in result.object_list:
                files.append({
                    "file_key": obj.key,
                    "file_size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if hasattr(obj.last_modified, 'isoformat') else str(obj.last_modified) if obj.last_modified else None,
                    "etag": obj.etag,
                    "file_url": self._generate_file_url(obj.key)
                })
            
            return {
                "files": files,
                "next_marker": result.next_marker,
                "is_truncated": result.is_truncated,
                "prefix": prefix
            }
            
        except OssError as e:
            logger.error(f"列出文件失败: {str(e)}")
            raise ExternalServiceError(f"列出文件失败: {str(e)}")
    
    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """
        复制文件
        
        Args:
            source_key: 源文件键
            dest_key: 目标文件键
            
        Returns:
            bool: 是否复制成功
        """
        try:
            # 构建源文件路径
            source_bucket_name = settings.ALIYUN_OSS_BUCKET_NAME
            copy_source = f"{source_bucket_name}/{source_key}"
            
            self.bucket.copy_object(copy_source, dest_key)
            logger.info(f"文件复制成功: {source_key} -> {dest_key}")
            return True
            
        except NoSuchKey:
            logger.warning(f"复制文件失败，源文件不存在: {source_key}")
            raise NotFoundError(f"源文件不存在: {source_key}")
        except OssError as e:
            logger.error(f"复制文件失败: {str(e)}")
            raise ExternalServiceError(f"复制文件失败: {str(e)}")
    
    async def _validate_file(self, file: UploadFile) -> None:
        """
        验证上传文件
        
        Args:
            file: 上传文件对象
            
        Raises:
            ValidationError: 文件验证失败
        """
        # 检查文件名
        if not file.filename:
            raise ValidationError("文件名不能为空")
        
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置文件指针
        
        if file_size == 0:
            raise ValidationError("文件不能为空")
        
        if file_size > settings.MAX_FILE_SIZE:
            raise ValidationError(f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)")
        
        # 检查文件类型
        content_type = file.content_type
        if not content_type:
            # 尝试根据文件扩展名推断类型
            content_type, _ = mimetypes.guess_type(file.filename)
        
        if not content_type:
            raise ValidationError("无法确定文件类型")
        
        # 验证文件类型
        allowed_types = settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES
        if content_type not in allowed_types:
            raise ValidationError(f"不支持的文件类型: {content_type}")
        
        # 使用python-magic进行更准确的文件类型检测（如果可用）
        if MAGIC_AVAILABLE:
            try:
                file_content = await file.read()
                file.file.seek(0)  # 重置文件指针
                
                detected_type = magic.from_buffer(file_content[:1024], mime=True)
                if detected_type not in allowed_types:
                    raise ValidationError(f"文件内容与扩展名不匹配，检测到类型: {detected_type}")
            except Exception as e:
                logger.warning(f"文件类型检测失败: {str(e)}")
                # 如果检测失败，继续使用原始content_type
        else:
            logger.debug("python-magic不可用，跳过文件内容类型检测")
    
    def _generate_file_key(
        self,
        filename: str,
        folder: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        生成文件存储键
        
        Args:
            filename: 原始文件名
            folder: 文件夹
            user_id: 用户ID
            
        Returns:
            str: 文件存储键
        """
        # 生成唯一文件名
        file_ext = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # 构建文件路径
        date_path = datetime.now().strftime("%Y/%m/%d")
        
        if user_id:
            file_key = f"{folder}/{user_id}/{date_path}/{unique_filename}"
        else:
            file_key = f"{folder}/{date_path}/{unique_filename}"
        
        return file_key
    
    def _generate_file_url(self, file_key: str) -> str:
        """
        生成文件访问URL
        
        Args:
            file_key: 文件键
            
        Returns:
            str: 文件访问URL
        """
        # 生成公共访问URL
        return f"https://{settings.ALIYUN_OSS_BUCKET_NAME}.{settings.ALIYUN_OSS_ENDPOINT}/{file_key}"
    
    def cleanup_expired_files(self, days: int = 30) -> Dict[str, int]:
        """
        清理过期文件
        
        Args:
            days: 保留天数
            
        Returns:
            Dict[str, int]: 清理统计信息
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            total_count = 0
            
            # 列出所有文件
            marker = ""
            while True:
                result = self.bucket.list_objects(marker=marker, max_keys=1000)
                
                files_to_delete = []
                for obj in result.object_list:
                    total_count += 1
                    # 处理不同类型的last_modified
                    if obj.last_modified:
                        if hasattr(obj.last_modified, 'replace'):
                            # 如果是datetime对象
                            obj_date = obj.last_modified
                        else:
                            # 如果是时间戳，转换为datetime
                            from datetime import datetime
                            obj_date = datetime.fromtimestamp(obj.last_modified)
                        
                        if obj_date < cutoff_date:
                            files_to_delete.append(obj.key)
                
                # 批量删除过期文件
                if files_to_delete:
                    delete_result = self.delete_multiple_files(files_to_delete)
                    deleted_count += len(delete_result["success"])
                
                if not result.is_truncated:
                    break
                marker = result.next_marker
            
            logger.info(f"清理过期文件完成，总文件数: {total_count}, 删除数: {deleted_count}")
            
            return {
                "total_files": total_count,
                "deleted_files": deleted_count,
                "cutoff_days": days
            }
            
        except OssError as e:
            logger.error(f"清理过期文件失败: {str(e)}")
            raise ExternalServiceError(f"清理过期文件失败: {str(e)}")


# 创建全局OSS服务实例
oss_service = OSSService()