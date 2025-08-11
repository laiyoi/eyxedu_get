<script setup>
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

    // 监听时间更新事件
    videoRef.value.addEventListener('timeupdate', () => {
      if (videoRef.value) {
        currentTime.value = videoRef.value.currentTime
      }
    })

    // 监听视频结束事件
    videoRef.value.addEventListener('ended', () => {
      isPlaying.value = false
    })

    // 初始化音量
    videoRef.value.volume = volume.value
  })
}

// 组件卸载时清理HLS播放器
onUnmounted(() => {
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
  <div class="video-player-page">
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
  min-height: 100%;
  background-color: #f5f5f5;
  color: #333;
  width: 100vw;
  max-width: 100%;
  overflow-x: hidden;
  margin: 0 auto;
  padding: 0;
}

/* 顶部导航 */
.player-header {
  background-color: #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #409eff;
  font-size: 16px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.back-button:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

.course-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  text-align: left;
}

.course-time {
  font-size: 14px;
  color: #606266;
  margin: 0;
}

/* 主要内容区 */
.player-content {
  flex: 1;
  width: 100%;
  max-width: 95%;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* 加载状态 */
.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 5px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 错误信息 */
.error-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 40px;
}

.error-container p {
  font-size: 18px;
  color: #f56c6c;
  text-align: center;
}

/* 内容包装器 */
.content-wrapper {
  display: flex;
  gap: 5px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

/* 左侧视频区域 */
.play-lt {
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

/* 视频容器 */
.video-container {
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  max-width: 100%;
  width: 100%;
  height: auto;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}


</style>