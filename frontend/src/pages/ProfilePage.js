/**
 * 个人设置页面组件
 * 实现用户个人信息展示、资料编辑、密码修改和应用设置功能
 */
import { Navigation } from '../components/Navigation.js';
import { Modal } from '../components/Modal.js';
import { Notification } from '../components/Notification.js';
import { AuthService } from '../services/AuthService.js';
import { EventService } from '../services/EventService.js';
import { FileService } from '../services/FileService.js';
import UserStore from '../stores/UserStore.js';
import ConfigStore from '../stores/ConfigStore.js';

// 导入样式
import '../styles/profile.css';

export class ProfilePage {
    constructor() {
        this.container = null;
        this.navigation = null;
        this.currentModal = null;
        this.userStats = null;
        this.tempAvatarUrl = null;
        this.isLoggingOut = false; // 防止重复退出登录

        // 服务实例
        this.authService = new AuthService();
        this.eventService = new EventService();
        this.fileService = new FileService();

        // 状态管理
        this.userStore = UserStore;
        this.configStore = ConfigStore;

        this.init();
    }

    /**
     * 初始化组件
     */
    async init() {
        this.bindStoreEvents();
        await this.loadUserStats();
    }

    /**
     * 绑定状态管理事件
     */
    bindStoreEvents() {
        // 监听用户状态变化
        this.userStore.subscribe((state) => {
            this.handleUserStateChange(state);
        });

        // 监听配置状态变化
        this.configStore.subscribe((state) => {
            this.handleConfigStateChange(state);
        });

        // 监听认证事件
        window.addEventListener('auth:profile-updated', (e) => {
            this.handleProfileUpdated(e.detail);
        });

        window.addEventListener('auth:logout', () => {
            this.handleLogout();
        });
    }

    /**
     * 加载用户统计数据
     */
    async loadUserStats() {
        try {
            const response = await this.eventService.getUserStats();
            if (response.success) {
                const data = response.data;
                // 映射后端数据到前端期望的格式
                this.userStats = {
                    totalReports: data.total_events || 0,
                    resolvedReports: data.status_stats?.resolved || 0,
                    contributionPoints: (data.total_events || 0) * 10, // 简单计算贡献值
                    achievementLevel: this.calculateAchievementLevel(data.total_events || 0)
                };
                this.updateStatsDisplay();
            }
        } catch (error) {
            console.warn('Failed to load user stats:', error);
            // 使用默认统计数据
            this.userStats = {
                totalReports: 0,
                resolvedReports: 0,
                contributionPoints: 0,
                achievementLevel: '新手市民'
            };
        }
    }

    /**
     * 计算成就等级
     */
    calculateAchievementLevel(totalEvents) {
        if (totalEvents >= 50) return '社区达人';
        if (totalEvents >= 20) return '活跃市民';
        if (totalEvents >= 10) return '热心市民';
        if (totalEvents >= 5) return '参与市民';
        return '新手市民';
    }

    /**
     * 渲染页面
     */
    render() {
        this.container = document.createElement('div');
        this.container.className = 'profile-page min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 pt-96';

        this.container.innerHTML = this.getTemplate();

        // 渲染子组件
        this.renderComponents();

        // 绑定页面事件
        this.bindPageEvents();

        // 添加页面加载动画
        this.animatePageLoad();

        // 更新用户信息显示
        this.updateUserDisplay();
        this.updateStatsDisplay();
        this.updateSettingsDisplay();

        return this.container;
    }

    /**
     * 获取页面模板
     */
    getTemplate() {
        return `
      <!-- 页面头部 -->
      <header class="page-header bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
        <div class="px-4 pt-12 pb-6">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                </svg>
              </div>
              <div>
                <h1 class="text-xl font-bold">个人设置</h1>
                <p class="text-blue-100 text-sm">账户管理与应用配置</p>
              </div>
            </div>
          </div>

          <!-- 用户信息卡片 -->
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6 text-center">
            <div class="user-avatar w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">
              <span id="user-initials">用户</span>
            </div>
            <h2 class="text-lg font-semibold text-gray-900 mb-1" id="user-name">加载中...</h2>
            <p class="text-sm text-gray-600 mb-4" id="user-phone">-</p>
            
            <!-- 用户统计 -->
            <div class="grid grid-cols-3 gap-4 mb-4">
              <div class="text-center">
                <div class="text-xl font-bold text-blue-600" id="total-reports">-</div>
                <div class="text-xs text-gray-600">总上报</div>
              </div>
              <div class="text-center">
                <div class="text-xl font-bold text-green-600" id="resolved-reports">-</div>
                <div class="text-xs text-gray-600">已解决</div>
              </div>
              <div class="text-center">
                <div class="text-xl font-bold text-yellow-600" id="contribution-points">-</div>
                <div class="text-xs text-gray-600">贡献值</div>
              </div>
            </div>
            
            <!-- 成就徽章 -->
            <div class="achievement-badge inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-yellow-400 to-orange-500 text-white">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
              </svg>
              <span id="achievement-level">新手市民</span>
            </div>
          </div>
        </div>
      </header>

      <!-- 主要内容区域 -->
      <main class="page-content px-4 py-6 pb-24 space-y-6">
        <!-- 账户设置 -->
        <section class="account-settings">
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">账户设置</h3>
            <div class="space-y-4">
              <div class="setting-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer" id="edit-profile-btn">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">个人信息</div>
                    <div class="text-sm text-gray-600">编辑姓名、电话等信息</div>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
              
              <div class="setting-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer" id="change-password-btn">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">修改密码</div>
                    <div class="text-sm text-gray-600">更新登录密码</div>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
            </div>
          </div>
        </section>

        <!-- 通知设置 -->
        <section class="notification-settings">
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">通知设置</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between p-3">
                <div>
                  <div class="font-medium text-gray-900">事件状态更新</div>
                  <div class="text-sm text-gray-600">事件处理状态变化时通知</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" id="status-notifications" class="sr-only">
                  <div class="toggle-slider"></div>
                </label>
              </div>
              
              <div class="flex items-center justify-between p-3">
                <div>
                  <div class="font-medium text-gray-900">推送通知</div>
                  <div class="text-sm text-gray-600">接收重要事件推送</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" id="push-notifications" class="sr-only">
                  <div class="toggle-slider"></div>
                </label>
              </div>
              
              <div class="flex items-center justify-between p-3">
                <div>
                  <div class="font-medium text-gray-900">邮件通知</div>
                  <div class="text-sm text-gray-600">通过邮件接收通知</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" id="email-notifications" class="sr-only">
                  <div class="toggle-slider"></div>
                </label>
              </div>
            </div>
          </div>
        </section>

        <!-- 隐私设置 -->
        <section class="privacy-settings">
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">隐私设置</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between p-3">
                <div>
                  <div class="font-medium text-gray-900">位置服务</div>
                  <div class="text-sm text-gray-600">允许应用访问位置信息</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" id="location-services" class="sr-only">
                  <div class="toggle-slider"></div>
                </label>
              </div>
              
              <div class="flex items-center justify-between p-3">
                <div>
                  <div class="font-medium text-gray-900">数据收集</div>
                  <div class="text-sm text-gray-600">帮助改进应用体验</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" id="data-collection" class="sr-only">
                  <div class="toggle-slider"></div>
                </label>
              </div>
            </div>
          </div>
        </section>

        <!-- 应用设置 -->
        <section class="app-settings">
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">应用设置</h3>
            <div class="space-y-4">
              <div class="setting-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer" id="language-settings-btn">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">语言设置</div>
                    <div class="text-sm text-gray-600" id="current-language">简体中文</div>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
              
              <div class="setting-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer" id="clear-cache-btn">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">清除缓存</div>
                    <div class="text-sm text-gray-600">释放存储空间</div>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
            </div>
          </div>
        </section>

        <!-- 帮助与支持 -->
        <section class="help-support">
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">帮助与支持</h3>
            <div class="space-y-4">
              <div class="setting-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer" id="help-btn">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-cyan-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">使用帮助</div>
                    <div class="text-sm text-gray-600">查看使用指南</div>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
              
              <div class="setting-item flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer" id="feedback-btn">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">意见反馈</div>
                    <div class="text-sm text-gray-600">提交建议和问题</div>
                  </div>
                </div>
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </div>
            </div>
          </div>
        </section>

        <!-- 关于应用 -->
        <section class="about-app">
          <div class="glass-card bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-6 cursor-pointer hover:bg-gray-50 transition-colors" id="about-app-btn">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">关于应用</h3>
                <div class="text-sm text-gray-600 mt-1">基层治理智能体</div>
              </div>
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </div>
          </div>
        </section>

        <!-- 退出登录按钮 -->
        <section class="logout-section mt-8">
          <button id="logout-btn" class="w-full bg-red-600 text-white py-4 rounded-xl font-semibold text-lg hover:bg-red-700 transition-colors">
            退出登录
          </button>
        </section>
      </main>

      <!-- 底部导航容器 -->
      <div id="navigation-container" class="navigation-container">
        <!-- Navigation 组件将在这里渲染 -->
      </div>
    `;
    }

