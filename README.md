# 视频导航网站

一个基于Vue 3的视频导航网站，适用于GitHub Pages，能够读取JSON中的视频数据并展示。

## 功能特点

- 从JSON文件加载视频数据
- 分类导航功能
- 视频卡片展示，包含缩略图、标题和描述
- 响应式设计，适应不同屏幕尺寸
- 点击视频卡片跳转到对应视频页面

## 项目结构

```
.\
├── public\
│   └── videos.json  # 视频数据文件
├── src\
│   ├── App.vue      # 主应用组件
│   ├── main.js      # 入口文件
│   └── assets\      # 静态资源
├── index.html       # 入口HTML
├── vite.config.js   # Vite配置文件
└── package.json     # 项目依赖
```

## 本地开发

1. 安装依赖

```bash
npm install
```

2. 启动开发服务器

```bash
npm run dev
```

3. 在浏览器中打开 http://localhost:5173

## 部署到GitHub Pages

1. 构建项目

```bash
npm run build
```

2. 部署到GitHub Pages

可以使用gh-pages工具部署：

```bash
# 安装gh-pages
npm install -g gh-pages

# 部署dist目录到gh-pages分支
gh-pages -d dist
```

3. 在GitHub仓库设置中，将Pages的源设置为gh-pages分支

## 自定义视频数据

编辑`public/videos.json`文件，按照以下格式添加或修改视频数据：

```json
{
  "categories": [
    {
      "id": "category-id",
      "name": "分类名称",
      "videos": [
        {
          "id": "video-id",
          "title": "视频标题",
          "description": "视频描述",
          "thumbnail": "缩略图URL",
          "url": "视频URL"
        }
      ]
    }
  ]
}
```

## 技术栈

- Vue 3
- Vite
- CSS (响应式设计)
