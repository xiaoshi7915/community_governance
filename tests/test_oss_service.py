"""
OSS服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
from fastapi import UploadFile
import oss2

from app.services.oss_service import OSSService
from app.core.exceptions import ValidationError, FileUploadError, NotFoundError


class TestOSSService:
    """OSS服务测试类"""
    
    @pytest.fixture
    def oss_service(self):
        """创建OSS服务实例"""
        with patch('app.services.oss_service.oss2'):
            service = OSSService()
            return service
    
    @pytest.fixture
    def mock_upload_file(self):
        """创建模拟上传文件"""
        content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        file = UploadFile(
            filename="test.png",
            file=BytesIO(content),
            size=len(content),
            headers={"content-type": "image/png"}
        )
        return file
    
    @pytest.mark.asyncio
    async def test_validate_file_success(self, oss_service, mock_upload_file):
        """测试文件验证成功"""
        # 不应该抛出异常
        await oss_service._validate_file(mock_upload_file)
    
    @pytest.mark.asyncio
    async def test_validate_file_empty_filename(self, oss_service):
        """测试空文件名验证失败"""
        file = UploadFile(filename="", file=BytesIO(b"test"))
        
        with pytest.raises(ValidationError, match="文件名不能为空"):
            await oss_service._validate_file(file)
    
    @pytest.mark.asyncio
    async def test_validate_file_empty_content(self, oss_service):
        """测试空文件内容验证失败"""
        file = UploadFile(filename="test.png", file=BytesIO(b""))
        
        with pytest.raises(ValidationError, match="文件不能为空"):
            await oss_service._validate_file(file)
    
    @pytest.mark.asyncio
    async def test_validate_file_unsupported_type(self, oss_service):
        """测试不支持的文件类型验证失败"""
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"test content"),
            headers={"content-type": "text/plain"}
        )
        
        with pytest.raises(ValidationError, match="不支持的文件类型"):
            await oss_service._validate_file(file)
    
    def test_generate_file_key(self, oss_service):
        """测试文件键生成"""
        file_key = oss_service._generate_file_key(
            filename="test.png",
            folder="uploads",
            user_id="user123"
        )
        
        # 检查文件键格式
        assert file_key.startswith("uploads/user123/")
        assert file_key.endswith(".png")
        assert len(file_key.split("/")) == 6  # uploads/user123/2025/09/30/filename.png
    
    def test_generate_file_key_without_user(self, oss_service):
        """测试无用户ID的文件键生成"""
        file_key = oss_service._generate_file_key(
            filename="test.png",
            folder="uploads"
        )
        
        # 检查文件键格式
        assert file_key.startswith("uploads/")
        assert file_key.endswith(".png")
        assert len(file_key.split("/")) == 5  # uploads/2025/09/30/filename.png
    
    def test_generate_file_url(self, oss_service):
        """测试文件URL生成"""
        file_key = "uploads/user123/test.png"
        file_url = oss_service._generate_file_url(file_key)
        
        # 使用实际配置值进行测试
        from app.core.config import settings
        expected_url = f"https://{settings.ALIYUN_OSS_BUCKET_NAME}.{settings.ALIYUN_OSS_ENDPOINT}/{file_key}"
        assert file_url == expected_url
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, oss_service, mock_upload_file):
        """测试文件上传成功"""
        # Mock OSS bucket put_object方法
        mock_result = Mock()
        mock_result.etag = "test-etag"
        oss_service.bucket.put_object = Mock(return_value=mock_result)
        
        result = await oss_service.upload_file(mock_upload_file, "test", "user123")
        
        # 验证返回结果
        assert "file_key" in result
        assert "file_url" in result
        assert "file_name" in result
        assert result["file_name"] == "test.png"
        assert result["etag"] == "test-etag"
        
        # 验证调用了put_object
        oss_service.bucket.put_object.assert_called_once()
    
    def test_generate_presigned_url_success(self, oss_service):
        """测试生成预签名URL成功"""
        # Mock OSS bucket sign_url方法
        expected_url = "https://example.com/presigned-url"
        oss_service.bucket.sign_url = Mock(return_value=expected_url)
        
        result = oss_service.generate_presigned_url("test/file.png", 3600)
        
        assert result == expected_url
        oss_service.bucket.sign_url.assert_called_once_with("GET", "test/file.png", 3600)
    
    def test_delete_file_success(self, oss_service):
        """测试删除文件成功"""
        # Mock OSS bucket delete_object方法
        oss_service.bucket.delete_object = Mock()
        
        result = oss_service.delete_file("test/file.png")
        
        assert result is True
        oss_service.bucket.delete_object.assert_called_once_with("test/file.png")
    
    def test_get_file_info_success(self, oss_service):
        """测试获取文件信息成功"""
        # Mock OSS bucket head_object方法
        mock_metadata = Mock()
        mock_metadata.content_length = 1024
        mock_metadata.content_type = "image/png"
        mock_metadata.etag = "test-etag"
        mock_metadata.last_modified = "2025-09-30T10:00:00Z"
        oss_service.bucket.head_object = Mock(return_value=mock_metadata)
        
        result = oss_service.get_file_info("test/file.png")
        
        assert result["file_key"] == "test/file.png"
        assert result["file_size"] == 1024
        assert result["content_type"] == "image/png"
        assert result["etag"] == "test-etag"
        
        oss_service.bucket.head_object.assert_called_once_with("test/file.png")
    
    def test_list_files_success(self, oss_service):
        """测试列出文件成功"""
        # Mock OSS bucket list_objects方法
        mock_obj = Mock()
        mock_obj.key = "test/file.png"
        mock_obj.size = 1024
        mock_obj.last_modified = "2025-09-30T10:00:00Z"
        mock_obj.etag = "test-etag"
        
        mock_result = Mock()
        mock_result.object_list = [mock_obj]
        mock_result.next_marker = None
        mock_result.is_truncated = False
        
        oss_service.bucket.list_objects = Mock(return_value=mock_result)
        
        result = oss_service.list_files("test/", 10)
        
        assert len(result["files"]) == 1
        assert result["files"][0]["file_key"] == "test/file.png"
        assert result["files"][0]["file_size"] == 1024
        assert result["is_truncated"] is False
        
        oss_service.bucket.list_objects.assert_called_once()
    
    def test_delete_multiple_files_success(self, oss_service):
        """测试批量删除文件成功"""
        # Mock OSS batch_delete_objects方法
        mock_deleted_obj = Mock()
        mock_deleted_obj.key = "test/file1.png"
        
        mock_result = Mock()
        mock_result.deleted_objects = [mock_deleted_obj]
        
        oss_service.bucket.batch_delete_objects = Mock(return_value=mock_result)
        
        result = oss_service.delete_multiple_files(["test/file1.png", "test/file2.png"])
        
        assert len(result["success"]) == 1
        assert len(result["failed"]) == 1
        assert "test/file1.png" in result["success"]
        assert "test/file2.png" in result["failed"]
        
        oss_service.bucket.batch_delete_objects.assert_called_once()
    
    def test_copy_file_success(self, oss_service):
        """测试复制文件成功"""
        # Mock OSS bucket copy_object方法
        oss_service.bucket.copy_object = Mock()
        
        result = oss_service.copy_file("source/file.png", "dest/file.png")
        
        assert result is True
        oss_service.bucket.copy_object.assert_called_once()
    
    def test_delete_file_oss_error(self, oss_service):
        """测试删除文件时OSS错误"""
        # Mock OSS异常
        oss_service.bucket.delete_object = Mock(side_effect=oss2.exceptions.OssError("删除失败", ""))
        
        result = oss_service.delete_file("test/file.png")
        
        assert result is False
    
    def test_get_file_info_not_found(self, oss_service):
        """测试获取不存在文件的信息"""
        # Mock OSS NoSuchKey异常
        oss_service.bucket.head_object = Mock(side_effect=oss2.exceptions.NoSuchKey("文件不存在", ""))
        
        with pytest.raises(NotFoundError, match="文件不存在"):
            oss_service.get_file_info("test/nonexistent.png")
    
    @pytest.mark.asyncio
    async def test_upload_file_validation_error(self, oss_service):
        """测试上传文件验证错误"""
        # 创建无效文件
        invalid_file = UploadFile(filename="", file=BytesIO(b""))
        
        with pytest.raises(ValidationError):
            await oss_service.upload_file(invalid_file, "test")
    
    @pytest.mark.asyncio
    async def test_upload_file_oss_error(self, oss_service, mock_upload_file):
        """测试上传文件时OSS错误"""
        # Mock OSS异常
        oss_service.bucket.put_object = Mock(side_effect=oss2.exceptions.OssError("上传失败", ""))
        
        with pytest.raises(FileUploadError, match="文件上传失败"):
            await oss_service.upload_file(mock_upload_file, "test", "user123")
    
    def test_generate_presigned_url_error(self, oss_service):
        """测试生成预签名URL错误"""
        # Mock OSS异常
        oss_service.bucket.sign_url = Mock(side_effect=oss2.exceptions.OssError("签名失败", ""))
        
        with pytest.raises(FileUploadError, match="生成预签名URL失败"):
            oss_service.generate_presigned_url("test/file.png", 3600)
    
    def test_list_files_empty(self, oss_service):
        """测试列出空文件夹"""
        # Mock空结果
        mock_result = Mock()
        mock_result.object_list = []
        mock_result.next_marker = None
        mock_result.is_truncated = False
        
        oss_service.bucket.list_objects = Mock(return_value=mock_result)
        
        result = oss_service.list_files("empty/", 10)
        
        assert len(result["files"]) == 0
        assert result["is_truncated"] is False
    
    def test_delete_multiple_files_partial_success(self, oss_service):
        """测试批量删除文件部分成功"""
        # Mock部分成功的删除结果
        mock_deleted_obj1 = Mock()
        mock_deleted_obj1.key = "test/file1.png"
        
        mock_result = Mock()
        mock_result.deleted_objects = [mock_deleted_obj1]
        
        oss_service.bucket.batch_delete_objects = Mock(return_value=mock_result)
        
        result = oss_service.delete_multiple_files(["test/file1.png", "test/file2.png", "test/file3.png"])
        
        assert len(result["success"]) == 1
        assert len(result["failed"]) == 2
        assert "test/file1.png" in result["success"]
        assert "test/file2.png" in result["failed"]
        assert "test/file3.png" in result["failed"]
    
    def test_validate_file_size_limit(self, oss_service):
        """测试文件大小限制验证"""
        # 创建超大文件
        large_content = b"x" * (100 * 1024 * 1024 + 1)  # 超过100MB
        large_file = UploadFile(
            filename="large.jpg",
            file=BytesIO(large_content),
            size=len(large_content),
            headers={"content-type": "image/jpeg"}
        )
        
        with pytest.raises(ValidationError, match="文件大小超过限制"):
            oss_service._validate_file_size(large_file)
    
    def test_get_file_extension(self, oss_service):
        """测试获取文件扩展名"""
        assert oss_service._get_file_extension("test.jpg") == ".jpg"
        assert oss_service._get_file_extension("test.PNG") == ".png"
        assert oss_service._get_file_extension("test") == ""
        assert oss_service._get_file_extension("test.tar.gz") == ".gz"
    
    def test_is_image_file(self, oss_service):
        """测试判断是否为图片文件"""
        assert oss_service._is_image_file("test.jpg") is True
        assert oss_service._is_image_file("test.PNG") is True
        assert oss_service._is_image_file("test.gif") is True
        assert oss_service._is_image_file("test.mp4") is False
        assert oss_service._is_image_file("test.txt") is False
    
    def test_is_video_file(self, oss_service):
        """测试判断是否为视频文件"""
        assert oss_service._is_video_file("test.mp4") is True
        assert oss_service._is_video_file("test.AVI") is True
        assert oss_service._is_video_file("test.mov") is True
        assert oss_service._is_video_file("test.jpg") is False
        assert oss_service._is_video_file("test.txt") is False