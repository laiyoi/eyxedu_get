<script setup>
import { ref, onMounted, computed } from 'vue'

// 视频数据状态
const videoData = ref(null)
const loading = ref(true)
const error = ref(null)
const activeCategory = ref('all')

// 加载视频数据
onMounted(async () => {
  try {
    const response = await fetch('/eyxedu_get/videos.json')
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    videoData.value = await response.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})

// 过滤当前分类的视频
const filteredVideos = computed(() => {
  if (!videoData.value) return []
  if (activeCategory.value === 'all') {
    return videoData.value.categories.flatMap(category => category.videos)
  }
  const category = videoData.value.categories.find(cat => cat.id === activeCategory.value)
  return category ? category.videos : []
})

// 获取分类颜色
const getCategoryColor = (categoryId) => {
  const colorMap = {
    'tech': '#f56c6c',
    'design': '#409eff',
    'all': '#67c23a'
  }
  return colorMap[categoryId] || '#606266'
}

// 获取分类背景颜色
const getCategoryBgColor = (categoryId) => {
  const bgColorMap = {
    'tech': '#fef0f0',
    'design': '#ecf5ff',
    'all': '#f0f9eb'
  }
  return bgColorMap[categoryId] || '#f4f4f5'
}

// 获取分类名称
const getCategoryName = (categoryId) => {
  if (categoryId === 'all') return '全部'
  if (videoData.value) {
    const category = videoData.value.categories.find(cat => cat.id === categoryId)
    if (category) return category.name
  }
  return '未知分类'
}

</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>视频导航网站</h1>
      <p>发现优质视频内容</p>
    </header>

    <main class="main-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <div class="el-loading-spinner">
          <svg viewBox="25 25 50 50" class="circular">
            <circle cx="50" cy="50" r="20" fill="none" class="path"></circle>
          </svg>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-else-if="error" class="error">错误: {{ error }}</div>

      <!-- 视频内容 -->
      <div v-else class="video-content">
        <!-- 分类导航 -->
        <div class="categories">
          <button
            :class="{ 'active': activeCategory === 'all' }"
            @click="activeCategory = 'all'"
          >
            全部
          </button>
          <button
            v-for="category in videoData.categories"
            :key="category.id"
            :class="{ 'active': activeCategory === category.id }"
            @click="activeCategory = category.id"
          >
            {{ category.name }}
          </button>
        </div>

        <!-- 视频列表 -->
        <div class="review-list flex-wrap">
          <div v-for="video in filteredVideos" :key="video.id" class="el-card pointer is-always-shadow">
            <div class="el-card__body">
              <div class="review-wrap">
                <img :src="video.thumbnail" :alt="video.title" class="thumbnail">
                <div class="review-info">
                  <h3 class="review-title">{{ video.title }}</h3>
                  <div class="review-course-info">
                    <span class="el-tag el-tag--success el-tag--medium el-tag--light"
                      :style="{ 'margin-right': '17px', 'color': getCategoryColor(activeCategory.value), 'background': getCategoryBgColor(activeCategory.value), 'border-color': getCategoryBgColor(activeCategory.value) }"
                    >
                      {{ getCategoryName(activeCategory.value) }}
                    </span>
                    <span style="font-size: 14px; margin-right: 10px;">高中</span>
                    <span style="font-size: 14px;">高二</span>
                  </div>
                  <div class="review-opea flex-sp-between">
                    <div class="name">
                      <span style="font-size: 14px; font-weight: bold; margin-bottom: 5px;">{{ video.teacher }}</span>
                      <div style="font-size: 12px;">
                        <span style="margin-right: 5px;">{{ video.date }}</span>
                        <span>{{ video.time }}</span>
                      </div>
                    </div>
                    <div class="review-btn">
                      <a :href="video.url" target="_blank" rel="noopener noreferrer">
                        <button type="button" class="el-button el-button--primary el-button--small">
                          <span>立即回看</span>
                        </button>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="footer">
      <p>© {{ new Date().getFullYear() }} 视频导航网站 | 托管于 GitHub Pages</p>
    </footer>
  </div>
</template>

<style scoped>
/* 基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Arial', sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

/* 头部样式 */
.header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px 0;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 28px;
  margin-bottom: 10px;
  color: #333;
}

.header p {
  font-size: 16px;
  color: #666;
}

/* 主要内容区样式 */
.main-content {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 加载状态样式 */
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.el-loading-spinner {
  width: 50px;
  height: 50px;
}

.circular {
  animation: rotate 2s linear infinite;
  height: 50px;
  width: 50px;
}

.path {
  stroke: #409eff;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
  stroke-width: 2;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

/* 错误信息样式 */
.error {
  text-align: center;
  color: #f56c6c;
  padding: 20px;
  background-color: #fef0f0;
  border-radius: 4px;
  margin-bottom: 20px;
}

/* 分类导航样式 */
.categories {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.categories button {
  padding: 8px 16px;
  background-color: #f5f5f5;
  border: 1px solid #dcdcdc;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.categories button:hover {
  background-color: #e6f7ff;
  border-color: #91cbff;
}

.categories button.active {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
}

/* 视频列表样式 */
.review-list {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  justify-content: flex-start;
}

.el-card {
  width: calc(25% - 24px);
  min-width: 280px;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

@media (max-width: 1200px) {
  .el-card {
    width: calc(33.333% - 24px);
  }
}

@media (max-width: 900px) {
  .el-card {
    width: calc(50% - 24px);
  }
}

@media (max-width: 600px) {
  .el-card {
    width: 100%;
  }
}

.el-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.el-card__body {
  padding: 0;
}

.review-wrap {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.thumbnail {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.review-info {
  padding: 15px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.review-title {
  font-size: 18px;
  margin-bottom: 10px;
  color: #333;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.review-course-info {
  margin-bottom: 10px;
}

.el-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.review-opea {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: auto;
  padding-top: 10px;
}

.name {
  font-size: 12px;
  color: #666;
}

.review-btn button {
  padding: 6px 12px;
  font-size: 12px;
}

.el-button {
  display: inline-block;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  background: #409eff;
  border: 1px solid #409eff;
  color: #fff;
  -webkit-appearance: none;
  text-align: center;
  box-sizing: border-box;
  outline: none;
  margin: 0;
  transition: 0.1s;
  font-weight: 500;
  padding: 12px 20px;
  font-size: 14px;
  border-radius: 4px;
}

.el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
  color: #fff;
}

.el-button--small {
  padding: 9px 15px;
  font-size: 12px;
  border-radius: 3px;
}

/* 底部样式 */
.footer {
  text-align: center;
  margin-top: 30px;
  padding: 20px 0;
  color: #666;
  font-size: 14px;
}
</style>
