<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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
const showDemo = ref(false) // 控制演示框展开状态
const demoVideo = ref(null) // 视频播放器引用

// 监听showDemo变化，收回时暂停视频
watch(showDemo, (newVal) => {
  if (!newVal && demoVideo.value) {
    demoVideo.value.pause()
  }
})

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

// 可见页码计算（总长度恒为15）
const visiblePages = computed(() => {
  const pages = []
  const totalDisplayLength = 15
  let availableNumberSlots = totalDisplayLength - 2 // 减去第一页和最后一页，剩下13个数字槽位

  // 始终添加第一页
  pages.push(1)

  // 如果总页数 <= totalDisplayLength，直接显示所有页码
  if (totalPages.value <= totalDisplayLength) {
    for (let i = 2; i < totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // 计算当前页应该显示的范围
    let startPage, endPage
    let hasLeftEllipsis = false
    let hasRightEllipsis = false

    // 如果当前页靠近前面（前11页）
    if (currentPage.value <= 11) {
      startPage = 2
      endPage = 12 // 显示1-12页，共12个数字页码
      hasRightEllipsis = true
    }
    // 如果当前页靠近后面（后11页）
    else if (currentPage.value >= totalPages.value - 10) {
      startPage = totalPages.value - 11
      endPage = totalPages.value - 1
      hasLeftEllipsis = true
    }
    // 如果当前页在中间
    else {
      startPage = currentPage.value - 5 // 当前页前5页
      endPage = currentPage.value + 5 // 当前页后5页
      hasLeftEllipsis = true
      hasRightEllipsis = true
    }

    // 添加左侧省略号
    if (hasLeftEllipsis) {
      pages.push('...')
    }

    // 添加数字页码
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i)
    }

    // 添加右侧省略号
    if (hasRightEllipsis) {
      pages.push('...')
    }
  }

  // 始终添加最后一页
  if (totalPages.value > 1) {
    pages.push(totalPages.value)
  }

  // 确保总长度为15（防止异常情况）
  if (pages.length > totalDisplayLength) {
    // 保留第一页、最后一页和中间的13个元素
    const middlePart = pages.slice(1, -1)
    pages.splice(1, pages.length - 2, ...middlePart.slice(0, 13))
  } else if (pages.length < totalDisplayLength) {
    // 如果不足15个，尝试在合适位置添加省略号
    if (pages.indexOf('...') === -1 && pages.length > 2) {
      // 在第二位置添加省略号
      pages.splice(1, 0, '...')
    }
  }

  // 确保总长度为16，如果不足则填充
  while (pages.length < totalDisplayLength) {
    // 尝试在合适位置插入省略号
    if (pages.indexOf('...') === -1 && pages.length > 2) {
      // 在第二位置添加省略号
      pages.splice(1, 0, '...')
    } else {
      // 如果已有省略号或无法添加，则重复最后一个数字页码前的数字
      const lastNumIndex = pages.findLastIndex(item => typeof item === 'number')
      if (lastNumIndex > 0 && lastNumIndex < pages.length - 1) {
        pages.splice(lastNumIndex, 0, pages[lastNumIndex] - 1)
      } else {
        break // 无法继续填充
      }
    }
  }

  // 如果超过16，则截断（理论上不应该发生）
  if (pages.length > totalDisplayLength) {
    // 保留第一页、最后一页和中间的14个元素
    const middlePart = pages.slice(1, -1)
    while (pages.length > totalDisplayLength) {
      // 优先移除省略号
      const ellipsisIndex = middlePart.indexOf('...')
      if (ellipsisIndex !== -1) {
        middlePart.splice(ellipsisIndex, 1)
      } else if (middlePart.length > 0) {
        // 如果没有省略号，则移除中间的页码
        const removeIndex = Math.floor(middlePart.length / 2)
        middlePart.splice(removeIndex, 1)
      } else {
        break
      }
    }
    pages.splice(1, pages.length - 2, ...middlePart)
  }

  return pages
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
      <h1>亿云校索引</h1>
      <p>关注永雏塔菲谢谢喵</p>
    </header>

    <div class="main-content">
      <!-- 本地部署演示区域 -->
      <div class="demo-section">
        <div class="demo-header" @click="showDemo = !showDemo">
          <h3>查看本地部署演示</h3>
          <span class="expand-icon">{{ showDemo ? '▼' : '▶' }}</span>
        </div>
        
        <div v-show="showDemo" class="demo-content">
          <video 
            ref="demoVideo"
            class="demo-video"
            controls
            preload="metadata"
            src="https://upos-sz-estghw.bilivideo.com/upgcxcode/17/15/32056281517/32056281517-1-192.mp4?e=ig8euxZM2rNcNbRahWdVhwdlhWu1hwdVhoNvNC8BqJIzNbfq9rVEuxTEnE8L5F6VnEsSTx0vkX8fqJeYTj_lta53NCM=&nbs=1&mid=3493273117133651&trid=3676deb1b4224dd5a31f7b2261b5f1fT&os=estghw&og=hw&platform=html5&deadline=1756572631&oi=0x24088270406d62c05d1441a8bfc4fa2b&uipk=5&gen=playurlv3&upsig=f4916d784d31399fab169e7282ff8fc8&uparams=e,nbs,mid,trid,os,og,platform,deadline,oi,uipk,gen&bvc=vod&nettype=0&bw=1388057&agrr=0&buvid=&build=0&dl=0&f=T_0_0&mobi_app=&orderid=0,1"
          >
            您的浏览器不支持视频播放。
          </video>
          <div class="demo-description">
            <p>这是一个本地部署演示视频，展示了如何搭建和使用亿云校视频系统。</p>
          </div>
        </div>
      </div>

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
          <div v-for="page in visiblePages" :key="page" class="pagination-item" :class="{ 'active': page === currentPage }" @click="typeof page === 'number' ? goToPage(page) : null">
            {{ page }}
          </div>
          <button @click="nextPage" :disabled="currentPage === totalPages" class="pagination-btn">下一页</button>
        </div>
        <div class="pagination-info">当前第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</div>
      </div>
    </div>

    <footer class="footer">
      <p>© {{ new Date().getFullYear() }} 亿云校</p>
    </footer>
  </div>
</template>

<style scoped>
/* 基础样式 */

.home-page { 
  width: 100vw; 
  height: 100vh;
  margin: 0; 
  padding: 0; 
  box-sizing: border-box;
  overflow: hidden; /* 完全隐藏滚动 */
  display: flex;
  flex-direction: column;
}

/* 头部样式 */
.header {
  text-align: center;
  margin: 0; /* 移除所有margin */
  padding: 6px 0; /* 进一步减少padding */
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* 减小阴影 */
  border-radius: 0; /* 移除圆角 */
  flex-shrink: 0;
}

.header h1 { 
  font-size: clamp(1.2rem, 2vw, 1.8rem); /* 进一步减小字体 */
  margin: 0; 
  color: #333; 
  font-weight: 700; 
  line-height: 1.2;
}

.header p { 
  font-size: clamp(0.8rem, 1.2vw, 1rem); /* 减小字体 */
  color: #666; 
  margin: 0; 
  line-height: 1.2;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  background-color: #fff;
  padding: 10px; /* 减少padding */
  overflow-y: auto; /* 只在内容区域允许垂直滚动 */
  box-sizing: border-box;
}

/* 视频列表样式 */
.review-list { 
  display: flex; 
  width: 100%; 
  flex-wrap: wrap; 
  gap: 6px; 
  margin: 0;
  padding: 0;
}

.el-card { 
  width: calc(16.666% - 5px); 
  aspect-ratio: 16/9; /* 调整为16:9，更合适的视频比例 */
  border-radius: 6px; /* 减小圆角 */
  overflow: hidden; 
  transition: all 0.3s; 
  box-sizing: border-box; 
  display: flex; 
  flex-direction: column;
  margin: 0;
}

/* 视频卡片内部样式优化 */
.el-card__body { 
  padding: 8px; 
  flex-grow: 1; 
  display: flex; 
  flex-direction: column;
}

.review-info { 
  flex-grow: 1; 
  display: flex; 
  flex-direction: column;
  justify-content: space-between;
}

.review-title { 
  font-size: clamp(0.85rem, 2vw, 1rem); /* 增大标题字体 */
  margin-bottom: 4px; 
  display: -webkit-box; 
  -webkit-box-orient: vertical; 
  overflow: hidden;
  line-height: 1.3; /* 稍微增加行高 */
  font-weight: 600; /* 增加字重 */
  color: #2c3e50; /* 更深的颜色 */
}

.review-course-info { 
  font-size: clamp(0.7rem, 1.5vw, 0.8rem); /* 时间信息字体稍小 */
  margin-bottom: 6px;
  line-height: 1.2;
  color: #7f8c8d; /* 灰色 */
}

.el-button--small { 
  padding: 4px 8px; /* 稍微增大按钮 */
  font-size: clamp(0.65rem, 1.3vw, 0.75rem); /* 增大按钮字体 */
  line-height: 1.2;
  font-weight: 500; /* 增加按钮字重 */
}

/* 分页控件样式 */
.pagination-container {
  margin-top: 10px; /* 减少顶部margin */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 3px; /* 减少间距 */
  max-width: 100%;
  overflow-x: auto;
  padding-bottom: 2px;
  justify-content: center;
}

.pagination-btn {
  padding: 3px 8px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8rem;
}

.pagination-item {
  padding: 3px 6px;
  border: 1px solid #ddd;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8rem;
}

.pagination-info { 
  font-size: clamp(0.65rem, 1.2vw, 0.8rem); 
  color: #666; 
}

/* 本地部署演示区域样式 */
.demo-section {
  margin-bottom: 15px; /* 减少底部margin */
  border: 1px solid #e0e0e0;
  border-radius: 6px; /* 减小圆角 */
  overflow: hidden;
  background-color: #fafafa;
  flex-shrink: 0;
}

.demo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px; /* 减少padding */
  background-color: #f5f5f5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.demo-header h3 {
  margin: 0;
  font-size: 1rem; /* 减小字体 */
  color: #333;
}

.demo-content {
  padding: 15px; /* 减少padding */
  background-color: white;
}

.demo-video {
  width: 100%;
  max-width: 600px; /* 减小最大宽度 */
  height: auto;
  border-radius: 3px;
  margin-bottom: 10px;
}

.demo-description p {
  margin: 0;
  color: #666;
  font-size: 0.8rem; /* 减小字体 */
  line-height: 1.3;
}
</style>