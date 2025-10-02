import { defineConfig } from 'vite';

export default defineConfig({
  // 开发服务器配置
  server: {
    port: 3000,
    host: true,
    proxy: {
      // 代理API请求到后端服务器
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    minify: 'terser',
    sourcemap: false,
    rollupOptions: {
      output: {
        // 代码分割配置
        manualChunks: {
          // 第三方库单独打包
          vendor: ['animejs'],
          // 工具函数单独打包
          utils: ['./src/utils/index.js']
        },
        // 文件命名规则
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    // 构建优化
    chunkSizeWarningLimit: 1000,
    target: 'es2015'
  },
  
  // 预览服务器配置
  preview: {
    port: 4173,
    host: true
  },
  
  // 测试配置
  test: {
    globals: true,
    environment: 'jsdom'
  },
  
  // 路径解析
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@pages': '/src/pages',
      '@services': '/src/services',
      '@utils': '/src/utils',
      '@stores': '/src/stores',
      '@styles': '/src/styles',
      '@assets': '/src/assets'
    }
  },
  
  // 环境变量前缀
  envPrefix: 'VITE_',
  
  // CSS配置
  css: {
    postcss: './postcss.config.js'
  }
});