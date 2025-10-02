# 静态资源目录

## 需要迁移的资源文件

请将以下文件从 `frontend_bak/resources/` 目录复制到此目录：

- `ai-brain.png` - AI大脑图标
- `app-icons.png` - 应用图标集合
- `hero-bg.png` - 首页背景图片

## 使用方式

在组件中引用资源文件：

```javascript
// 导入图片
import aiBrainIcon from '@assets/ai-brain.png';
import heroBg from '@assets/hero-bg.png';

// 在HTML中使用
const iconElement = `<img src="${aiBrainIcon}" alt="AI Brain" />`;
```

## 图片优化建议

- 使用WebP格式以获得更好的压缩率
- 为不同屏幕密度提供多个版本（1x, 2x, 3x）
- 考虑使用SVG格式的图标以获得更好的缩放效果