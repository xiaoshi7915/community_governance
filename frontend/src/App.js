import { Router } from './utils/Router.js';
import { AuthService } from './services/AuthService.js';
import { ErrorHandler } from './utils/ErrorHandler.js';
import { NavigationManager } from './utils/NavigationManager.js';
import { networkDetector } from './utils/NetworkDetector.js';
import UserStore from './stores/UserStore.js';

export class App {
    constructor() {
        this.router = new Router({
            container: document.getElementById('app'),
            mode: 'hash', // 使用hash模式以避免服务器配置问题
            defaultRoute: '/'
        });
        this.authService = new AuthService();
        this.userStore = UserStore;
        this.navigationManager = NavigationManager.getInstance();
    }

    async init() {
        try {
            // 初始化错误处理
            ErrorHandler.init();
            
            // 检测网络和API服务器
            console.log('🔍 检测API服务器连接...');
            const apiBaseUrl = await networkDetector.detectApiServer();
            console.log(`✅ API服务器: ${apiBaseUrl}`);
            
            // 更新全局API配置
            window.API_BASE_URL = apiBaseUrl;
            
            // 显示连接状态
            networkDetector.showConnectionStatus();
            
            // 初始化导航管理器
            this.navigationManager.init();
            
            // 注册路由
            this.registerRoutes();
            
            // 设置路由守卫
            this.setupRouteGuards();
            
            // 检查认证状态
            await this.checkAuthStatus();
            
            // 设置全局事件监听器
            this.setupGlobalEventListeners();
            
            // 启动路由
            this.router.start();
            
            // 设置全局引用
            window.router = this.router;
            window.navigationManager = this.navigationManager;
            window.userStore = this.userStore;
            
            console.log('应用初始化完成');
        } catch (error) {
            console.error('应用初始化失败:', error);
            ErrorHandler.handleError(error);
        }
    }

    /**
     * 注册应用路由
     */
    registerRoutes() {
        // 懒加载页面组件
        this.router.registerRoutes([
            {
                path: '/',
                component: () => import('./pages/HomePage.js').then(m => m.HomePage),
                options: {
                    requiresAuth: false,
                    meta: { title: '事件上报' }
                }
            },
            {
                path: '/login',
                component: () => import('./pages/LoginPage.js').then(m => m.LoginPage),
                options: {
                    requiresAuth: false,
                    meta: { title: '登录注册' }
                }
            },
            {
                path: '/tracking',
                component: () => import('./pages/TrackingPage.js').then(m => m.TrackingPage),
                options: {
                    requiresAuth: true,
                    meta: { title: '事件跟踪' }
                }
            },
            {
                path: '/profile',
                component: () => import('./pages/ProfilePage.js').then(m => m.ProfilePage),
                options: {
                    requiresAuth: true,
                    meta: { title: '个人中心' }
                }
            },
            {
                path: '/history',
                component: () => import('./pages/HistoryPage.js').then(m => m.HistoryPage),
                options: {
                    requiresAuth: true,
                    meta: { title: '历史记录' }
                }
            },
            {
                path: '/permission-test',
                component: () => import('./pages/PermissionTestPage.js').then(m => m.PermissionTestPage),
                options: {
                    requiresAuth: true,
                    meta: { title: '权限测试' }
                }
            }
        ]);
    }

    /**
     * 设置路由守卫
     */
    setupRouteGuards() {
        // 认证守卫
        this.router.addGuard(async (to, from) => {
            const route = this.router.findRoute(to);
            
            if (route?.options.requiresAuth) {
                const isAuthenticated = this.userStore.getState().isAuthenticated;
                
                if (!isAuthenticated) {
                    ErrorHandler.showWarningNotification('请先登录');
                    return '/login'; // 重定向到登录页面
                }
            }
            
            return true;
        });

        // 页面标题守卫
        this.router.addGuard(async (to, from) => {
            const route = this.router.findRoute(to);
            if (route?.options.meta?.title) {
                document.title = `${route.options.meta.title} - 基层治理智能体`;
            }
            return true;
        });
    }

    async checkAuthStatus() {
        try {
            const token = localStorage.getItem('access_token');
            if (token) {
                // 验证token有效性
                const isValid = await this.authService.validateToken(token);
                if (isValid) {
                    // 获取用户信息
                    const userInfo = await this.authService.getCurrentUser();
                    this.userStore.setUser(userInfo);
                    console.log('用户已登录:', userInfo);
                } else {
                    // token无效，清除认证信息
                    this.userStore.clearUser();
                    console.log('Token已过期，已清除认证信息');
                }
            }
        } catch (error) {
            console.error('认证状态检查失败:', error);
            this.userStore.clearUser();
        }
    }

    setupGlobalEventListeners() {
        // 监听路由变化事件
        window.addEventListener('routechange', (event) => {
            const { path, route } = event.detail;
            console.log('Route changed:', path);
            
            // 更新导航状态
            this.updateNavigationState(path);
        });

        // 监听用户状态变化
        this.userStore.subscribe((state) => {
            console.log('User state changed:', state);
        });

        // 监听网络状态变化
        window.addEventListener('online', () => {
            ErrorHandler.showSuccessNotification('网络连接已恢复');
        });

        window.addEventListener('offline', () => {
            ErrorHandler.showWarningNotification('网络连接已断开');
        });
    }

    /**
     * 更新导航状态
     * @param {string} path - 当前路径
     */
    updateNavigationState(path) {
        // 根据路径确定活动标签
        let activeTab = 'home';
        if (path.startsWith('/tracking')) {
            activeTab = 'tracking';
        } else if (path.startsWith('/profile')) {
            activeTab = 'profile';
        }

        // 触发导航更新事件
        const navigationEvent = new CustomEvent('navigationupdate', {
            detail: { activeTab, path }
        });
        document.dispatchEvent(navigationEvent);
    }

    /**
     * 获取应用实例
     */
    static getInstance() {
        if (!App.instance) {
            App.instance = new App();
        }
        return App.instance;
    }

    /**
     * 销毁应用
     */
    destroy() {
        if (this.router) {
            this.router.destroy();
        }
        
        // 清理全局引用
        delete window.router;
        
        console.log('应用已销毁');
    }
}