# Agenta 会议纪要生成系统 - Vue3版本

这是一个基于Vue3的智能会议纪要生成系统，将原有的HTML模板转换为现代化的Vue3单页应用。

## 项目结构

```
agenta-vue3/
├── src/
│   ├── views/           # 页面组件
│   │   ├── UploadPage.vue      # 文件上传页面
│   │   ├── TranscriptionPage.vue # 转写页面
│   │   ├── TemplatesPage.vue    # 模板选择页面
│   │   └── ResultPage.vue       # 结果展示页面
│   ├── App.vue          # 根组件
│   ├── main.js          # 应用入口
│   └── style.css        # 全局样式
├── package.json         # 项目配置
├── vite.config.js       # Vite配置
├── tailwind.config.js   # Tailwind配置
├── postcss.config.js    # PostCSS配置
└── index.html           # HTML入口
```

## 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **Vue Router 4** - 官方路由管理器
- **Vite** - 快速的前端构建工具
- **Tailwind CSS** - 实用优先的CSS框架
- **Axios** - HTTP客户端
- **Marked** - Markdown解析器
- **Highlight.js** - 代码高亮

## 功能特性

### 1. 文件上传页面 (UploadPage.vue)
- 拖拽上传支持
- 文件格式验证
- 上传进度显示
- 会议名称输入
- 实时状态反馈

### 2. 转写页面 (TranscriptionPage.vue)
- 实时进度显示
- 转写结果展示
- 文件导出功能
- 自动检查转写状态

### 3. 模板选择页面 (TemplatesPage.vue)
- 会议信息表单
- 会议类型选择
- 自定义模板上传
- 表单验证

### 4. 结果展示页面 (ResultPage.vue)
- Markdown渲染
- 代码高亮
- 文件导出
- 错误处理

## 安装和运行

### 1. 安装依赖
```bash
npm install
```

### 2. 开发模式运行
```bash
npm run dev
```

### 3. 构建生产版本
```bash
npm run build
```

### 4. 预览生产版本
```bash
npm run preview
```

## 开发说明

### 与后端API集成
项目配置了代理，将`/api`开头的请求转发到后端服务器：

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

### 样式系统
使用Tailwind CSS作为主要样式框架，并保持了原有的设计风格：

- 主色调：`#9CC932` (绿色)
- 次要色：`#f1f5f9` (浅灰)
- 中性色：`#64748b` (中性灰)

### 组件通信
- 使用Vue Router进行页面导航
- 使用Axios进行HTTP请求
- 使用Vue 3 Composition API进行状态管理

## 与原HTML版本的对比

### 优势
1. **更好的代码组织** - 组件化开发，代码更易维护
2. **响应式数据** - 自动更新UI，无需手动DOM操作
3. **更好的开发体验** - 热重载、TypeScript支持等
4. **更现代的技术栈** - Vue 3 + Vite + Tailwind CSS
5. **更好的性能** - 虚拟DOM、代码分割等优化

### 保持的功能
1. **完全相同的UI设计** - 保持原有的视觉风格
2. **相同的交互逻辑** - 文件上传、转写、模板选择等
3. **相同的API接口** - 与后端完全兼容
4. **相同的用户体验** - 拖拽上传、进度显示等

## 部署说明

### 开发环境
确保后端Flask服务器运行在`http://localhost:5000`，然后运行：
```bash
npm run dev
```

### 生产环境
1. 构建项目：
```bash
npm run build
```

2. 将`dist`目录部署到Web服务器

3. 配置后端API地址（如果需要）

## 注意事项

1. 确保后端服务器正在运行
2. 检查API接口的兼容性
3. 确保所有依赖都已正确安装
4. 在生产环境中配置正确的API地址

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！ 