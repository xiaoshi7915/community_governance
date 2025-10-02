"""
文件相关的Pydantic模型
用于API请求和响应的数据验证
"""
from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_key: str = Field(..., description="文件存储键")
    file_url: str = Field(..., description="文件访问URL")
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件MIME类型")
    etag: str = Field(..., description="文件ETag")
    upload_time: str = Field(..., description="上传时间")


class MultipleFileUploadResponse(BaseModel):
    """批量文件上传响应模型"""
    success_files: List[FileUploadResponse] = Field(..., description="上传成功的文件列表")
    failed_files: List[Dict[str, str]] = Field(default=[], description="上传失败的文件列表")
    total_count: int = Field(..., description="总文件数")
    success_count: int = Field(..., description="成功上传数")
    failed_count: int = Field(..., description="失败上传数")


class PresignedUrlRequest(BaseModel):
    """预签名URL请求模型"""
    file_key: str = Field(..., description="文件存储键")
    expires: int = Field(default=3600, ge=60, le=86400, description="过期时间（秒）")
    method: str = Field(default="GET", description="HTTP方法")
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = ['GET', 'PUT', 'POST', 'DELETE']
        if v.upper() not in allowed_methods:
            raise ValueError(f'方法必须是以下之一: {", ".join(allowed_methods)}')
        return v.upper()


class PresignedUrlResponse(BaseModel):
    """预签名URL响应模型"""
    presigned_url: str = Field(..., description="预签名URL")
    file_key: str = Field(..., description="文件存储键")
    expires_in: int = Field(..., description="过期时间（秒）")
    method: str = Field(..., description="HTTP方法")


class UploadPresignedUrlRequest(BaseModel):
    """上传预签名URL请求模型"""
    file_name: str = Field(..., description="文件名")
    content_type: Optional[str] = Field(None, description="文件MIME类型")
    folder: str = Field(default="uploads", description="存储文件夹")
    expires: int = Field(default=3600, ge=60, le=86400, description="过期时间（秒）")


class UploadPresignedUrlResponse(BaseModel):
    """上传预签名URL响应模型"""
    upload_url: str = Field(..., description="上传URL")
    file_key: str = Field(..., description="文件存储键")
    expires_in: int = Field(..., description="过期时间（秒）")
    method: str = Field(..., description="HTTP方法")
    content_type: Optional[str] = Field(None, description="内容类型")


class FileInfoResponse(BaseModel):
    """文件信息响应模型"""
    file_key: str = Field(..., description="文件存储键")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件MIME类型")
    etag: str = Field(..., description="文件ETag")
    last_modified: Optional[str] = Field(None, description="最后修改时间")
    file_url: str = Field(..., description="文件访问URL")
    custom_metadata: Optional[Dict[str, str]] = Field(None, description="自定义元数据")


class FileListRequest(BaseModel):
    """文件列表请求模型"""
    prefix: str = Field(default="", description="文件前缀")
    max_keys: int = Field(default=100, ge=1, le=1000, description="最大返回数量")
    marker: str = Field(default="", description="分页标记")


class FileListResponse(BaseModel):
    """文件列表响应模型"""
    files: List[FileInfoResponse] = Field(..., description="文件列表")
    next_marker: Optional[str] = Field(None, description="下一页标记")
    is_truncated: bool = Field(..., description="是否还有更多文件")
    prefix: str = Field(..., description="查询前缀")


class FileDeleteRequest(BaseModel):
    """文件删除请求模型"""
    file_key: str = Field(..., description="文件存储键")


class MultipleFileDeleteRequest(BaseModel):
    """批量文件删除请求模型"""
    file_keys: List[str] = Field(..., min_items=1, max_items=1000, description="文件存储键列表")


class FileDeleteResponse(BaseModel):
    """文件删除响应模型"""
    success: bool = Field(..., description="是否删除成功")
    file_key: str = Field(..., description="文件存储键")
    message: str = Field(..., description="删除结果消息")


class MultipleFileDeleteResponse(BaseModel):
    """批量文件删除响应模型"""
    success_files: List[str] = Field(..., description="删除成功的文件列表")
    failed_files: List[str] = Field(..., description="删除失败的文件列表")
    total_count: int = Field(..., description="总文件数")
    success_count: int = Field(..., description="成功删除数")
    failed_count: int = Field(..., description="失败删除数")


class FileCopyRequest(BaseModel):
    """文件复制请求模型"""
    source_key: str = Field(..., description="源文件键")
    dest_key: str = Field(..., description="目标文件键")


class FileCopyResponse(BaseModel):
    """文件复制响应模型"""
    success: bool = Field(..., description="是否复制成功")
    source_key: str = Field(..., description="源文件键")
    dest_key: str = Field(..., description="目标文件键")
    message: str = Field(..., description="复制结果消息")


class FileCleanupRequest(BaseModel):
    """文件清理请求模型"""
    days: int = Field(default=30, ge=1, le=365, description="保留天数")


class FileCleanupResponse(BaseModel):
    """文件清理响应模型"""
    total_files: int = Field(..., description="总文件数")
    deleted_files: int = Field(..., description="删除文件数")
    cutoff_days: int = Field(..., description="保留天数")
    message: str = Field(..., description="清理结果消息")


class FileValidationError(BaseModel):
    """文件验证错误模型"""
    field: str = Field(..., description="错误字段")
    message: str = Field(..., description="错误消息")
    code: str = Field(..., description="错误代码")


class FileOperationResult(BaseModel):
    """文件操作结果模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    data: Optional[Union[Dict, List]] = Field(None, description="操作结果数据")
    errors: Optional[List[FileValidationError]] = Field(None, description="错误列表")