    /**
     * 渲染子组件
     */
    renderComponents() {
        // 渲染导航组件
        this.navigation = new Navigation({
            activeTab: 'profile',
            onNavigate: (path, tabId) => this.handleNavigation(path, tabId)
        });

        const navContainer = this.container.querySelector('#navigation-container');
        this.navigation.mount(navContainer);
    }

    /**
     * 绑定页面事件
     */
    bindPageEvents() {
        // 账户设置事件
        const editProfileBtn = this.container.querySelector('#edit-profile-btn');
        const changePasswordBtn = this.container.querySelector('#change-password-btn');

        editProfileBtn.addEventListener('click', () => this.showEditProfileModal());
        changePasswordBtn.addEventListener('click', () => this.showChangePasswordModal());

        // 应用设置事件
        const languageSettingsBtn = this.container.querySelector('#language-settings-btn');
        const clearCacheBtn = this.container.querySelector('#clear-cache-btn');

        languageSettingsBtn.addEventListener('click', () => this.showLanguageSettings());
        clearCacheBtn.addEventListener('click', () => this.clearCache());

        // 帮助与支持事件
        const helpBtn = this.container.querySelector('#help-btn');
        const feedbackBtn = this.container.querySelector('#feedback-btn');

        helpBtn.addEventListener('click', () => this.showHelp());
        feedbackBtn.addEventListener('click', () => this.showFeedback());

        // 关于应用事件
        const aboutAppBtn = this.container.querySelector('#about-app-btn');
        if (aboutAppBtn) {
            aboutAppBtn.addEventListener('click', () => this.showAboutApp());
        }

        // 退出登录事件
        const logoutBtn = this.container.querySelector('#logout-btn');
        logoutBtn.addEventListener('click', () => this.handleLogout());

        // 设置开关事件
        this.bindToggleSwitches();
    }

