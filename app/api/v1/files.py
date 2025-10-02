"""
文件管理API端点
提供文件上传、下载、删除等功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPBearer

from app.services.oss_service import oss_service
from app.schemas.file import (
    FileUploadResponse,
    MultipleFileUploadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
    UploadPresignedUrlRequest,
    UploadPresignedUrlResponse,
    FileInfoResponse,
    FileListRequest,
    FileListResponse,
    FileDeleteRequest,
    MultipleFileDeleteRequest,
    FileDeleteResponse,
    MultipleFileDeleteResponse,
    FileCopyRequest,
    FileCopyResponse,
    FileCleanupRequest,
    FileCleanupResponse
)
from app.core.response import response_formatter
from app.core.auth_middleware import get_current_user
from app.core.permissions import require_permission, Permission
from app.core.exceptions import (
    FileUploadError,
    ValidationError,
    NotFoundError,
    ExternalServiceError
)
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form(default="uploads"),
    current_user: User = Depends(require_permission(Permission.UPLOAD_FILE))
):
    """
    上传单个文件
    
    Args:
        file: 上传的文件
        folder: 存储文件夹
        current_user: 当前用户
        
    Returns:
        FileUploadResponse: 上传结果
    """
    try:
        logger.info(f"用户 {current_user.id} 开始上传文件: {file.filename}")
        
        result = await oss_service.upload_file(
            file=file,
            folder=folder,
            user_id=str(current_user.id)
        )
        
        logger.info(f"文件上传成功: {result['file_key']}")
        # 直接返回FileUploadResponse格式
        return FileUploadResponse(**result)
        
    except ValidationError as e:
        logger.warning(f"文件上传验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileUploadError as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload-multiple", response_model=MultipleFileUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    folder: str = Form(default="uploads"),
    current_user: User = Depends(get_current_user)
):
    """
    批量上传文件
    
    Args:
        files: 上传的文件列表
        folder: 存储文件夹
        current_user: 当前用户
        
    Returns:
        MultipleFileUploadResponse: 批量上传结果
    """
    try:
        logger.info(f"用户 {current_user.id} 开始批量上传 {len(files)} 个文件")
        
        if len(files) > 10:  # 限制批量上传数量
            raise ValidationError("批量上传文件数量不能超过10个")
        
        results = await oss_service.upload_multiple_files(
            files=files,
            folder=folder,
            user_id=str(current_user.id)
        )
        
        success_files = [FileUploadResponse(**result) for result in results]
        failed_files = []  # OSS服务已处理失败情况
        
        response_data = MultipleFileUploadResponse(
            success_files=success_files,
            failed_files=failed_files,
            total_count=len(files),
            success_count=len(success_files),
            failed_count=len(failed_files)
        )
        
        logger.info(f"批量上传完成，成功: {len(success_files)}, 失败: {len(failed_files)}")
        return response_formatter.success(
            data=response_data,
            message=f"批量上传完成，成功: {len(success_files)}, 失败: {len(failed_files)}"
        )
        
    except ValidationError as e:
        logger.warning(f"批量文件上传验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileUploadError as e:
        logger.error(f"批量文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def generate_presigned_url(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成文件预签名URL
    
    Args:
        request: 预签名URL请求
        current_user: 当前用户
        
    Returns:
        PresignedUrlResponse: 预签名URL响应
    """
    try:
        logger.info(f"用户 {current_user.id} 请求生成预签名URL: {request.file_key}")
        
        presigned_url = oss_service.generate_presigned_url(
            file_key=request.file_key,
            expires=request.expires,
            method=request.method
        )
        
        response_data = PresignedUrlResponse(
            presigned_url=presigned_url,
            file_key=request.file_key,
            expires_in=request.expires,
            method=request.method
        )
        
        logger.info(f"预签名URL生成成功: {request.file_key}")
        return response_formatter.success(
            data=response_data,
            message="预签名URL生成成功"
        )
        
    except ExternalServiceError as e:
        logger.error(f"生成预签名URL失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.post("/upload-presigned-url", response_model=UploadPresignedUrlResponse)
async def generate_upload_presigned_url(
    request: UploadPresignedUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成上传预签名URL
    
    Args:
        request: 上传预签名URL请求
        current_user: 当前用户
        
    Returns:
        UploadPresignedUrlResponse: 上传预签名URL响应
    """
    try:
        logger.info(f"用户 {current_user.id} 请求生成上传预签名URL: {request.file_name}")
        
        # 生成文件键
        import os
        import uuid
        from datetime import datetime
        
        file_ext = os.path.splitext(request.file_name)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        date_path = datetime.now().strftime("%Y/%m/%d")
        file_key = f"{request.folder}/{current_user.id}/{date_path}/{unique_filename}"
        
        result = oss_service.generate_upload_presigned_url(
            file_key=file_key,
            expires=request.expires,
            content_type=request.content_type
        )
        
        response_data = UploadPresignedUrlResponse(**result)
        
        logger.info(f"上传预签名URL生成成功: {file_key}")
        return response_formatter.success(
            data=response_data,
            message="上传预签名URL生成成功"
        )
        
    except ExternalServiceError as e:
        logger.error(f"生成上传预签名URL失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.get("/{file_key:path}/url", response_model=PresignedUrlResponse)
async def get_file_url(
    file_key: str,
    expires: int = 3600,
    current_user: User = Depends(get_current_user)
):
    """
    生成文件访问URL
    
    Args:
        file_key: 文件存储键
        expires: 过期时间（秒）
        current_user: 当前用户
        
    Returns:
        PresignedUrlResponse: 文件访问URL
    """
    try:
        logger.info(f"用户 {current_user.id} 请求生成文件访问URL: {file_key}")
        
        # 检查用户权限（只能访问自己的文件）
        user_prefix = f"uploads/{current_user.id}/"
        if not file_key.startswith(user_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文件"
            )
        
        presigned_url = oss_service.generate_presigned_url(
            file_key=file_key,
            expires=expires,
            method="GET"
        )
        
        response_data = PresignedUrlResponse(
            presigned_url=presigned_url,
            file_key=file_key,
            expires_in=expires,
            method="GET"
        )
        
        logger.info(f"文件访问URL生成成功: {file_key}")
        return response_formatter.success(
            data=response_data,
            message="文件访问URL生成成功"
        )
        
    except NotFoundError as e:
        logger.warning(f"文件不存在: {file_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ExternalServiceError as e:
        logger.error(f"生成文件访问URL失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.get("/{file_key:path}/info", response_model=FileInfoResponse)
async def get_file_info(
    file_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取文件信息
    
    Args:
        file_key: 文件存储键
        current_user: 当前用户
        
    Returns:
        FileInfoResponse: 文件信息
    """
    try:
        logger.info(f"用户 {current_user.id} 请求获取文件信息: {file_key}")
        
        file_info = oss_service.get_file_info(file_key)
        response_data = FileInfoResponse(**file_info)
        
        logger.info(f"文件信息获取成功: {file_key}")
        return response_formatter.success(
            data=response_data,
            message="文件信息获取成功"
        )
        
    except NotFoundError as e:
        logger.warning(f"文件不存在: {file_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ExternalServiceError as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    prefix: str = "",
    max_keys: int = 100,
    marker: str = "",
    current_user: User = Depends(get_current_user)
):
    """
    列出文件
    
    Args:
        prefix: 文件前缀
        max_keys: 最大返回数量
        marker: 分页标记
        current_user: 当前用户
        
    Returns:
        FileListResponse: 文件列表
    """
    try:
        logger.info(f"用户 {current_user.id} 请求文件列表，前缀: {prefix}")
        
        # 限制用户只能查看自己的文件
        user_prefix = f"uploads/{current_user.id}/"
        if prefix and not prefix.startswith(user_prefix):
            prefix = f"{user_prefix}{prefix}"
        elif not prefix:
            prefix = user_prefix
        
        result = oss_service.list_files(
            prefix=prefix,
            max_keys=min(max_keys, 1000),  # 限制最大返回数量
            marker=marker
        )
        
        files = [FileInfoResponse(**file_info) for file_info in result["files"]]
        response_data = FileListResponse(
            files=files,
            next_marker=result["next_marker"],
            is_truncated=result["is_truncated"],
            prefix=result["prefix"]
        )
        
        logger.info(f"文件列表获取成功，返回 {len(files)} 个文件")
        return response_formatter.success(
            data=response_data,
            message=f"文件列表获取成功，共 {len(files)} 个文件"
        )
        
    except ExternalServiceError as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.delete("/{file_key:path}", response_model=FileDeleteResponse)
async def delete_file(
    file_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除单个文件
    
    Args:
        file_key: 文件存储键
        current_user: 当前用户
        
    Returns:
        FileDeleteResponse: 删除结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求删除文件: {file_key}")
        
        # 检查用户权限（只能删除自己的文件）
        user_prefix = f"uploads/{current_user.id}/"
        if not file_key.startswith(user_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限删除此文件"
            )
        
        success = oss_service.delete_file(file_key)
        
        response_data = FileDeleteResponse(
            success=success,
            file_key=file_key,
            message="文件删除成功"
        )
        
        logger.info(f"文件删除成功: {file_key}")
        return response_formatter.success(
            data=response_data,
            message="文件删除成功"
        )
        
    except NotFoundError as e:
        logger.warning(f"删除文件不存在: {file_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ExternalServiceError as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.post("/delete-multiple", response_model=MultipleFileDeleteResponse)
async def delete_multiple_files(
    request: MultipleFileDeleteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    批量删除文件
    
    Args:
        request: 批量删除请求
        current_user: 当前用户
        
    Returns:
        MultipleFileDeleteResponse: 批量删除结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求批量删除 {len(request.file_keys)} 个文件")
        
        # 检查用户权限（只能删除自己的文件）
        user_prefix = f"uploads/{current_user.id}/"
        unauthorized_files = [
            key for key in request.file_keys 
            if not key.startswith(user_prefix)
        ]
        
        if unauthorized_files:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限删除以下文件: {', '.join(unauthorized_files[:5])}"
            )
        
        result = oss_service.delete_multiple_files(request.file_keys)
        
        response_data = MultipleFileDeleteResponse(
            success_files=result["success"],
            failed_files=result["failed"],
            total_count=len(request.file_keys),
            success_count=len(result["success"]),
            failed_count=len(result["failed"])
        )
        
        logger.info(f"批量删除完成，成功: {len(result['success'])}, 失败: {len(result['failed'])}")
        return response_formatter.success(
            data=response_data,
            message=f"批量删除完成，成功: {len(result['success'])}, 失败: {len(result['failed'])}"
        )
        
    except ExternalServiceError as e:
        logger.error(f"批量删除文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.post("/copy", response_model=FileCopyResponse)
async def copy_file(
    request: FileCopyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    复制文件
    
    Args:
        request: 文件复制请求
        current_user: 当前用户
        
    Returns:
        FileCopyResponse: 复制结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求复制文件: {request.source_key} -> {request.dest_key}")
        
        # 检查用户权限（只能操作自己的文件）
        user_prefix = f"uploads/{current_user.id}/"
        if not request.source_key.startswith(user_prefix) or not request.dest_key.startswith(user_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限操作此文件"
            )
        
        success = oss_service.copy_file(request.source_key, request.dest_key)
        
        response_data = FileCopyResponse(
            success=success,
            source_key=request.source_key,
            dest_key=request.dest_key,
            message="文件复制成功"
        )
        
        logger.info(f"文件复制成功: {request.source_key} -> {request.dest_key}")
        return response_formatter.success(
            data=response_data,
            message="文件复制成功"
        )
        
    except NotFoundError as e:
        logger.warning(f"复制文件不存在: {request.source_key}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ExternalServiceError as e:
        logger.error(f"复制文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )


@router.post("/cleanup", response_model=FileCleanupResponse)
async def cleanup_expired_files(
    request: FileCleanupRequest,
    current_user: User = Depends(get_current_user)
):
    """
    清理过期文件（管理员功能）
    
    Args:
        request: 文件清理请求
        current_user: 当前用户
        
    Returns:
        FileCleanupResponse: 清理结果
    """
    try:
        # TODO: 添加管理员权限检查
        # if not current_user.is_admin:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="需要管理员权限"
        #     )
        
        logger.info(f"管理员 {current_user.id} 请求清理 {request.days} 天前的过期文件")
        
        result = oss_service.cleanup_expired_files(request.days)
        
        response_data = FileCleanupResponse(
            total_files=result["total_files"],
            deleted_files=result["deleted_files"],
            cutoff_days=result["cutoff_days"],
            message=f"清理完成，删除了 {result['deleted_files']} 个过期文件"
        )
        
        logger.info(f"文件清理完成，删除了 {result['deleted_files']} 个文件")
        return response_formatter.success(
            data=response_data,
            message=f"清理完成，删除了 {result['deleted_files']} 个过期文件"
        )
        
    except ExternalServiceError as e:
        logger.error(f"清理过期文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )