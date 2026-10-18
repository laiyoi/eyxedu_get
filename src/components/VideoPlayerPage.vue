<script setup>
/**
 * 课程播放页
 * ------------------------------------------------------------
 * 播放器用 ArtPlayer（通用播放器内核）+ hls.js 播放 m3u8。
 * 原始 .ts 是单个 1.3GB 的 MPEG-TS，浏览器无法直接播放，
 * 所以统一走同名 .m3u8（见 utils/lessons.js 的 toPlayUrl）。
 */
import { ref, shallowRef, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from '../i18n/artplayer-zh-cn'
import { loadLessons, findLesson, relatedLessons, neighbours } from '../utils/lessons'

const route = useRoute()
const router = useRouter()

const all = ref([])
const lesson = ref(null)
const loading = ref(true)
const error = ref('')
const playing = ref(false)
const copied = ref(false)

const stageRef = ref(null)
const art = shallowRef(null)

const related = computed(() => relatedLessons(all.value, lesson.value, 12))
const around = computed(() => neighbours(all.value, lesson.value))

const infoRows = computed(() => {
  if (!lesson.value) return []
  return [
    { label: '学科', value: lesson.value.subject },
    { label: '年级', value: lesson.value.grade || '—' },
    { label: '日期', value: lesson.value.date || '—' },
    { label: '时间', value: lesson.value.clock || '—' },
    { label: '课程编号', value: `#${lesson.value.id}` }
  ]
})

/* ----------------------------- 生命周期 ----------------------------- */
onMounted(async () => {
  try {
    all.value = await loadLessons()
  } catch (err) {
    error.value = err && err.message ? err.message : '课程数据加载失败'
    loading.value = false
    return
  }
  await openCurrent()
})

onBeforeUnmount(() => {
  destroyPlayer()
})

/* 同一页面内切换课程（侧栏点选）时复用组件，这里监听 id 变化 */
watch(
  () => route.query.id,
  async (id) => {
    if (!all.value.length) return
    if (lesson.value && String(lesson.value.id) === String(id)) return
    await openCurrent()
  }
)

/* ----------------------------- 逻辑 ----------------------------- */
async function openCurrent() {
  const id = route.query.id
  if (!id) {
    error.value = '缺少课程编号，请从课程库进入'
    loading.value = false
    return
  }

  const found = findLesson(all.value, id)
  if (!found) {
    // 编号不存在：清掉上一个课程并销毁播放器，走"未找到"整屏状态
    destroyPlayer()
    lesson.value = null
    error.value = `没有找到编号 #${id} 的课程`
    loading.value = false
    return
  }

  error.value = ''
  lesson.value = found
  loading.value = false

  await nextTick()
  await mountPlayer(found)
}

function destroyPlayer() {
  if (art.value) {
    try {
      art.value.destroy()
    } catch (e) {
      /* 忽略销毁异常 */
    }
    art.value = null
  }
  playing.value = false
}

async function mountPlayer(item) {
  destroyPlayer()

  const container = stageRef.value
  if (!container) return

  let Artplayer
  let Hls
  try {
    // 播放器与 HLS 引擎按需加载，首页不需要为它们付体积
    const [artModule, hlsModule] = await Promise.all([import('artplayer'), import('hls.js')])
    Artplayer = artModule.default
    Hls = hlsModule.default
  } catch (err) {
    error.value = '播放器脚本加载失败，请刷新页面重试'
    return
  }

  art.value = new Artplayer({
    container,
    url: item.playUrl,
    type: 'm3u8',
    theme: '#6366f1',
    lang: 'zh-cn',
    i18n: { 'zh-cn': zhCn },
    volume: 0.8,
    autoplay: true,
    autoSize: false,
    autoPlayback: true,
    autoMini: true,
    setting: true,
    hotkey: true,
    playbackRate: true,
    aspectRatio: true,
    screenshot: true,
    pip: true,
    airplay: true,
    fullscreen: true,
    fullscreenWeb: true,
    miniProgressBar: true,
    lock: true,
    gesture: true,
    fastForward: true,
    playsInline: true,
    backdrop: true,
    moreVideoAttr: {
      crossOrigin: 'anonymous',
      preload: 'auto'
    },
    customType: {
      m3u8(video, url, instance) {
        if (Hls && Hls.isSupported()) {
          const hls = new Hls({
            enableWorker: true,
            lowLatencyMode: false,
            backBufferLength: 90,
            maxBufferLength: 60
          })

          hls.loadSource(url)
          hls.attachMedia(video)

          hls.on(Hls.Events.ERROR, (event, data) => {
            if (!data || !data.fatal) return
            if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
              instance.notice.show = '网络中断，正在重连…'
              hls.startLoad()
            } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
              instance.notice.show = '媒体解码异常，正在恢复…'
              hls.recoverMediaError()
            } else {
              instance.notice.show = '视频加载失败，请刷新重试'
              hls.destroy()
            }
          })

          instance.hls = hls
          instance.on('destroy', () => hls.destroy())
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // Safari / iOS 原生 HLS
          video.src = url
        } else {
          instance.notice.show = '当前浏览器不支持 HLS 播放'
        }
      }
    }
  })

  art.value.on('ready', () => {
    playing.value = true
  })
  art.value.on('video:error', () => {
    playing.value = false
  })
}

/* ----------------------------- 交互 ----------------------------- */
function goBack() {
  const back = window.history.state && window.history.state.back
  if (back) router.back()
  else router.push('/')
}

async function copyLink() {
  const url = window.location.href
  try {
    await navigator.clipboard.writeText(url)
    copied.value = true
    setTimeout(() => (copied.value = false), 1600)
  } catch (err) {
    window.prompt('复制下面的链接：', url)
  }
}

function titleOf(item) {
  if (!item) return ''
  return item.title.length > 22 ? `${item.title.slice(0, 22)}…` : item.title
}
</script>

<template>
  <div class="player-page">
    <!-- 返回 + 面包屑 -->
    <div class="container topbar">
      <button type="button" class="back" @click="goBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round" aria-hidden="true">
          <path d="m15 18-6-6 6-6" />
        </svg>
        返回课程库
      </button>
      <p class="crumbs" v-if="lesson">
        <router-link to="/">课程库</router-link>
        <span aria-hidden="true">/</span>
        <router-link :to="{ path: '/', query: { subject: lesson.subject } }">{{ lesson.subject }}</router-link>
        <span aria-hidden="true">/</span>
        <em>{{ lesson.date }}</em>
      </p>
    </div>

    <div class="container">
      <!-- 加载中 -->
      <div v-if="loading" class="stage stage--solo">
        <div class="skeleton-stage">
          <div class="spinner"></div>
          <p>正在准备播放器…</p>
        </div>
      </div>

      <!-- 出错（无课程 / 数据失败） -->
      <div v-else-if="error && !lesson" class="stage stage--solo">
        <div class="skeleton-stage">
          <div class="badge-error">!</div>
          <p>{{ error }}</p>
          <button type="button" class="ghost-btn" @click="goBack">返回课程库</button>
        </div>
      </div>

      <!-- 正常内容 -->
      <template v-else-if="lesson">
        <header class="head">
          <div class="head__text">
            <div class="head__tags">
              <span class="tag" :style="{ '--accent': lesson.color }">{{ lesson.subject }}</span>
              <span v-if="lesson.grade" class="tag tag--ghost">{{ lesson.grade }}</span>
            </div>
            <h1 class="head__title">{{ lesson.title }}</h1>
            <p class="head__meta">
              <span>{{ lesson.date }}</span>
              <span v-if="lesson.clock">· {{ lesson.clock }}</span>
              <span>· #{{ lesson.id }}</span>
            </p>
          </div>

          <div class="head__actions">
            <button type="button" class="ghost-btn" @click="copyLink">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
                aria-hidden="true">
                <rect x="9" y="9" width="12" height="12" rx="2.5" />
                <path d="M15 5.5A2.5 2.5 0 0 0 12.5 3H5.5A2.5 2.5 0 0 0 3 5.5v7A2.5 2.5 0 0 0 5.5 15" />
              </svg>
              {{ copied ? '已复制' : '复制链接' }}
            </button>
            <a class="ghost-btn" :href="lesson.playUrl" target="_blank" rel="noopener noreferrer">m3u8 直链</a>
          </div>
        </header>

        <div class="layout">
          <div class="main-col">
            <!-- ArtPlayer 容器 -->
            <div class="stage">
              <div ref="stageRef" class="stage__art"></div>
              <div v-if="error" class="stage__mask">
                <p>{{ error }}</p>
                <button type="button" class="ghost-btn ghost-btn--light" @click="openCurrent">重试</button>
              </div>
            </div>

            <!-- 上一节 / 下一节 -->
            <div class="steppers">
              <router-link
                v-if="around.prev"
                class="stepper"
                :to="{ path: '/player', query: { id: String(around.prev.id) } }"
              >
                <span class="stepper__label">上一节</span>
                <span class="stepper__title">{{ titleOf(around.prev) }}</span>
              </router-link>
              <span v-else class="stepper stepper--empty">
                <span class="stepper__label">上一节</span>
                <span class="stepper__title">已经是第一节</span>
              </span>

              <router-link
                v-if="around.next"
                class="stepper stepper--right"
                :to="{ path: '/player', query: { id: String(around.next.id) } }"
              >
                <span class="stepper__label">下一节</span>
                <span class="stepper__title">{{ titleOf(around.next) }}</span>
              </router-link>
              <span v-else class="stepper stepper--right stepper--empty">
                <span class="stepper__label">下一节</span>
                <span class="stepper__title">已经是最后一节</span>
              </span>
            </div>

            <!-- 课程信息 -->
            <section class="info-card">
              <h2>课程信息</h2>
              <dl class="info-grid">
                <div v-for="row in infoRows" :key="row.label" class="info-row">
                  <dt>{{ row.label }}</dt>
                  <dd>{{ row.value }}</dd>
                </div>
              </dl>
              <p v-if="playing" class="info-tip">播放进度记录在本机，下次打开这门课会从上次位置继续。</p>
            </section>
          </div>

          <!-- 侧栏：同科目 -->
          <aside class="side">
            <div class="side__head">
              <h2>同科目课程</h2>
              <router-link class="side__all" :to="{ path: '/', query: { subject: lesson.subject } }">
                查看全部
              </router-link>
            </div>

            <ul v-if="related.length" class="side-list">
              <li v-for="item in related" :key="item.id">
                <router-link
                  class="side-item"
                  :class="{ 'side-item--current': item.id === lesson.id }"
                  :to="{ path: '/player', query: { id: String(item.id) } }"
                >
                  <span class="side-item__date">{{ item.date }}</span>
                  <span class="side-item__title">{{ item.title }}</span>
                </router-link>
              </li>
            </ul>
            <p v-else class="side__empty">这门学科暂时没有其它课程。</p>
          </aside>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.player-page {
  padding-top: 18px;
}