    /**
     * 绑定设置开关事件
     */
    bindToggleSwitches() {
        const toggles = this.container.querySelectorAll('.toggle-switch input');

        toggles.forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                this.handleSettingToggle(e.target.id, e.target.checked);
            });
        });
    }

    /**
     * 页面加载动画
     */
    animatePageLoad() {
        this.container.classList.add('animate-fade-in');

        // 依次显示各个区域
        const sections = this.container.querySelectorAll('section');
        sections.forEach((section, index) => {
            setTimeout(() => {
                section.classList.add('animate-slide-up');
            }, index * 100);
        });
    }

    /**
     * 处理导航
     */
    handleNavigation(path, tabId) {
        // 使用路由系统进行导航
        if (window.router) {
            window.router.navigate(path);
        } else {
            // 降级处理：触发自定义导航事件
            const navigationEvent = new CustomEvent('navigate', {
                detail: { path, tabId }
            });
            document.dispatchEvent(navigationEvent);
        }
    }

    /**
     * 处理用户状态变化
     */
    handleUserStateChange(state) {
        this.updateUserDisplay();
    }

    /**
     * 处理配置状态变化
     */
    handleConfigStateChange(state) {
        this.updateSettingsDisplay();
    }

    /**
     * 处理用户资料更新
     */
    handleProfileUpdated(data) {
        this.updateUserDisplay();
        Notification.show('个人信息已更新', 'success');
    }

    /**
     * 更新用户信息显示
     */
    updateUserDisplay() {
        const userState = this.userStore.getState();
        const user = userState.user;

        if (user) {
            const userInitials = this.container.querySelector('#user-initials');
            const userName = this.container.querySelector('#user-name');
            const userPhone = this.container.querySelector('#user-phone');

            // 更新用户头像首字母
            const initials = user.name ? user.name.substring(0, 2) :
                user.username ? user.username.substring(0, 2) : '用户';
            userInitials.textContent = initials;

            // 更新用户名
            userName.textContent = user.name || user.username || '用户';

            // 更新手机号（脱敏显示）
            if (user.phone) {
                const maskedPhone = user.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
                userPhone.textContent = maskedPhone;
            } else {
                userPhone.textContent = '-';
            }
        }
    }

    /**
     * 更新统计数据显示
     */
    updateStatsDisplay() {
        if (!this.userStats) return;

        const totalReports = this.container.querySelector('#total-reports');
        const resolvedReports = this.container.querySelector('#resolved-reports');
        const contributionPoints = this.container.querySelector('#contribution-points');
        const achievementLevel = this.container.querySelector('#achievement-level');

        // 使用动画更新数字
        this.animateNumber(totalReports, this.userStats.totalReports);
        this.animateNumber(resolvedReports, this.userStats.resolvedReports);
        this.animateNumber(contributionPoints, this.userStats.contributionPoints);

        // 更新成就等级
        if (achievementLevel) {
            achievementLevel.textContent = this.userStats.achievementLevel || '新手市民';
        }
    }

    /**
     * 数字动画
     */
    animateNumber(element, targetValue) {
        // 确保targetValue是有效数字
        const safeTargetValue = Number(targetValue) || 0;
        const startValue = 0;
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // 使用缓动函数
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.round(startValue + (safeTargetValue - startValue) * easeOutQuart);

            element.textContent = currentValue;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * 更新设置显示
     */
    updateSettingsDisplay() {
        const configState = this.configStore.getState();
        const settings = configState.settings;

        // 更新通知设置
        const statusNotifications = this.container.querySelector('#status-notifications');
        const pushNotifications = this.container.querySelector('#push-notifications');
        const emailNotifications = this.container.querySelector('#email-notifications');

        if (statusNotifications) statusNotifications.checked = settings.statusNotifications !== false;
        if (pushNotifications) pushNotifications.checked = settings.pushNotifications !== false;
        if (emailNotifications) emailNotifications.checked = settings.emailNotifications === true;

        // 更新隐私设置
        const locationServices = this.container.querySelector('#location-services');
        const dataCollection = this.container.querySelector('#data-collection');

        if (locationServices) locationServices.checked = settings.locationServices !== false;
        if (dataCollection) dataCollection.checked = settings.dataCollection !== false;

        // 更新语言设置显示
        const currentLanguage = this.container.querySelector('#current-language');
        if (currentLanguage) {
            const languageMap = {
                'zh-CN': '简体中文',
                'en-US': 'English'
            };
            currentLanguage.textContent = languageMap[settings.language] || '简体中文';
        }
    }

    /**
     * 处理设置开关切换
     */
    handleSettingToggle(settingId, checked) {
        const settingKey = settingId.replace(/-([a-z])/g, (g) => g[1].toUpperCase());

        this.configStore.updateSetting(settingKey, checked);

        // 显示保存提示
        Notification.show('设置已保存', 'success');
    }

    /**
     * 显示编辑个人资料模态框
     */
    showEditProfileModal() {
        const userState = this.userStore.getState();
        const user = userState.user || {};

        const editProfileContent = document.createElement('div');
        editProfileContent.className = 'edit-profile-content';
        editProfileContent.innerHTML = `
      <div class="space-y-4">
        <!-- 头像上传 -->
        <div class="text-center mb-6">
          <div class="relative inline-block">
            <div class="user-avatar w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-2">
              <span id="edit-user-initials">${user.name ? user.name.substring(0, 2) : '用户'}</span>
            </div>
            <button id="upload-avatar-btn" class="absolute bottom-0 right-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center hover:bg-blue-700 transition-colors">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
            </button>
          </div>
          <p class="text-sm text-gray-500">点击上传头像</p>
          <input type="file" id="avatar-input" accept="image/*" class="hidden">
        </div>

        <!-- 基本信息表单 -->
        <form id="edit-profile-form" class="space-y-4">
          <div>
            <label class="form-label">姓名</label>
            <input 
              type="text" 
              id="edit-name" 
              name="name"
              value="${user.name || ''}" 
              class="form-input"
              placeholder="请输入姓名"
              maxlength="20"
              required
            >
            <div class="text-xs text-gray-500 mt-1">2-20个字符</div>
          </div>

          <div>
            <label class="form-label">手机号</label>
            <input 
              type="tel" 
              id="edit-phone" 
              name="phone"
              value="${user.phone || ''}" 
              class="form-input"
              placeholder="请输入手机号"
              pattern="^1[3-9]\\d{9}$"
              required
            >
            <div class="text-xs text-gray-500 mt-1">用于登录和接收通知</div>
          </div>

          <div>
            <label class="form-label">邮箱（可选）</label>
            <input 
              type="email" 
              id="edit-email" 
              name="email"
              value="${user.email || ''}" 
              class="form-input"
              placeholder="请输入邮箱地址"
            >
            <div class="text-xs text-gray-500 mt-1">用于接收邮件通知</div>
          </div>

          <div>
            <label class="form-label">个人简介（可选）</label>
            <textarea 
              id="edit-bio" 
              name="bio"
              rows="3"
              class="form-input resize-none"
              placeholder="简单介绍一下自己..."
              maxlength="200"
            >${user.bio || ''}</textarea>
            <div class="text-right text-xs text-gray-500 mt-1">
              <span id="bio-count">${(user.bio || '').length}</span>/200
            </div>
          </div>

          <!-- 地址信息 -->
          <div>
            <label class="form-label">常用地址（可选）</label>
            <input 
              type="text" 
              id="edit-address" 
              name="address"
              value="${user.address || ''}" 
              class="form-input"
              placeholder="请输入常用地址"
              maxlength="100"
            >
            <div class="text-xs text-gray-500 mt-1">用于快速定位</div>
          </div>
        </form>

        <!-- 上传进度 -->
        <div id="upload-progress" class="hidden">
          <div class="bg-gray-200 rounded-full h-2">
            <div id="upload-progress-bar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
          </div>
          <div class="text-sm text-gray-600 mt-1 text-center">
            <span id="upload-progress-text">上传中...</span>
          </div>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '编辑个人资料',
            content: editProfileContent,
            className: 'max-w-md',
            actions: [
                {
                    key: 'cancel',
                    label: '取消',
                    className: 'btn-secondary',
                    handler: (modal) => modal.hide()
                },
                {
                    key: 'save',
                    label: '保存',
                    className: 'btn-primary',
                    handler: (modal) => this.handleSaveProfile(modal)
                }
            ],
            onShow: () => {
                this.bindEditProfileEvents();
            }
        });

        this.currentModal.show();
    }

    /**
     * 绑定编辑资料事件
     */
    bindEditProfileEvents() {
        const uploadAvatarBtn = document.getElementById('upload-avatar-btn');
        const avatarInput = document.getElementById('avatar-input');
        const bioTextarea = document.getElementById('edit-bio');
        const bioCount = document.getElementById('bio-count');
        const nameInput = document.getElementById('edit-name');
        const editUserInitials = document.getElementById('edit-user-initials');

        // 头像上传事件
        uploadAvatarBtn.addEventListener('click', () => {
            avatarInput.click();
        });

        avatarInput.addEventListener('change', (e) => {
            this.handleAvatarUpload(e.target.files[0]);
        });

        // 个人简介字数统计
        bioTextarea.addEventListener('input', (e) => {
            bioCount.textContent = e.target.value.length;
        });

        // 姓名变化时更新头像首字母
        nameInput.addEventListener('input', (e) => {
            const name = e.target.value.trim();
            if (name) {
                editUserInitials.textContent = name.substring(0, 2);
            }
        });

        // 表单验证
        const form = document.getElementById('edit-profile-form');
        form.addEventListener('input', (e) => {
            this.validateProfileForm();
        });
    }

    /**
     * 处理头像上传
     */
    async handleAvatarUpload(file) {
        if (!file) return;

        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            Notification.show('请选择图片文件', 'error');
            return;
        }

        // 验证文件大小 (5MB)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            Notification.show('图片大小不能超过5MB', 'error');
            return;
        }

        try {
            // 显示上传进度
            this.showUploadProgress();

            // 压缩图片
            const compressedFile = await this.compressImage(file, 0.8, 400, 400);

            // 上传文件
            const uploadResult = await this.fileService.uploadFile(compressedFile, (progress) => {
                this.updateUploadProgress(progress);
            });

            if (uploadResult.success) {
                // 更新头像预览
                const userAvatar = document.querySelector('.user-avatar');
                userAvatar.style.backgroundImage = `url(${uploadResult.data.url})`;
                userAvatar.style.backgroundSize = 'cover';
                userAvatar.style.backgroundPosition = 'center';
                userAvatar.innerHTML = '';

                // 保存头像URL到表单数据
                this.tempAvatarUrl = uploadResult.data.url;

                this.hideUploadProgress();
                Notification.show('头像上传成功', 'success');
            } else {
                throw new Error(uploadResult.message || '头像上传失败');
            }
        } catch (error) {
            console.error('Avatar upload failed:', error);
            this.hideUploadProgress();
            Notification.show(error.message || '头像上传失败', 'error');
        }
    }

    /**
     * 压缩图片
     */
    compressImage(file, quality = 0.8, maxWidth = 400, maxHeight = 400) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();

            img.onload = () => {
                // 计算压缩后的尺寸
                let { width, height } = img;

                if (width > height) {
                    if (width > maxWidth) {
                        height = (height * maxWidth) / width;
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width = (width * maxHeight) / height;
                        height = maxHeight;
                    }
                }

                canvas.width = width;
                canvas.height = height;

                // 绘制压缩后的图片
                ctx.drawImage(img, 0, 0, width, height);

                // 转换为Blob
                canvas.toBlob(resolve, 'image/jpeg', quality);
            };

            img.src = URL.createObjectURL(file);
        });
    }

    /**
     * 显示上传进度
     */
    showUploadProgress() {
        const uploadProgress = document.getElementById('upload-progress');
        if (uploadProgress) {
            uploadProgress.classList.remove('hidden');
        }
    }

    /**
     * 更新上传进度
     */
    updateUploadProgress(progress) {
        const progressBar = document.getElementById('upload-progress-bar');
        const progressText = document.getElementById('upload-progress-text');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }

        if (progressText) {
            progressText.textContent = `上传中... ${progress}%`;
        }
    }

    /**
     * 隐藏上传进度
     */
    hideUploadProgress() {
        const uploadProgress = document.getElementById('upload-progress');
        if (uploadProgress) {
            uploadProgress.classList.add('hidden');
        }
    }

    /**
     * 验证个人资料表单
     */
    validateProfileForm() {
        const form = document.getElementById('edit-profile-form');
        const nameInput = form.querySelector('#edit-name');
        const phoneInput = form.querySelector('#edit-phone');
        const emailInput = form.querySelector('#edit-email');

        let isValid = true;

        // 验证姓名
        if (!nameInput.value.trim() || nameInput.value.trim().length < 2) {
            this.setFieldError(nameInput, '姓名至少需要2个字符');
            isValid = false;
        } else {
            this.clearFieldError(nameInput);
        }

        // 验证手机号
        const phoneRegex = /^1[3-9]\d{9}$/;
        if (!phoneInput.value.trim() || !phoneRegex.test(phoneInput.value.trim())) {
            this.setFieldError(phoneInput, '请输入正确的手机号');
            isValid = false;
        } else {
            this.clearFieldError(phoneInput);
        }

        // 验证邮箱（可选）
        if (emailInput.value.trim()) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailInput.value.trim())) {
                this.setFieldError(emailInput, '请输入正确的邮箱地址');
                isValid = false;
            } else {
                this.clearFieldError(emailInput);
            }
        } else {
            this.clearFieldError(emailInput);
        }

        return isValid;
    }

    /**
     * 设置字段错误
     */
    setFieldError(field, message) {
        field.classList.add('border-red-500');

        // 移除旧的错误信息
        const oldError = field.parentNode.querySelector('.field-error');
        if (oldError) {
            oldError.remove();
        }

        // 添加新的错误信息
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-xs text-red-500 mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * 清除字段错误
     */
    clearFieldError(field) {
        field.classList.remove('border-red-500');

        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * 处理保存个人资料
     */
    async handleSaveProfile(modal) {
        if (!this.validateProfileForm()) {
            Notification.show('请检查输入信息', 'error');
            return;
        }

        const form = document.getElementById('edit-profile-form');
        const formData = new FormData(form);

        const profileData = {
            name: formData.get('name').trim(),
            phone: formData.get('phone').trim(),
            email: formData.get('email').trim() || null,
            bio: formData.get('bio').trim() || null,
            address: formData.get('address').trim() || null
        };

        // 如果有上传的头像，添加到数据中
        if (this.tempAvatarUrl) {
            profileData.avatar = this.tempAvatarUrl;
        }

        try {
            // 设置加载状态
            this.userStore.setUpdateLoading(true);

            // 更新保存按钮状态
            const saveBtn = modal.container.querySelector('[data-action="save"]');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '保存中...';
            saveBtn.disabled = true;

            // 调用API更新用户资料
            const response = await this.authService.updateProfile(profileData);

            if (response.success) {
                // 更新本地用户状态
                this.userStore.updateUser(response.data);

                // 清除临时头像URL
                this.tempAvatarUrl = null;

                modal.hide();
                Notification.show('个人资料已更新', 'success');
            } else {
                throw new Error(response.message || '更新失败');
            }
        } catch (error) {
            console.error('Update profile failed:', error);
            Notification.show(error.message || '更新个人资料失败', 'error');

            // 恢复按钮状态
            const saveBtn = modal.container.querySelector('[data-action="save"]');
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        } finally {
            this.userStore.setUpdateLoading(false);
        }
    }

    /**
     * 显示修改密码模态框
     */
    showChangePasswordModal() {
        const changePasswordContent = document.createElement('div');
        changePasswordContent.className = 'change-password-content';
        changePasswordContent.innerHTML = `
      <div class="space-y-4">
        <!-- 密码修改表单 -->
        <form id="change-password-form" class="space-y-4">
          <div>
            <label class="form-label">当前密码</label>
            <div class="relative">
              <input 
                type="password" 
                id="current-password" 
                name="currentPassword"
                class="form-input pr-10"
                placeholder="请输入当前密码"
                required
                autocomplete="current-password"
              >
              <button type="button" class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600" onclick="this.previousElementSibling.type = this.previousElementSibling.type === 'password' ? 'text' : 'password'">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                </svg>
              </button>
            </div>
          </div>

          <div>
            <label class="form-label">新密码</label>
            <div class="relative">
              <input 
                type="password" 
                id="new-password" 
                name="newPassword"
                class="form-input pr-10"
                placeholder="请输入新密码"
                minlength="6"
                maxlength="20"
                required
                autocomplete="new-password"
              >
              <button type="button" class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600" onclick="this.previousElementSibling.type = this.previousElementSibling.type === 'password' ? 'text' : 'password'">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                </svg>
              </button>
            </div>
          </div>

          <div>
            <label class="form-label">确认新密码</label>
            <div class="relative">
              <input 
                type="password" 
                id="confirm-password" 
                name="confirmPassword"
                class="form-input pr-10"
                placeholder="请再次输入新密码"
                minlength="6"
                maxlength="20"
                required
                autocomplete="new-password"
              >
              <button type="button" class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600" onclick="this.previousElementSibling.type = this.previousElementSibling.type === 'password' ? 'text' : 'password'">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- 安全验证选项 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-900 mb-3">安全验证</h4>
            <div class="space-y-2">
              <label class="flex items-center">
                <input type="radio" name="verification" value="sms" class="mr-2" checked>
                <span class="text-sm text-gray-700">短信验证码验证</span>
              </label>
              <label class="flex items-center">
                <input type="radio" name="verification" value="email" class="mr-2">
                <span class="text-sm text-gray-700">邮箱验证码验证</span>
              </label>
            </div>
            
            <!-- 验证码输入 -->
            <div id="verification-section" class="mt-4 space-y-3">
              <div class="flex space-x-2">
                <input 
                  type="text" 
                  id="verification-code" 
                  name="verificationCode"
                  class="form-input flex-1"
                  placeholder="请输入验证码"
                  maxlength="6"
                  pattern="\\d{6}"
                >
                <button 
                  type="button" 
                  id="send-verification-btn"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm whitespace-nowrap"
                >
                  发送验证码
                </button>
              </div>
              <div class="text-xs text-gray-500">
                <span id="verification-target">验证码将发送到您的手机</span>
              </div>
            </div>
          </div>
        </form>
      </div>
    `;

        this.currentModal = new Modal({
            title: '修改密码',
            content: changePasswordContent,
            className: 'max-w-md',
            actions: [
                {
                    key: 'cancel',
                    label: '取消',
                    className: 'btn-secondary',
                    handler: (modal) => modal.hide()
                },
                {
                    key: 'save',
                    label: '确认修改',
                    className: 'btn-primary',
                    handler: (modal) => this.handleChangePassword(modal)
                }
            ],
            onShow: () => {
                this.bindChangePasswordEvents();
            }
        });

        this.currentModal.show();
    }

    /**
     * 绑定修改密码事件
     */
    bindChangePasswordEvents() {
        const newPasswordInput = document.getElementById('new-password');
        const confirmPasswordInput = document.getElementById('confirm-password');
        const sendVerificationBtn = document.getElementById('send-verification-btn');
        const verificationRadios = document.querySelectorAll('input[name="verification"]');
        const verificationTarget = document.getElementById('verification-target');

        // 密码强度检测
        newPasswordInput.addEventListener('input', (e) => {
            this.updatePasswordStrength(e.target.value);
            this.validatePasswordMatch();
        });

        // 确认密码验证
        confirmPasswordInput.addEventListener('input', () => {
            this.validatePasswordMatch();
        });

        // 验证方式切换
        verificationRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                const method = e.target.value;
                if (method === 'sms') {
                    verificationTarget.textContent = '验证码将发送到您的手机';
                } else {
                    verificationTarget.textContent = '验证码将发送到您的邮箱';
                }
            });
        });

        // 发送验证码
        sendVerificationBtn.addEventListener('click', () => {
            this.sendVerificationCode();
        });

        // 表单验证
        const form = document.getElementById('change-password-form');
        form.addEventListener('input', () => {
            this.validatePasswordForm();
        });
    }

    /**
     * 更新密码强度
     */
    updatePasswordStrength(password) {
        const strengthBar = document.getElementById('password-strength-bar');
        const strengthText = document.getElementById('password-strength-text');

        let strength = 0;
        let strengthLabel = '弱';
        let strengthColor = '#ef4444';

        if (password.length >= 6) strength += 1;
        if (password.length >= 8) strength += 1;
        if (/[a-z]/.test(password)) strength += 1;
        if (/[A-Z]/.test(password)) strength += 1;
        if (/\d/.test(password)) strength += 1;
        if (/[^a-zA-Z\d]/.test(password)) strength += 1;

        if (strength >= 5) {
            strengthLabel = '强';
            strengthColor = '#10b981';
        } else if (strength >= 3) {
            strengthLabel = '中';
            strengthColor = '#f59e0b';
        }

        const percentage = Math.min((strength / 6) * 100, 100);
        strengthBar.style.width = `${percentage}%`;
        strengthBar.style.backgroundColor = strengthColor;
        strengthText.textContent = `密码强度: ${strengthLabel}`;
        strengthText.style.color = strengthColor;
    }

    /**
     * 验证密码匹配
     */
    validatePasswordMatch() {
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const confirmPasswordInput = document.getElementById('confirm-password');

        if (confirmPassword && newPassword !== confirmPassword) {
            this.setFieldError(confirmPasswordInput, '两次输入的密码不一致');
            return false;
        } else {
            this.clearFieldError(confirmPasswordInput);
            return true;
        }
    }

    /**
     * 验证密码表单
     */
    validatePasswordForm() {
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const verificationCode = document.getElementById('verification-code').value;

        let isValid = true;

        // 验证当前密码
        if (!currentPassword.trim()) {
            isValid = false;
        }

        // 验证新密码
        if (!newPassword.trim() || newPassword.length < 6 || newPassword.length > 20) {
            isValid = false;
        }

        // 验证密码匹配
        if (!this.validatePasswordMatch()) {
            isValid = false;
        }

        // 验证验证码
        if (!verificationCode.trim() || verificationCode.length !== 6) {
            isValid = false;
        }

        return isValid;
    }

    /**
     * 发送验证码
     */
    async sendVerificationCode() {
        const sendBtn = document.getElementById('send-verification-btn');
        const verificationMethod = document.querySelector('input[name="verification"]:checked').value;
        const userState = this.userStore.getState();
        const user = userState.user;

        if (!user) {
            Notification.show('用户信息不存在', 'error');
            return;
        }

        // 验证联系方式
        if (verificationMethod === 'sms' && !user.phone) {
            Notification.show('请先设置手机号', 'error');
            return;
        }

        if (verificationMethod === 'email' && !user.email) {
            Notification.show('请先设置邮箱地址', 'error');
            return;
        }

        try {
            // 禁用按钮并显示倒计时
            sendBtn.disabled = true;
            let countdown = 60;

            const updateCountdown = () => {
                sendBtn.textContent = `${countdown}秒后重发`;
                countdown--;

                if (countdown < 0) {
                    sendBtn.disabled = false;
                    sendBtn.textContent = '发送验证码';
                } else {
                    setTimeout(updateCountdown, 1000);
                }
            };

            updateCountdown();

            // 发送验证码
            const target = verificationMethod === 'sms' ? user.phone : user.email;
            const response = await this.authService.sendVerificationCode(target, 'change_password');

            if (response.success) {
                Notification.show('验证码已发送', 'success');
            } else {
                throw new Error(response.message || '验证码发送失败');
            }
        } catch (error) {
            console.error('Send verification code failed:', error);
            Notification.show(error.message || '验证码发送失败', 'error');

            // 恢复按钮状态
            sendBtn.disabled = false;
            sendBtn.textContent = '发送验证码';
        }
    }

    /**
     * 处理修改密码
     */
    async handleChangePassword(modal) {
        if (!this.validatePasswordForm()) {
            Notification.show('请检查输入信息', 'error');
            return;
        }

        const form = document.getElementById('change-password-form');
        const formData = new FormData(form);

        const changeData = {
            old_password: formData.get('currentPassword'),
            new_password: formData.get('newPassword'),
            verification_code: formData.get('verificationCode'),
            verification_method: formData.get('verification')
        };

        try {
            // 更新按钮状态
            const saveBtn = modal.container.querySelector('[data-action="save"]');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '修改中...';
            saveBtn.disabled = true;

            // 调用API修改密码
            const response = await this.authService.changePassword(changeData);

            if (response.success) {
                modal.hide();

                // 显示成功提示
                Notification.show('密码修改成功，请重新登录', 'success');

                // 延迟后自动退出登录
                setTimeout(async () => {
                    await this.authService.logout();
                }, 2000);
            } else {
                throw new Error(response.message || '密码修改失败');
            }
        } catch (error) {
            console.error('Change password failed:', error);

            // 处理特定错误
            let errorMessage = error.message || '密码修改失败';

            if (error.message.includes('当前密码')) {
                errorMessage = '当前密码不正确';
            } else if (error.message.includes('验证码')) {
                errorMessage = '验证码不正确或已过期';
            } else if (error.message.includes('密码强度')) {
                errorMessage = '新密码强度不够，请设置更复杂的密码';
            }

            Notification.show(errorMessage, 'error');

            // 恢复按钮状态
            const saveBtn = modal.container.querySelector('[data-action="save"]');
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }
    }

    /**
     * 显示语言设置
     */
    showLanguageSettings() {
        const configState = this.configStore.getState();
        const currentLanguage = configState.settings.language;

        const languageContent = document.createElement('div');
        languageContent.className = 'language-settings-content';
        languageContent.innerHTML = `
      <div class="space-y-4">
        <div class="text-sm text-gray-600 mb-4">
          选择您偏好的语言，应用将在下次启动时生效。
        </div>
        
        <div class="space-y-3">
          <label class="flex items-center p-3 rounded-lg border hover:bg-gray-50 cursor-pointer ${currentLanguage === 'zh-CN' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}">
            <input 
              type="radio" 
              name="language" 
              value="zh-CN" 
              class="mr-3"
              ${currentLanguage === 'zh-CN' ? 'checked' : ''}
            >
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                中
              </div>
              <div>
                <div class="font-medium text-gray-900">简体中文</div>
                <div class="text-sm text-gray-500">Simplified Chinese</div>
              </div>
            </div>
            ${currentLanguage === 'zh-CN' ? '<svg class="w-5 h-5 text-blue-500 ml-auto" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>' : ''}
          </label>
          
          <label class="flex items-center p-3 rounded-lg border hover:bg-gray-50 cursor-pointer ${currentLanguage === 'en-US' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}">
            <input 
              type="radio" 
              name="language" 
              value="en-US" 
              class="mr-3"
              ${currentLanguage === 'en-US' ? 'checked' : ''}
            >
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                EN
              </div>
              <div>
                <div class="font-medium text-gray-900">English</div>
                <div class="text-sm text-gray-500">英语</div>
              </div>
            </div>
            ${currentLanguage === 'en-US' ? '<svg class="w-5 h-5 text-blue-500 ml-auto" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>' : ''}
          </label>
        </div>
        

      </div>
    `;

        this.currentModal = new Modal({
            title: '语言设置',
            content: languageContent,
            className: 'max-w-md',
            actions: [
                {
                    key: 'cancel',
                    label: '取消',
                    className: 'btn-secondary',
                    handler: (modal) => modal.hide()
                },
                {
                    key: 'save',
                    label: '保存',
                    className: 'btn-primary',
                    handler: (modal) => this.handleLanguageChange(modal)
                }
            ]
        });

        this.currentModal.show();
    }

    /**
     * 处理语言更改
     */
    handleLanguageChange(modal) {
        const selectedLanguage = modal.container.querySelector('input[name="language"]:checked').value;
        const configState = this.configStore.getState();

        if (selectedLanguage !== configState.settings.language) {
            // 更新语言设置
            this.configStore.setLanguage(selectedLanguage);

            // 更新显示
            this.updateSettingsDisplay();

            modal.hide();
            Notification.show('语言设置已保存', 'success');

            // 提示刷新页面
            setTimeout(() => {
                if (confirm('语言已更改，是否刷新页面以应用新语言？')) {
                    window.location.reload();
                }
            }, 1000);
        } else {
            modal.hide();
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        const clearCacheContent = document.createElement('div');
        clearCacheContent.className = 'clear-cache-content';
        clearCacheContent.innerHTML = `
      <div class="space-y-4">
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 bg-orange-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">清除应用缓存</h3>
          <p class="text-gray-600 mb-4">这将清除以下缓存数据：</p>
        </div>
        
        <div class="space-y-3">
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <span class="text-sm text-gray-700">图片缓存</span>
            </div>
            <span class="text-sm text-gray-500" id="image-cache-size">计算中...</span>
          </div>
          
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              <span class="text-sm text-gray-700">数据缓存</span>
            </div>
            <span class="text-sm text-gray-500" id="data-cache-size">计算中...</span>
          </div>
          
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
              <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span class="text-sm text-gray-700">临时文件</span>
            </div>
            <span class="text-sm text-gray-500" id="temp-cache-size">计算中...</span>
          </div>
        </div>
        
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div class="flex items-start space-x-2">
            <svg class="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
            <div class="text-sm text-yellow-800">
              <p class="font-medium mb-1">注意</p>
              <p>清除缓存后，应用可能需要重新加载数据，首次加载速度会变慢。</p>
            </div>
          </div>
        </div>
        
        <div class="text-center">
          <div class="text-sm text-gray-600">
            总缓存大小: <span id="total-cache-size" class="font-medium">计算中...</span>
          </div>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '清除缓存',
            content: clearCacheContent,
            className: 'max-w-md',
            actions: [
                {
                    key: 'cancel',
                    label: '取消',
                    className: 'btn-secondary',
                    handler: (modal) => modal.hide()
                },
                {
                    key: 'clear',
                    label: '清除缓存',
                    className: 'btn-danger',
                    handler: (modal) => this.handleClearCache(modal)
                }
            ],
            onShow: () => {
                this.calculateCacheSize();
            }
        });

        this.currentModal.show();
    }

    /**
     * 计算缓存大小
     */
    async calculateCacheSize() {
        try {
            // 计算localStorage大小
            let localStorageSize = 0;
            for (let key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    localStorageSize += localStorage[key].length + key.length;
                }
            }

            // 计算sessionStorage大小
            let sessionStorageSize = 0;
            for (let key in sessionStorage) {
                if (sessionStorage.hasOwnProperty(key)) {
                    sessionStorageSize += sessionStorage[key].length + key.length;
                }
            }

            // 估算缓存大小（字节转换为可读格式）
            const formatSize = (bytes) => {
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            };

            // 更新显示
            const imageCacheSize = document.getElementById('image-cache-size');
            const dataCacheSize = document.getElementById('data-cache-size');
            const tempCacheSize = document.getElementById('temp-cache-size');
            const totalCacheSize = document.getElementById('total-cache-size');

            if (imageCacheSize) imageCacheSize.textContent = formatSize(localStorageSize * 0.6); // 估算图片缓存占60%
            if (dataCacheSize) dataCacheSize.textContent = formatSize(localStorageSize * 0.3); // 估算数据缓存占30%
            if (tempCacheSize) tempCacheSize.textContent = formatSize(sessionStorageSize); // 临时缓存
            if (totalCacheSize) totalCacheSize.textContent = formatSize(localStorageSize + sessionStorageSize);

        } catch (error) {
            console.error('Calculate cache size failed:', error);

            // 显示错误状态
            const elements = ['image-cache-size', 'data-cache-size', 'temp-cache-size', 'total-cache-size'];
            elements.forEach(id => {
                const element = document.getElementById(id);
                if (element) element.textContent = '计算失败';
            });
        }
    }

    /**
     * 处理清除缓存
     */
    async handleClearCache(modal) {
        try {
            // 更新按钮状态
            const clearBtn = modal.container.querySelector('[data-action="clear"]');
            const originalText = clearBtn.textContent;
            clearBtn.textContent = '清除中...';
            clearBtn.disabled = true;

            // 清除各种缓存
            const cacheKeys = [];

            // 收集需要清除的localStorage键
            for (let key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    // 保留用户登录信息和重要设置
                    if (!key.includes('access_token') &&
                        !key.includes('refresh_token') &&
                        !key.includes('userStore') &&
                        !key.includes('configStore')) {
                        cacheKeys.push(key);
                    }
                }
            }

            // 清除localStorage缓存
            cacheKeys.forEach(key => {
                localStorage.removeItem(key);
            });

            // 清除sessionStorage
            sessionStorage.clear();

            // 清除配置存储中的临时数据
            this.configStore.cleanupTempData();
            this.configStore.clearAllFormStates();

            // 如果支持，清除浏览器缓存
            if ('caches' in window) {
                const cacheNames = await caches.keys();
                await Promise.all(
                    cacheNames.map(cacheName => caches.delete(cacheName))
                );
            }

            // 更新缓存大小显示
            this.configStore.updateCacheSize(0);

            modal.hide();
            Notification.show('缓存清除成功', 'success');

            // 提示刷新页面
            setTimeout(() => {
                if (confirm('缓存已清除，建议刷新页面以获得最佳体验，是否立即刷新？')) {
                    window.location.reload();
                }
            }, 1000);

        } catch (error) {
            console.error('Clear cache failed:', error);
            Notification.show('缓存清除失败', 'error');

            // 恢复按钮状态
            const clearBtn = modal.container.querySelector('[data-action="clear"]');
            clearBtn.textContent = originalText;
            clearBtn.disabled = false;
        }
    }

    /**
     * 显示帮助
     */
    showHelp() {
        const helpContent = `
      <div class="help-content">
        <h3 class="text-lg font-semibold mb-4">使用帮助</h3>
        <div class="space-y-4 text-sm">
          <div>
            <h4 class="font-medium mb-2">如何上报事件？</h4>
            <p class="text-gray-600">点击底部导航的"上报"按钮，拍照或选择图片，填写事件信息后提交即可。</p>
          </div>
          <div>
            <h4 class="font-medium mb-2">如何查看事件状态？</h4>
            <p class="text-gray-600">在"跟踪"页面可以查看所有已上报事件的处理状态和详细信息。</p>
          </div>
          <div>
            <h4 class="font-medium mb-2">AI识别不准确怎么办？</h4>
            <p class="text-gray-600">AI识别结果仅供参考，您可以手动修改事件类型和描述信息。</p>
          </div>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '使用帮助',
            content: helpContent,
            actions: [
                {
                    key: 'close',
                    label: '关闭',
                    className: 'btn-primary',
                    handler: (modal) => modal.hide()
                }
            ]
        });

        this.currentModal.show();
    }

    /**
     * 显示意见反馈
     */
    showFeedback() {
        const feedbackContent = `
      <div class="feedback-content">
        <h3 class="text-lg font-semibold mb-4">意见反馈</h3>
        <form id="feedback-form" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">反馈类型</label>
            <select class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="bug">问题反馈</option>
              <option value="feature">功能建议</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">详细描述</label>
            <textarea rows="4" class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none" placeholder="请详细描述您的问题或建议..."></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">联系方式（可选）</label>
            <input type="text" class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="邮箱或手机号">
          </div>
        </form>
      </div>
    `;

        this.currentModal = new Modal({
            title: '意见反馈',
            content: feedbackContent,
            actions: [
                {
                    key: 'cancel',
                    label: '取消',
                    className: 'btn-secondary',
                    handler: (modal) => modal.hide()
                },
                {
                    key: 'submit',
                    label: '提交',
                    className: 'btn-primary',
                    handler: (modal) => {
                        Notification.show('感谢您的反馈，我们会认真处理', 'success');
                        modal.hide();
                    }
                }
            ]
        });

        this.currentModal.show();
    }

    /**
     * 显示关于应用详情
     */
    showAboutApp() {
        const aboutContent = document.createElement('div');
        aboutContent.className = 'about-app-content';
        aboutContent.innerHTML = `
      <div class="space-y-6">
        <!-- 应用信息 -->
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-2xl flex items-center justify-center">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h4M9 7h6m-6 4h6m-2 4h2M7 7h.01M7 11h.01M7 15h.01"></path>
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">基层治理智能体</h3>
          <div class="text-lg font-medium text-gray-700 mb-1">版本 1.2.0</div>
          <div class="text-sm text-gray-500">基于AI计算机视觉技术的智慧城市解决方案</div>
        </div>

        <!-- 功能介绍 -->
        <div class="bg-gray-50 rounded-lg p-4">
          <h4 class="font-medium text-gray-900 mb-2">主要功能</h4>
          <ul class="text-sm text-gray-600 space-y-1">
            <li>• 智能事件上报与处理</li>
            <li>• AI图像识别与分析</li>
            <li>• 实时事件跟踪</li>
            <li>• 多角色协同管理</li>
          </ul>
        </div>

        <!-- 法律信息 -->
        <div class="border-t pt-4">
          <div class="flex justify-center space-x-6">
            <button id="privacy-policy-btn" class="text-blue-600 text-sm hover:underline">隐私政策</button>
            <button id="terms-btn" class="text-blue-600 text-sm hover:underline">服务条款</button>
          </div>
        </div>

        <!-- 版权信息 -->
        <div class="text-center text-xs text-gray-400 border-t pt-4">
          <p>© 2024 基层治理智能体. 保留所有权利.</p>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '关于应用',
            content: aboutContent,
            className: 'max-w-md',
            actions: [
                {
                    key: 'close',
                    label: '关闭',
                    className: 'btn-primary',
                    handler: (modal) => modal.hide()
                }
            ]
        });

        // 绑定法律信息按钮事件
        setTimeout(() => {
            const privacyBtn = aboutContent.querySelector('#privacy-policy-btn');
            const termsBtn = aboutContent.querySelector('#terms-btn');
            
            if (privacyBtn) {
                privacyBtn.addEventListener('click', () => {
                    this.currentModal.hide();
                    this.showPrivacyPolicy();
                });
            }
            
            if (termsBtn) {
                termsBtn.addEventListener('click', () => {
                    this.currentModal.hide();
                    this.showTerms();
                });
            }
        }, 100);

        this.currentModal.show();
    }

    /**
     * 显示隐私政策
     */
    showPrivacyPolicy() {
        const privacyContent = `
      <div class="privacy-content">
        <h3 class="text-lg font-semibold mb-4">隐私政策</h3>
        <div class="text-sm text-gray-600 space-y-3 max-h-64 overflow-y-auto">
          <p>我们重视您的隐私保护，本政策说明我们如何收集、使用和保护您的个人信息。</p>
          <h4 class="font-medium text-gray-900">信息收集</h4>
          <p>我们可能收集您提供的个人信息，包括姓名、电话号码、位置信息等。</p>
          <h4 class="font-medium text-gray-900">信息使用</h4>
          <p>收集的信息仅用于提供服务、改进用户体验和处理您上报的事件。</p>
          <h4 class="font-medium text-gray-900">信息保护</h4>
          <p>我们采用行业标准的安全措施保护您的个人信息，不会向第三方泄露。</p>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '隐私政策',
            content: privacyContent,
            actions: [
                {
                    key: 'close',
                    label: '我知道了',
                    className: 'btn-primary',
                    handler: (modal) => modal.hide()
                }
            ]
        });

        this.currentModal.show();
    }

    /**
     * 显示服务条款
     */
    showTerms() {
        const termsContent = `
      <div class="terms-content">
        <h3 class="text-lg font-semibold mb-4">服务条款</h3>
        <div class="text-sm text-gray-600 space-y-3 max-h-64 overflow-y-auto">
          <p>欢迎使用基层治理智能体应用，使用本服务即表示您同意以下条款。</p>
          <h4 class="font-medium text-gray-900">服务内容</h4>
          <p>本应用提供基于AI技术的城市问题上报和跟踪服务。</p>
          <h4 class="font-medium text-gray-900">用户责任</h4>
          <p>用户应确保上报信息的真实性，不得恶意上报虚假信息。</p>
          <h4 class="font-medium text-gray-900">服务变更</h4>
          <p>我们保留随时修改或终止服务的权利，重要变更会提前通知用户。</p>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '服务条款',
            content: termsContent,
            actions: [
                {
                    key: 'close',
                    label: '我知道了',
                    className: 'btn-primary',
                    handler: (modal) => modal.hide()
                }
            ]
        });

        this.currentModal.show();
    }

    /**
     * 处理退出登录
     */
    async handleLogout() {
        // 防止重复调用
        if (this.isLoggingOut) {
            return;
        }
        
        const confirmContent = `
      <div class="logout-confirm">
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">确认退出登录</h3>
          <p class="text-gray-600">退出后需要重新登录才能使用应用功能</p>
        </div>
      </div>
    `;

        this.currentModal = new Modal({
            title: '退出登录',
            content: confirmContent,
            actions: [
                {
                    key: 'cancel',
                    label: '取消',
                    className: 'btn-secondary',
                    handler: (modal) => modal.hide()
                },
                {
                    key: 'confirm',
                    label: '确认退出',
                    className: 'btn-danger',
                    handler: async (modal) => {
                        // 防止重复点击
                        if (this.isLoggingOut) {
                            return;
                        }
                        
                        this.isLoggingOut = true;
                        
                        try {
                            // 先关闭弹框
                            await modal.hide();
                            
                            // 显示退出中提示
                            Notification.show('正在退出登录...', 'info');
                            
                            // 执行退出登录
                            await this.authService.logout();
                            
                            // 清除当前页面状态
                            this.currentModal = null;
                            
                        } catch (error) {
                            console.error('Logout failed:', error);
                            Notification.show('退出登录失败，请重试', 'error');
                        } finally {
                            this.isLoggingOut = false;
                        }
                    }
                }
            ]
        });

        this.currentModal.show();
    }
}