# 基层治理智能体前端应用

基于AI技术的智慧城市管理系统前端应用，采用现代化的前端架构重构。

## 技术栈

- **构建工具**: Vite 5.0
- **样式框架**: Tailwind CSS 3.3
- **JavaScript**: ES6+ 模块化
- **动画库**: Anime.js 3.2
- **测试框架**: Vitest
- **包管理器**: npm

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── Navigation.js    # 底部导航组件
│   │   ├── Modal.js         # 模态框组件
│   │   ├── Notification.js  # 通知组件
│   │   └── ...
│   ├── pages/              # 页面组件
│   │   ├── HomePage.js      # 首页（事件上报）
│   │   ├── TrackingPage.js  # 事件跟踪页面
│   │   └── ProfilePage.js   # 个人设置页面
│   ├── services/           # API服务层
│   │   ├── HttpClient.js    # HTTP客户端基类
│   │   ├── AuthService.js   # 认证服务
│   │   ├── EventService.js  # 事件服务
│   │   └── ...
│   ├── utils/              # 工具函数
│   │   ├── Router.js        # 路由管理
│   │   ├── ErrorHandler.js  # 错误处理
│   │   └── ...
│   ├── stores/             # 状态管理
│   │   ├── Store.js         # 基础状态管理类
│   │   ├── UserStore.js     # 用户状态
│   │   └── ...
│   ├── styles/             # 样式文件
│   │   ├── main.css         # 主样式文件
│   │   ├── components.css   # 组件样式
│   │   └── animations.css   # 动画样式
│   └── assets/             # 静态资源
├── public/                 # 公共资源
├── dist/                   # 构建输出
└── package.json           # 项目配置
```

## 开发指南

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动，支持热重载。

### 构建生产版本

```bash
npm run build
```

构建文件将输出到 `dist/` 目录。

### 预览生产版本

```bash
npm run preview
```

### 运行测试

```bash
# 运行测试
npm run test

# 运行测试UI
npm run test:ui
```

## 环境配置

### 开发环境

复制 `.env.example` 为 `.env.development` 并配置：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_DEBUG=true
```

### 生产环境

创建 `.env.production` 文件：

```env
VITE_API_BASE_URL=/api/v1
VITE_DEBUG=false
```

## API集成

应用与后端API完全对接，支持以下功能：

- 用户认证（登录/注册）
- 事件管理（创建/查询/更新）
- 文件上传
- AI智能识别
- 统计数据获取
- 通知推送

## 组件开发

### 创建新组件

```javascript
// src/components/MyComponent.js
export class MyComponent {
    constructor(props = {}) {
        this.props = props;
        this.element = null;
    }
    
    render() {
        this.element = document.createElement('div');
        this.element.innerHTML = this.template();
        this.bindEvents();
        return this.element;
    }
    
    template() {
        return `
            <div class="my-component">
                <!-- 组件模板 -->
            </div>
        `;
    }
    
    bindEvents() {
        // 事件绑定
    }
}
```

### 使用组件

```javascript
import { MyComponent } from '@components/MyComponent.js';

const component = new MyComponent({ prop: 'value' });
const element = component.render();
document.body.appendChild(element);
```

## 样式指南

### 使用Tailwind CSS类

```html
<div class="glass-card p-6 rounded-2xl shadow-lg">
    <h2 class="text-lg font-semibold mb-4">标题</h2>
    <p class="text-gray-600">内容</p>
</div>
```

### 自定义组件样式

```css
/* src/styles/components.css */
.my-component {
    @apply bg-white rounded-lg shadow-md p-4;
}

.my-component:hover {
    @apply shadow-lg transform -translate-y-1;
}
```

## 状态管理

### 创建Store

```javascript
// src/stores/MyStore.js
import { Store } from './Store.js';

export class MyStore extends Store {
    constructor() {
        super({
            data: [],
            loading: false
        });
    }
    
    setData(data) {
        this.setState({ data });
    }
    
    setLoading(loading) {
        this.setState({ loading });
    }
}
```

### 使用Store

```javascript
import { MyStore } from '@stores/MyStore.js';

const store = new MyStore();

// 订阅状态变化
const unsubscribe = store.subscribe((state) => {
    console.log('状态更新:', state);
});

// 更新状态
store.setData([1, 2, 3]);
```

## 路由管理

### 添加新路由

```javascript
// src/utils/Router.js
const routes = {
    '/': () => import('@pages/HomePage.js'),
    '/tracking': () => import('@pages/TrackingPage.js'),
    '/profile': () => import('@pages/ProfilePage.js'),
    '/new-page': () => import('@pages/NewPage.js') // 新增路由
};
```

### 导航到页面

```javascript
import { Router } from '@utils/Router.js';

const router = new Router();
router.navigate('/new-page');
```

## 部署

### 构建优化

- 代码分割和懒加载
- 图片压缩和优化
- CSS和JS压缩
- 缓存策略配置

### 部署到生产环境

1. 构建生产版本：`npm run build`
2. 将 `dist/` 目录部署到Web服务器
3. 配置反向代理将 `/api` 请求转发到后端服务

## 贡献指南

1. Fork项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

## 许可证

MIT License