/* ------------------------------ 顶部 ------------------------------ */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 32px;
  margin-bottom: 10px;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px 6px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  color: var(--text-2);
  transition: all 0.18s var(--ease);
}

.back:hover {
  color: var(--text);
  border-color: var(--border-strong);
  transform: translateX(-2px);
}

.back svg {
  width: 16px;
  height: 16px;
}

.crumbs {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  color: var(--text-3);
  overflow: hidden;
  white-space: nowrap;
}

.crumbs a {
  color: var(--text-2);
}

.crumbs a:hover {
  color: var(--brand-600);
}

.crumbs em {
  font-style: normal;
  color: var(--text-3);
}

/* ------------------------------ 标题区 ------------------------------ */
.head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.head__tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.tag {
  --accent: var(--brand-500);
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--accent);
  background: var(--surface-2);
  background: color-mix(in srgb, var(--accent) 12%, transparent);
}

.tag--ghost {
  color: var(--text-3);
  background: var(--surface-2);
  font-weight: 500;
}

.head__title {
  font-size: clamp(1.15rem, 2.4vw, 1.6rem);
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.01em;
}

.head__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-3);
}

.head__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ghost-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  color: var(--text-2);
  transition: all 0.18s var(--ease);
}

.ghost-btn:hover {
  color: var(--text);
  border-color: var(--border-strong);
  transform: translateY(-1px);
}

