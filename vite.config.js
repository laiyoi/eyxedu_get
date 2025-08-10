import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  // 开发环境使用相对路径，便于直接打开index.html
  // 部署到GitHub Pages时改为 '/eyxedu_get/'
  base: './',
  plugins: [vue()],
})
