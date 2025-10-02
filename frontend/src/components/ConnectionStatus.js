/**
 * 连接状态显示组件
 * 显示网络连接和API服务器状态
 */
import { networkDetector } from '../utils/NetworkDetector.js';

export class ConnectionStatus {
  constructor(options = {}) {
    this.options = {
      showDetails: false,
      autoHide: true,
      hideDelay: 3000,
      ...options
    };

    this.container = null;
    this.isVisible = false;
    this.checkInterval = null;
  }

  /**
   * 渲染连接状态组件
   * @returns {HTMLElement} 组件DOM元素
   */
  render() {
    this.container = document.createElement('div');
    this.container.className = 'connection-status';
    this.container.innerHTML = this.getTemplate();

    this.bindEvents();
    this.startStatusCheck();

    return this.container;
  }

  /**
   * 获取组件模板
   * @returns {string} HTML模板
   */
  getTemplate() {
    return `
      <div class="connection-indicator" id="connection-indicator">
        <div class="status-icon">
          <div class="loading-spinner"></div>
        </div>
        <div class="status-text">检测连接中...</div>
      </div>
      
      <div class="connection-details" id="connection-details" style="display: none;">
        <div class="detail-item">
          <span class="label">网络状态:</span>
          <span class="value" id="network-status">检测中</span>
        </div>
        <div class="detail-item">
          <span class="label">API服务器:</span>
          <span class="value" id="api-server">检测中</span>
        </div>
        <div class="detail-item">
          <span class="label">连接延迟:</span>
          <span class="value" id="connection-latency">-</span>
        </div>
      </div>
      
      <style>
        .connection-status {
          position: fixed;
          top: 10px;
          right: 10px;
          background: rgba(255, 255, 255, 0.95);
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
          padding: 10px;
          z-index: 9999;
          font-size: 12px;
          max-width: 250px;
          transition: all 0.3s ease;
        }
        
        .connection-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }
        
        .status-icon {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .status-icon.online {
          background: #10b981;
        }
        
        .status-icon.offline {
          background: #ef4444;
        }
        
        .status-icon.checking {
          background: #f59e0b;
        }
        
        .loading-spinner {
          width: 8px;
          height: 8px;
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-top: 1px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .status-text {
          font-weight: 500;
          color: #374151;
        }
        
        .connection-details {
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #e5e7eb;
        }
        
        .detail-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        
        .detail-item .label {
          color: #6b7280;
        }
        
        .detail-item .value {
          font-weight: 500;
          color: #374151;
        }
        
        .connection-status.hidden {
          opacity: 0;
          transform: translateX(100%);
          pointer-events: none;
        }
      </style>
    `;
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    const indicator = this.container.querySelector('#connection-indicator');
    const details = this.container.querySelector('#connection-details');

    indicator.addEventListener('click', () => {
      const isVisible = details.style.display !== 'none';
      details.style.display = isVisible ? 'none' : 'block';
    });
  }

  /**
   * 开始状态检查
   */
  startStatusCheck() {
    this.checkStatus();

    // 每30秒检查一次
    this.checkInterval = setInterval(() => {
      this.checkStatus();
    }, 30000);
  }

  /**
   * 停止状态检查
   */
  stopStatusCheck() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  /**
   * 检查连接状态
   */
  async checkStatus() {
    const startTime = Date.now();

    try {
      // 检测API服务器
      const apiUrl = await networkDetector.detectApiServer();
      const isConnected = await networkDetector.testConnection(apiUrl);
      const latency = Date.now() - startTime;

      this.updateStatus({
        online: navigator.onLine && isConnected,
        apiServer: apiUrl,
        latency: latency,
        networkOnline: navigator.onLine
      });

      // 如果设置了自动隐藏，在连接正常时隐藏组件
      if (this.options.autoHide && navigator.onLine && isConnected) {
        setTimeout(() => {
          this.hide();
        }, this.options.hideDelay);
      }

    } catch (error) {
      console.error('连接状态检查失败:', error);
      this.updateStatus({
        online: false,
        apiServer: '连接失败',
        latency: -1,
        networkOnline: navigator.onLine
      });
    }
  }

  /**
   * 更新状态显示
   * @param {Object} status - 状态信息
   */
  updateStatus(status) {
    const statusIcon = this.container.querySelector('.status-icon');
    const statusText = this.container.querySelector('.status-text');
    const networkStatus = this.container.querySelector('#network-status');
    const apiServer = this.container.querySelector('#api-server');
    const latency = this.container.querySelector('#connection-latency');

    // 更新图标和文本
    statusIcon.className = 'status-icon';
    if (status.online) {
      statusIcon.classList.add('online');
      statusText.textContent = '连接正常';
    } else {
      statusIcon.classList.add('offline');
      statusText.textContent = '连接异常';
    }

    // 更新详细信息
    networkStatus.textContent = status.networkOnline ? '在线' : '离线';
    apiServer.textContent = status.apiServer;
    latency.textContent = status.latency > 0 ? `${status.latency}ms` : '-';

    // 如果连接异常，自动显示详细信息
    if (!status.online) {
      this.show();
      const details = this.container.querySelector('#connection-details');
      details.style.display = 'block';
    }
  }

  /**
   * 显示组件
   */
  show() {
    if (this.container) {
      this.container.classList.remove('hidden');
      this.isVisible = true;
    }
  }

  /**
   * 隐藏组件
   */
  hide() {
    if (this.container) {
      this.container.classList.add('hidden');
      this.isVisible = false;
    }
  }

  /**
   * 销毁组件
   */
  destroy() {
    this.stopStatusCheck();
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
  }
}

// 创建全局实例
export const connectionStatus = new ConnectionStatus({
  showDetails: true,
  autoHide: true,
  hideDelay: 5000
});