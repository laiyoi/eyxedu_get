<script setup>
// 在现有script setup中添加网页全屏功能
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Hls from 'hls.js'

// 视频元素引用
const videoRef = ref(null)
const hls = ref(null)

// 路由和导航
const route = useRoute()
const router = useRouter()

// 视频状态
const video = ref(null)
const loading = ref(true)
const error = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.7)
const isMuted = ref(false)
const isFullscreen = ref(false)
const showSubtitleSettings = ref(false)

// 网页全屏状态
const isWebFullscreen = ref(false)

// 字幕设置
const subtitleSettings = ref({
  textColor: '#FFFFFF',
  textOpacity: '100%',
  backgroundColor: '#000000',
  backgroundOpacity: '50%',
  fontSize: '100%',
  edgeStyle: 'None',
  fontFamily: 'Proportional Sans-Serif'
})

// 网页全屏切换函数
const toggleWebFullscreen = () => {
  isWebFullscreen.value = !isWebFullscreen.value
  
  if (isWebFullscreen.value) {
    document.documentElement.classList.add('webpage-fullscreen-active')
  } else {
    document.documentElement.classList.remove('webpage-fullscreen-active')
  }
}

// 监听ESC键退出全屏
const handleEscKey = (event) => {
  if (event.key === 'Escape' && isWebFullscreen.value) {
    toggleWebFullscreen()
  }
}

// 加载视频数据
onMounted(async () => {
  try {
    // 从URL参数获取视频ID
    const videoId = route.query.id
    if (!videoId) {
      throw new Error('视频ID不存在')
    }

    // 加载lesson.json文件
    const response = await fetch('lesson.json')
    if (!response.ok) {
      throw new Error('获取视频数据失败')
    }
    const videos = await response.json()

    // 根据ID查找视频
    const foundVideo = videos.find(v => v.id === parseInt(videoId))
    if (!foundVideo) {
      throw new Error('未找到该视频')
    }

    video.value = foundVideo
    loading.value = false

    // 初始化HLS播放器
    initHlsPlayer()
    
    // 添加键盘监听
    document.addEventListener('keydown', handleEscKey)
  } catch (err) {
    error.value = err.message
    loading.value = false
    ElMessage.error(error.value)
  }
})

// 初始化HLS播放器
const initHlsPlayer = () => {
  // 使用requestAnimationFrame确保DOM已更新
  requestAnimationFrame(() => {
    if (!videoRef.value) {
      console.error('Video element not found, retrying...')
      // 延迟500ms后重试
      setTimeout(initHlsPlayer, 500)
      return
    }

    // 确定视频URL
    let videoUrl = video.value.url

    if (videoUrl.endsWith('.ts')) {
      videoUrl = videoUrl.replace('.ts', '.m3u8')
    }

    // 检查浏览器是否支持HLS
    if (Hls.isSupported()) {
      // 销毁已存在的HLS实例
      if (hls.value) {
        hls.value.destroy()
        hls.value = null
      }

      // 创建新的HLS实例
      hls.value = new Hls()

      // 监听HLS错误
      hls.value.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS error:', event, data)
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              error.value = '网络错误，正在重试...'
              ElMessage.error(error.value)
              hls.value.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              error.value = '媒体错误，无法播放'
              ElMessage.error(error.value)
              break
            default:
              error.value = '视频播放出错，请稍后重试'
              ElMessage.error(error.value)
              hls.value.destroy()
              hls.value = null
              break
          }
        }
      })

      // 监听加载完成事件
      hls.value.on(Hls.Events.MANIFEST_PARSED, () => {
        console.log('Manifest parsed successfully')
        duration.value = videoRef.value.duration

        // 自动播放
        if (videoRef.value) {
          videoRef.value.play()
            .then(() => {
              isPlaying.value = true
            })
            .catch(err => {
              console.error('Auto-play failed:', err)
              error.value = '自动播放失败，请点击播放按钮'
              ElMessage.error(error.value)
            })
        }
      })

      // 绑定视频元素和HLS源
      hls.value.attachMedia(videoRef.value)
      hls.value.loadSource(videoUrl)
    } else if (videoRef.value.canPlayType('application/vnd.apple.mpegurl')) {
      // 对于支持原生HLS的浏览器
      videoRef.value.src = videoUrl
      videoRef.value.addEventListener('loadedmetadata', () => {
        duration.value = videoRef.value.duration
      })

      videoRef.value.play()
        .then(() => {
          isPlaying.value = true
        })
        .catch(err => {
          console.error('Auto-play failed:', err)
          error.value = '自动播放失败，请点击播放按钮'
          ElMessage.error(error.value)
        })
    } else {
      error.value = '您的浏览器不支持HLS视频播放'
      ElMessage.error(error.value)
    }

    // 监听视频播放事件
    videoRef.value.addEventListener('play', () => {
      isPlaying.value = true
    })

    // 监听视频暂停事件
    videoRef.value.addEventListener('pause', () => {
      isPlaying.value = false
    })

    // 定义并存储事件处理函数
    videoEventsRefs.value.handleTimeUpdate = function() {
      if (videoRef.value) {
        currentTime.value = videoRef.value.currentTime
      }
    }

    videoEventsRefs.value.handleEnded = function() {
      isPlaying.value = false
    }

    // 注册事件监听器
    videoRef.value.addEventListener('timeupdate', videoEventsRefs.value.handleTimeUpdate)
    videoRef.value.addEventListener('ended', videoEventsRefs.value.handleEnded)

    // 初始化音量
    videoRef.value.volume = volume.value
  })
}

