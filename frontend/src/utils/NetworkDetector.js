/**
 * 网络检测工具
 * 自动检测API服务器地址并配置连接
 */
export class NetworkDetector {
  constructor() {
    // 动态获取可能的主机地址
    const currentHost = window.location.hostname;
    this.possibleHosts = [
      '192.168.43.249:8000', // 从日志中看到的有效IP
      `${currentHost}:8000`, // 当前页面的hostname
      'localhost:8000',
      '127.0.0.1:8000'
    ];

    // 如果当前不是localhost，添加更多局域网IP
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
      // 根据当前IP推测可能的服务器IP
      const ipParts = currentHost.split('.');
      if (ipParts.length === 4) {
        // 尝试同网段的常见服务器IP
        const baseIP = `${ipParts[0]}.${ipParts[1]}.${ipParts[2]}`;
        this.possibleHosts.unshift(
          `${baseIP}.1:8000`,    // 网关
          `${baseIP}.100:8000`,  // 常见服务器IP
          `${baseIP}.200:8000`,  // 另一个常见IP
          `${baseIP}.249:8000`   // 从日志看到的IP模式
        );
      }
    }
    this.detectedHost = null;
  }

  /**
   * 检测可用的API服务器
   * @returns {Promise<string>} 可用的API基础URL
   */
  async detectApiServer() {
    if (this.detectedHost) {
      return this.detectedHost;
    }

    console.log('🔍 开始检测API服务器...');

    for (const host of this.possibleHosts) {
      const url = `http://${host}`;

      try {
        console.log(`🌐 尝试连接: ${url}`);

        // 尝试连接健康检查端点
        const response = await fetch(`${url}/health`, {
          method: 'GET',
          timeout: 3000,
          signal: AbortSignal.timeout(3000)
        });

        if (response.ok) {
          console.log(`✅ 连接成功: ${url}`);
          this.detectedHost = url;

          // 保存到localStorage供下次使用
          localStorage.setItem('detected_api_host', url);

          return url;
        }
      } catch (error) {
        console.log(`❌ 连接失败: ${url} - ${error.message}`);
      }
    }

    // 如果都失败了，尝试从localStorage获取上次成功的地址
    const savedHost = localStorage.getItem('detected_api_host');
    if (savedHost) {
      console.log(`📱 使用保存的地址: ${savedHost}`);
      this.detectedHost = savedHost;
      return savedHost;
    }

    // 最后使用默认地址
    const defaultHost = `http://${window.location.hostname}:8000`;
    console.log(`🔄 使用默认地址: ${defaultHost}`);
    this.detectedHost = defaultHost;
    return defaultHost;
  }

  /**
   * 测试API连接
   * @param {string} baseUrl - API基础URL
   * @returns {Promise<boolean>} 连接是否成功
   */
  async testConnection(baseUrl) {
    try {
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        timeout: 5000,
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * 获取网络状态信息
   * @returns {Object} 网络状态信息
   */
  getNetworkInfo() {
    return {
      online: navigator.onLine,
      hostname: window.location.hostname,
      port: window.location.port,
      protocol: window.location.protocol,
      detectedHost: this.detectedHost
    };
  }

  /**
   * 显示网络连接状态
   */
  showConnectionStatus() {
    const info = this.getNetworkInfo();
    console.log('🌐 网络连接状态:', info);

    if (!info.online) {
      console.warn('⚠️ 设备离线');
    }

    if (info.detectedHost) {
      console.log(`✅ API服务器: ${info.detectedHost}`);
    } else {
      console.warn('⚠️ 未检测到API服务器');
    }
  }
}

// 创建全局实例
export const networkDetector = new NetworkDetector();

// 在页面加载时自动检测
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    networkDetector.detectApiServer().then(host => {
      console.log(`🎯 API服务器已配置: ${host}`);

      // 更新全局API配置
      if (window.API_CONFIG) {
        window.API_CONFIG.BASE_URL = host;
      }

      // 设置全局变量供其他模块使用
      window.API_BASE_URL = host;
    });
  });
}