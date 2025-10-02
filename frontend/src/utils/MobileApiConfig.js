/**
 * 移动端API配置工具
 * 专门处理移动端的API连接问题
 */
export class MobileApiConfig {
  constructor() {
    this.isConfigured = false;
    this.apiBaseUrl = null;
  }

  /**
   * 配置移动端API地址
   */
  async configureMobileApi() {
    console.log('🔧 开始配置移动端API...');
    
    // 获取当前页面信息
    const currentHost = window.location.hostname;
    const currentPort = window.location.port;
    
    console.log(`📱 当前页面: ${currentHost}:${currentPort}`);
    
    // 移动端常见的API地址模式
    const mobileApiHosts = [
      // 如果当前是IP地址，直接使用
      currentHost !== 'localhost' && currentHost !== '127.0.0.1' ? `${currentHost}:8000` : null,
      // 常见的移动热点IP
      '192.168.43.249:8000',
      '192.168.43.1:8000',
      // 其他常见局域网IP
      '192.168.1.100:8000',
      '192.168.0.100:8000',
      '10.0.0.100:8000',
      // 本地地址作为备选
      'localhost:8000',
      '127.0.0.1:8000'
    ].filter(Boolean);

    console.log('🔍 移动端API地址候选:', mobileApiHosts);

    // 测试每个地址
    for (const host of mobileApiHosts) {
      const apiUrl = `http://${host}`;
      
      try {
        console.log(`📡 测试移动端API: ${apiUrl}`);
        
        // 使用更短的超时时间
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        
        const response = await fetch(`${apiUrl}/health`, {
          method: 'GET',
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          console.log(`✅ 移动端API连接成功: ${apiUrl}`);
          this.apiBaseUrl = apiUrl;
          this.isConfigured = true;
          
          // 保存配置
          localStorage.setItem('mobile_api_host', apiUrl);
          window.API_BASE_URL = apiUrl;
          
          return apiUrl;
        }
        
      } catch (error) {
        console.log(`❌ 移动端API连接失败: ${apiUrl} - ${error.message}`);
      }
    }
    
    // 如果所有地址都失败，尝试使用保存的地址
    const savedHost = localStorage.getItem('mobile_api_host');
    if (savedHost) {
      console.log(`💾 使用保存的移动端API地址: ${savedHost}`);
      this.apiBaseUrl = savedHost;
      window.API_BASE_URL = savedHost;
      return savedHost;
    }
    
    // 最后使用当前host作为默认值
    const fallbackUrl = `http://${currentHost}:8000`;
    console.log(`🔄 使用默认移动端API地址: ${fallbackUrl}`);
    this.apiBaseUrl = fallbackUrl;
    window.API_BASE_URL = fallbackUrl;
    
    return fallbackUrl;
  }

  /**
   * 测试登录连接
   */
  async testLogin(phone, password) {
    if (!this.apiBaseUrl) {
      await this.configureMobileApi();
    }

    console.log(`🔐 测试移动端登录: ${phone}`);
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ phone, password })
      });

      console.log(`📊 登录响应状态: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ 移动端登录成功');
        return { success: true, data };
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.log('❌ 移动端登录失败:', errorData);
        return { success: false, error: errorData.message || `HTTP ${response.status}` };
      }
      
    } catch (error) {
      console.log('❌ 移动端登录请求失败:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * 显示移动端配置信息
   */
  showMobileConfig() {
    const info = {
      configured: this.isConfigured,
      apiBaseUrl: this.apiBaseUrl,
      currentHost: window.location.hostname,
      currentPort: window.location.port,
      userAgent: navigator.userAgent,
      online: navigator.onLine
    };
    
    console.log('📱 移动端配置信息:', info);
    return info;
  }

  /**
   * 手动设置API地址
   */
  setManualApiUrl(url) {
    console.log(`🔧 手动设置移动端API地址: ${url}`);
    this.apiBaseUrl = url;
    this.isConfigured = true;
    localStorage.setItem('mobile_api_host', url);
    window.API_BASE_URL = url;
  }
}

// 创建全局实例
export const mobileApiConfig = new MobileApiConfig();

// 在移动设备上自动配置
if (typeof window !== 'undefined' && /Mobi|Android/i.test(navigator.userAgent)) {
  console.log('📱 检测到移动设备，自动配置API...');
  mobileApiConfig.configureMobileApi();
}