<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

// 创建router引用
const router = useRouter()

// 视频数据状态
const videoData = ref(null)
const loading = ref(true)
const error = ref(null)

// 分页状态
const currentPage = ref(1)
const itemsPerPage = ref(18) // 每页显示18个视频 (6列x3行)

// 加载视频数据
onMounted(async () => {
  try {
    // 使用相对路径请求lesson.json
    const response = await fetch('lesson.json')
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

// 视频列表数据
const videos = computed(() => {
  return videoData.value || []
})

// 分页计算
const paginatedVideos = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage.value
  return videos.value.slice(startIndex, startIndex + itemsPerPage.value)
})

const totalPages = computed(() => {
  return Math.ceil(videos.value.length / itemsPerPage.value)
})

// 分页方法
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 格式化视频日期
const formatVideoDate = (timeStr) => {
  if (!timeStr) return ''
  const parts = timeStr.split(' ')
  if (parts.length < 2) return timeStr
  const date = parts[0]
  const time = parts[1].replace(/-/g, ':')
  return `${date} ${time}`
}

</script>

<template>
  <div class="home-page">
    <header class="header">
      <h1>视频导航网站</h1>
      <p>发现优质视频内容</p>
    </header>

    <div class="main-content">
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
        <!-- 视频列表 -->
        <div class="review-list flex-wrap">
          <div v-for="video in paginatedVideos" :key="video.id" class="el-card pointer is-always-shadow">
            <div class="el-card__body" >
              <div class="review-wrap">
                <div class="review-info">
                  <h3 class="review-title">{{ video.title }}</h3>
                  <div class="review-course-info">
                    <span style="font-size: 14px; margin-right: 10px;">时间: {{ formatVideoDate(video.time) }}</span>
                  </div>
                  <div class="review-opea flex-sp-between">
                    <div class="review-btn">
                      <button @click="router.push({ path: '/player', query: { id: video.id } })" type="button" class="el-button el-button--primary el-button--small">
                        <span>立即观看</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页控件 -->
      <div class="pagination-container" v-if="totalPages > 1">
        <div class="pagination">
          <button @click="prevPage" :disabled="currentPage === 1" class="pagination-btn">上一页</button>
          <div v-for="page in totalPages" :key="page" class="pagination-item" :class="{ 'active': page === currentPage }" @click="goToPage(page)">{{ page }}</div>
          <button @click="nextPage" :disabled="currentPage === totalPages" class="pagination-btn">下一页</button>
        </div>
        <div class="pagination-info">当前第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</div>
      </div>
    </div>

    <footer class="footer">
      <p>© {{ new Date().getFullYear() }} 视频导航网站</p>
    </footer>
  </div>
</template>

<style scoped>
/* 基础样式 */

.home-page { width: 100%; margin: 0; padding: 20px; }

/* 头部样式 */
.header {
  text-align: center;
  margin-bottom: 30px;
  padding: 10px 0;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header h1 { font-size: clamp(1.5rem, 3vw, 2.5rem); margin-bottom: 8px; color: #333; font-weight: 700; }

.header p { font-size: clamp(1rem, 2vw, 1.25rem); color: #666; }

/* 主要内容区样式 */
.main-content {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 100%;
  width: 100%;
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

@keyframes rotate {}
@keyframes dash {}

/* 错误信息样式 */
.error {
  text-align: center;
  color: #f56c6c;
  padding: 20px;
  background-color: #fef0f0;
  border-radius: 4px;
  margin-bottom: 20px;
}

/* 视频列表样式 */
.review-list { display: flex; width: 100%; flex-wrap: wrap; margin-right: -1.5%; gap: 5px; }

.el-card { width: 16% ; aspect-ratio: 2/1; border-radius: 8px; overflow: hidden; transition: all 0.3s; box-sizing: border-box; display: flex; flex-direction: column} /* 默认6列，16:9宽高比 */

.el-card__body { padding: 5%; flex-grow: 1; display: flex; flex-direction: column}

.review-info { flex-grow: 1; display: flex; flex-direction: column}

.review-title { font-size: clamp(0.7rem, 2vw, 1rem); margin-bottom: 8px; display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden}

.review-course-info { font-size: clamp(0.6rem, 1.5vw, 0.8rem); margin-bottom: 8px}

.el-button--small { padding: 4px 10px; font-size: clamp(0.6rem, 1.5vw, 0.8rem)}

/* 分页控件样式 */
.pagination-container {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 5px;
}

.pagination-btn {
  padding: 6px 12px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-item {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-item.active {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
}

.pagination-info { font-size: clamp(0.7rem, 1.5vw, 0.9rem); color: #666; }


</style>