.ghost-btn svg {
  width: 15px;
  height: 15px;
}

.ghost-btn--light {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

/* ------------------------------ 布局 ------------------------------ */
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
  align-items: start;
}

.main-col {
  min-width: 0;
}

/* ------------------------------ 播放器 ------------------------------ */
.stage {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: var(--r-lg);
  overflow: hidden;
  background: #07080d;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border);
}

.stage__art {
  width: 100%;
  height: 100%;
}

.stage__mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
  color: #fff;
  background: rgba(7, 8, 13, 0.82);
  backdrop-filter: blur(4px);
}

.stage--solo {
  display: grid;
  place-items: center;
  margin-bottom: 18px;
}

.skeleton-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  color: var(--text-2);
  font-size: 13.5px;
}

.spinner {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 3px solid rgba(99, 102, 241, 0.25);
  border: 3px solid color-mix(in srgb, var(--brand-500) 25%, transparent);
  border-top-color: var(--brand-600);
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.badge-error {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.14);
  color: var(--danger);
  font-size: 20px;
  font-weight: 700;
}

/* ------------------------------ 上下节 ------------------------------ */
.steppers {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 12px;
}

.stepper {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 11px 14px;
  border-radius: var(--r-md);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  transition: all 0.18s var(--ease);
  min-width: 0;
}

.stepper:hover {
  border-color: var(--brand-500);
  color: var(--text);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stepper--right {
  text-align: right;
  align-items: flex-end;
}

.stepper--empty {
  opacity: 0.55;
  pointer-events: none;
}

.stepper__label {
  font-size: 11.5px;
  color: var(--text-3);
  letter-spacing: 0.4px;
}

.stepper__title {
  font-size: 13.5px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* ------------------------------ 信息卡 ------------------------------ */
.info-card {
  margin-top: 14px;
  padding: 18px;
  border-radius: var(--r-lg);
  border: 1px solid var(--border);
  background: var(--surface);
}

.info-card h2 {
  font-size: 14px;
  font-weight: 650;
  margin-bottom: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px 18px;
  margin: 0;
}

.info-row dt {
  font-size: 11.5px;
  color: var(--text-3);
  margin-bottom: 2px;
}

.info-row dd {
  margin: 0;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text);
}

.info-tip {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
  font-size: 12px;
  color: var(--text-3);
}

/* ------------------------------ 侧栏 ------------------------------ */
.side {
  position: sticky;
  top: 78px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: var(--r-lg);
  border: 1px solid var(--border);
  background: var(--surface);
  max-height: calc(100vh - 100px);
  overflow: hidden;
}

.side__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.side__head h2 {
  font-size: 14px;
  font-weight: 650;
}

.side__all {
  font-size: 12px;
  color: var(--brand-600);
}

.side-list {
  list-style: none;
  margin: 0;
  padding: 0 4px 0 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.side-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 8px 10px;
  border-radius: var(--r-sm);
  color: var(--text);
  transition: background-color 0.15s var(--ease);
}

.side-item:hover {
  background: var(--surface-2);
  color: var(--text);
}

.side-item--current {
  background: var(--brand-50);
  color: var(--brand-700);
}

.side-item__date {
  font-size: 11px;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}

.side-item__title {
  font-size: 13px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.side__empty {
  font-size: 12.5px;
  color: var(--text-3);
}

/* ------------------------------ 响应式 ------------------------------ */
@media (max-width: 1080px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .side {
    position: static;
    max-height: none;
  }

  .side-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 4px;
  }
}

@media (max-width: 640px) {
  .topbar .crumbs {
    display: none;
  }

  .head__actions {
    width: 100%;
  }

  .head__actions .ghost-btn {
    flex: 1;
    justify-content: center;
  }

  .steppers {
    grid-template-columns: 1fr;
  }
}
</style>
