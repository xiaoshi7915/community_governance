"""
阿里云短信服务
实现手机验证码发送和验证功能
"""
import json
import time
import hashlib
import hmac
import base64
import urllib.parse
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings
from app.core.logging import get_logger


class SMSService:
    """阿里云短信服务"""
    
    def __init__(self):
        # 阿里云短信服务配置
        self.access_key_id = "LTAI5tJpFaLSz5F6uQqPD9EN"
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET  # 需要在环境变量中配置
        self.endpoint = "dysmsapi.aliyuncs.com"
        self.sign_name = "速通互联验证码"
        self.template_codes = {
            "login": "100001",  # 登录/注册模板
            "reset_password": "100003",  # 重置密码模板
            "bind_phone": "100004",  # 绑定新手机号模板
        }
        self.logger = get_logger(__name__)
        
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成阿里云API签名"""
        # 按参数名排序
        sorted_params = sorted(params.items())
        
        # 构建查询字符串
        query_string = urllib.parse.urlencode(sorted_params)
        
        # 构建签名字符串
        string_to_sign = f"GET&{urllib.parse.quote('/', safe='')}&{urllib.parse.quote(query_string, safe='')}"
        
        # 使用HMAC-SHA1生成签名
        signature = hmac.new(
            f"{self.access_key_secret}&".encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Base64编码
        return base64.b64encode(signature).decode('utf-8')
    
    async def send_verification_code(
        self, 
        phone_number: str, 
        code_type: str = "login",
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送验证码
        
        Args:
            phone_number: 手机号码
            code_type: 验证码类型 (login, reset_password, bind_phone)
            code: 验证码，如果不提供则自动生成
            
        Returns:
            发送结果
        """
        try:
            # 生成6位数字验证码
            if not code:
                import random
                code = str(random.randint(100000, 999999))
            
            # 获取模板代码
            template_code = self.template_codes.get(code_type, self.template_codes["login"])
            
            # 构建请求参数
            params = {
                "Action": "SendSms",
                "Version": "2017-05-25",
                "RegionId": "cn-hangzhou",
                "PhoneNumbers": phone_number,
                "SignName": self.sign_name,
                "TemplateCode": template_code,
                "TemplateParam": json.dumps({
                    "code": code,
                    "min": "5"
                }),
                "AccessKeyId": self.access_key_id,
                "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "SignatureMethod": "HMAC-SHA1",
                "SignatureVersion": "1.0",
                "SignatureNonce": str(int(time.time() * 1000)),
                "Format": "JSON"
            }
            
            # 生成签名
            signature = self._generate_signature(params)
            params["Signature"] = signature
            
            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.endpoint}",
                    params=params,
                    timeout=10.0
                )
                
                result = response.json()
                
                if result.get("Code") == "OK":
                    self.logger.info(f"验证码发送成功: {phone_number}")
                    return {
                        "success": True,
                        "message": "验证码发送成功",
                        "code": code,  # 开发环境返回验证码，生产环境应删除
                        "biz_id": result.get("BizId")
                    }
                else:
                    self.logger.error(f"验证码发送失败: {result}")
                    return {
                        "success": False,
                        "message": result.get("Message", "验证码发送失败"),
                        "error_code": result.get("Code")
                    }
                    
        except Exception as e:
            self.logger.error(f"发送验证码异常: {str(e)}")
            return {
                "success": False,
                "message": f"发送验证码失败: {str(e)}"
            }
    
    async def verify_code(
        self, 
        phone_number: str, 
        code: str, 
        biz_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证验证码
        
        Args:
            phone_number: 手机号码
            code: 验证码
            biz_id: 业务ID（可选）
            
        Returns:
            验证结果
        """
        try:
            # 构建请求参数
            params = {
                "Action": "QuerySendDetails",
                "Version": "2017-05-25",
                "RegionId": "cn-hangzhou",
                "PhoneNumber": phone_number,
                "SendDate": time.strftime("%Y%m%d", time.gmtime()),
                "PageSize": "10",
                "CurrentPage": "1",
                "AccessKeyId": self.access_key_id,
                "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "SignatureMethod": "HMAC-SHA1",
                "SignatureVersion": "1.0",
                "SignatureNonce": str(int(time.time() * 1000)),
                "Format": "JSON"
            }
            
            if biz_id:
                params["BizId"] = biz_id
            
            # 生成签名
            signature = self._generate_signature(params)
            params["Signature"] = signature
            
            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.endpoint}",
                    params=params,
                    timeout=10.0
                )
                
                result = response.json()
                
                if result.get("Code") == "OK":
                    # 检查发送记录
                    send_details = result.get("SmsSendDetailDTOs", {}).get("SmsSendDetailDTO", [])
                    if send_details:
                        latest_detail = send_details[0] if isinstance(send_details, list) else send_details
                    if latest_detail.get("SendStatus") == 3:  # 发送成功
                        self.logger.info(f"验证码验证成功: {phone_number}")
                        return {
                            "success": True,
                            "message": "验证码验证成功"
                        }
                    
                    return {
                        "success": False,
                        "message": "验证码验证失败"
                    }
                else:
                    self.logger.error(f"验证码验证失败: {result}")
                    return {
                        "success": False,
                        "message": result.get("Message", "验证码验证失败"),
                        "error_code": result.get("Code")
                    }
                    
        except Exception as e:
            self.logger.error(f"验证验证码异常: {str(e)}")
            return {
                "success": False,
                "message": f"验证验证码失败: {str(e)}"
            }


# 创建全局实例
sms_service = SMSService()