// 创建引用存储事件处理函数
const videoEventsRefs = ref({})

// 组件卸载时清理HLS播放器和事件监听器
onUnmounted(() => {
  // 移除事件监听器
  if (videoRef.value && videoEventsRefs.value) {
    videoRef.value.removeEventListener('timeupdate', videoEventsRefs.value.handleTimeUpdate)
    videoRef.value.removeEventListener('ended', videoEventsRefs.value.handleEnded)
  }

  // 清理键盘监听
  document.removeEventListener('keydown', handleEscKey)
  document.documentElement.classList.remove('webpage-fullscreen-active')

  // 清理HLS播放器
  if (hls.value) {
    hls.value.destroy()
    hls.value = null
  }
})

// 格式化时间
const formatTime = (seconds) => {
  if (isNaN(seconds) || seconds === Infinity) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
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

// 返回视频列表
const backToList = () => {
  router.push('/')
}
</script>

<template>
  <div class="video-player-page" :class="{ 'webpage-fullscreen': isWebFullscreen }">
    <!-- 顶部导航 -->
    <header class="player-header">
      <div class="header-container">
        <button @click="backToList" class="back-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6" />
          </svg>
          返回列表
        </button>
        <div class="course-info">
          <h1 class="page-title">{{ video?.title || '视频播放' }}</h1>
          <p class="course-time">{{ formatVideoDate(video?.time) }}</p>
        </div>
        <!-- 网页全屏按钮 -->
        <button @click="toggleWebFullscreen" class="fullscreen-button" :title="isWebFullscreen ? '退出全屏' : '网页全屏'">
          <svg v-if="!isWebFullscreen" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- 主要内容区 -->
    <main class="player-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 错误信息 -->
      <div v-else-if="error" class="error-container">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#f56c6c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="m15 9-6 6" />
          <path d="m9 9 6 6" />
        </svg>
        <p>{{ error }}</p>
        <button @click="backToList" class="back-button">返回列表</button>
      </div>

      <!-- 视频和内容区域 -->
      <div v-else-if="video" class="play-lt">
        <div class="video-container">
          <div class="video-player">
            <video
              ref="videoRef"
              class="video-element"
              controls
              :autoplay="true"
            >
              您的浏览器不支持视频播放
            </video>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.video-player-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
  color: #333;
  width: 100vw;
  overflow: hidden;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 顶部导航 */
.player-header {
  background-color: #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.header-container {
  width: 100%;
  margin: 0;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 5px;
  height: 60px;
  box-sizing: border-box;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: #409eff;
  font-size: 14px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  transition: background-color 0.2s;
  height: 36px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  text-align: left;
  line-height: 1.2;
}

.course-time {
  font-size: 12px;
  color: #606266;
  margin: 0;
  line-height: 1.2;
}

/* 网页全屏按钮样式 */
.fullscreen-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
  width: 36px;
  height: 36px;
}

.fullscreen-button:hover {
  background: rgba(0, 0, 0, 0.9);
}

/* 主要内容区 */
.player-content {
  flex: 1;
  width: 100%;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.loading-container, .error-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 15px;
  padding: 20px;
}

.play-lt {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.video-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  overflow: hidden;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.video-player {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #000;
  width: 100%;
  height: 100%;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  max-width: 100%;
  max-height: 100%;
}

/* 完全按照油猴脚本实现，确保视频画面被缩放 */
.webpage-fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  background-color: black !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  margin: 0 !important;
  padding: 0 !important;
}

.webpage-fullscreen .video-container {
  width: 100% !important;
  height: 100% !important;
  background-color: black !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

.webpage-fullscreen .video-player {
  width: 100% !important;
  height: 100% !important;
  background-color: black !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

.webpage-fullscreen .video-element {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  object-position: center center !important;
  max-width: none !important;
  max-height: none !important;
}

/* 保持顶部导航栏可访问 */
.webpage-fullscreen .player-header {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7), transparent) !important;
  box-shadow: none !important;
  z-index: 10000 !important;
  transition: opacity 0.3s ease !important;
  opacity: 0 !important;
}

.webpage-fullscreen .player-header:hover {
  opacity: 1 !important;
}

.webpage-fullscreen .header-container {
  background: none !important;
  padding: 10px 20px !important;
}

.webpage-fullscreen .page-title,
.webpage-fullscreen .course-time {
  color: white !important;
}

.webpage-fullscreen .back-button {
  color: white !important;
}

.webpage-fullscreen .fullscreen-button {
  background: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

.webpage-fullscreen .fullscreen-button:hover {
  background: rgba(255, 255, 255, 0.3) !important;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .fullscreen-button {
    width: 32px;
    height: 32px;
    padding: 6px;
  }
  
  .fullscreen-button svg {
    width: 16px;
    height: 16px;
  }
}
</style>