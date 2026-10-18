<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  SUBJECTS,
  GRADES,
  SORTS,
  loadLessons,
  filterLessons,
  sortLessons,
  summarize,
  highlightParts
} from '../utils/lessons'

const route = useRoute()
const router = useRouter()

/* ----------------------------- 数据 ----------------------------- */
const all = ref([])
const loading = ref(true)
const error = ref('')

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    all.value = await loadLessons()
  } catch (err) {
    error.value = err && err.message ? err.message : '课程数据加载失败'
  } finally {
    loading.value = false
  }
}

/* ----------------------------- 查询状态 ----------------------------- */
const inputValue = ref('')
const keyword = ref('')
const subject = ref('')
const grade = ref('')
const sort = ref(SORTS[0].value)
const page = ref(1)
const pageSize = ref(24)

const searchRef = ref(null)
const resultsRef = ref(null)
const focused = ref(false)

function readQuery() {
  const q = route.query
  const raw = typeof q.q === 'string' ? q.q : ''
  inputValue.value = raw
  keyword.value = raw
  subject.value = typeof q.subject === 'string' && SUBJECTS.some((s) => s.name === q.subject) ? q.subject : ''
  grade.value = typeof q.grade === 'string' && GRADES.includes(q.grade) ? q.grade : ''
  sort.value = SORTS.some((s) => s.value === q.sort) ? String(q.sort) : SORTS[0].value
  const p = Number(q.page)
  page.value = Number.isFinite(p) && p >= 1 ? Math.floor(p) : 1
}

function syncUrl() {
  const query = {}
  if (keyword.value) query.q = keyword.value
  if (subject.value) query.subject = subject.value
  if (grade.value) query.grade = grade.value
  if (sort.value !== SORTS[0].value) query.sort = sort.value
  if (page.value > 1) query.page = String(page.value)
  router.replace({ path: '/', query })
}

/* 输入防抖，避免每个字符都重算并写 URL */
let debounceTimer = null
watch(inputValue, (value) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    keyword.value = value.trim()
    page.value = 1
  }, 180)
})

watch([subject, grade, sort], () => {
  page.value = 1
})

watch([keyword, subject, grade, sort, page], syncUrl)

/* ----------------------------- 计算 ----------------------------- */
const filtered = computed(() =>
  sortLessons(
    filterLessons(all.value, {
      keyword: keyword.value,
      subject: subject.value,
      grade: grade.value
    }),
    sort.value
  )
)

const summary = computed(() => summarize(all.value))

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))

const pageItems = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

const pages = computed(() => {
  const total = totalPages.value
  const current = page.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const wanted = new Set([1, total, current, current - 1, current + 1])
  if (current <= 3) [2, 3, 4].forEach((n) => wanted.add(n))
  if (current >= total - 2) [total - 3, total - 2, total - 1].forEach((n) => wanted.add(n))

  const sorted = [...wanted].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b)
  const out = []
  let prev = 0
  for (const n of sorted) {
    if (prev && n - prev > 1) out.push('…')
    out.push(n)
    prev = n
  }
  return out
})

const hasFilter = computed(() => Boolean(keyword.value || subject.value || grade.value))

const resultText = computed(() =>
  hasFilter.value ? `筛选出 ${filtered.value.length} 节` : `共 ${filtered.value.length} 节课程`
)

watch(totalPages, (total) => {
  if (page.value > total) page.value = total
})

/* ----------------------------- 交互 ----------------------------- */
function go(target) {
  if (target < 1 || target > totalPages.value || target === page.value) return
  page.value = target
  nextTick(() => {
    const el = resultsRef.value
    if (!el) return
    const top = el.getBoundingClientRect().top + window.scrollY - 128
    window.scrollTo({ top: Math.max(top, 0), behavior: 'smooth' })
  })
}

function pickSubject(name) {
  subject.value = subject.value === name ? '' : name
}

function clearSearch() {
  inputValue.value = ''
  keyword.value = ''
  page.value = 1
  nextTick(() => searchRef.value && searchRef.value.focus())
}

function resetFilters() {
  inputValue.value = ''
  keyword.value = ''
  subject.value = ''
  grade.value = ''
  page.value = 1
}

function onKeydown(event) {
  const tag = (event.target && event.target.tagName) || ''
  const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (event.target && event.target.isContentEditable)

  if (event.key === '/' && !typing) {
    event.preventDefault()
    if (searchRef.value) searchRef.value.focus()
  } else if (event.key === 'Escape' && typing) {
    event.target.blur()
    if (event.target === searchRef.value && inputValue.value) clearSearch()
  }
}

onMounted(() => {
  readQuery()
  fetchData()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<template>
  <div class="home">
    <!-- ------------------------------ Hero ------------------------------ -->
    <section class="hero">
      <div class="container hero__inner">
        <p class="hero__eyebrow">
          <span class="dot" aria-hidden="true"></span>
          数据每周六自动更新
        </p>
        <h1 class="hero__title">亿云校课程回放</h1>
        <p class="hero__sub">
          <template v-if="!loading && !error">
            共 <strong>{{ summary.total.toLocaleString('zh-CN') }}</strong> 节课程，覆盖
            <strong>{{ summary.subjects }}</strong> 个学科，最近一次收录于
            <strong>{{ summary.latest }}</strong>。可按学科、年级或关键词检索。
          </template>
          <template v-else>正在读取课程数据…</template>
        </p>

        <div class="search" :class="{ 'search--active': focused }">
          <svg class="search__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.2-3.2" />
          </svg>
          <input
            ref="searchRef"
            v-model="inputValue"
            class="search__input"
            type="search"
            autocomplete="off"
            spellcheck="false"
            placeholder="搜索课程名，例如「高二物理」「函数」「作文」"
            aria-label="搜索课程"
            @focus="focused = true"
            @blur="focused = false"
          />
          <button v-if="inputValue" class="search__clear" type="button" aria-label="清空搜索" @click="clearSearch">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
          <kbd v-else class="search__kbd" aria-hidden="true">/</kbd>
        </div>
      </div>
    </section>

    <!-- ------------------------------ 筛选条 ------------------------------ -->
    <div class="toolbar">
      <div class="container toolbar__inner">
        <div class="chips" role="group" aria-label="按学科筛选">
          <button type="button" class="chip" :class="{ 'chip--active': subject === '' }" @click="subject = ''">
            全部
          </button>
          <button
            v-for="item in SUBJECTS"
            :key="item.name"
            type="button"
            class="chip"
            :class="{ 'chip--active': subject === item.name }"
            :style="{ '--chip': item.color }"
            @click="pickSubject(item.name)"
          >
            {{ item.name }}
          </button>
        </div>

        <div class="toolbar__selects">
          <label class="select">
            <span class="sr-only">年级</span>
            <select v-model="grade">
              <option value="">全部年级</option>
              <option v-for="g in GRADES" :key="g" :value="g">{{ g }}</option>
            </select>
          </label>
          <label class="select">
            <span class="sr-only">排序</span>
            <select v-model="sort">
              <option v-for="s in SORTS" :key="s.value" :value="s.value">{{ s.label }}</option>
            </select>
          </label>
        </div>
      </div>
    </div>

    <!-- ------------------------------ 结果 ------------------------------ -->
    <section ref="resultsRef" class="results container">
      <div class="results__head">
        <p v-if="hasFilter && !loading" class="results__count">
          {{ resultText }}
          <span class="results__hint">
            · <button type="button" class="link-btn" @click="resetFilters">清除筛选</button>
          </span>
        </p>
        <label class="select select--sm">
          <span class="sr-only">每页数量</span>
          <select v-model.number="pageSize" @change="page = 1">
            <option :value="24">每页 24</option>
            <option :value="48">每页 48</option>
            <option :value="96">每页 96</option>
          </select>
        </label>
      </div>

      <!-- 加载骨架 -->
      <div v-if="loading" class="grid" aria-hidden="true">
        <div v-for="n in 12" :key="n" class="card card--skeleton">
          <div class="sk sk--tag"></div>
          <div class="sk sk--line"></div>
          <div class="sk sk--line short"></div>
          <div class="sk sk--meta"></div>
        </div>
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="state state--error">
        <div class="state__icon">!</div>
        <h2>{{ error }}</h2>
        <p>请检查网络连接后重试；如果一直失败，可能是课程数据还没有生成。</p>
        <button type="button" class="btn btn--primary" @click="fetchData">重新加载</button>
      </div>

      <!-- 空结果 -->
      <div v-else-if="!filtered.length" class="state">
        <div class="state__icon state__icon--muted">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.2-3.2" />
          </svg>
        </div>
        <h2>没有找到符合条件的课程</h2>
        <p v-if="hasFilter">换个关键词，或者清除学科、年级筛选后再试。</p>
        <p v-else>暂时没有课程数据，请稍后重试。</p>
        <button v-if="hasFilter" type="button" class="btn" @click="resetFilters">清除筛选条件</button>
      </div>

      <!-- 卡片网格 -->
      <div v-else class="grid">
        <router-link
          v-for="item in pageItems"
          :key="item.id"
          class="card"
          :style="{ '--accent': item.color }"
          :to="{ path: '/player', query: { id: String(item.id) } }"
        >
          <div class="card__top">
            <span class="tag">{{ item.subject }}</span>
            <span v-if="item.grade" class="tag tag--ghost">{{ item.grade }}</span>
          </div>

          <h3 class="card__title">
            <template v-for="(part, i) in highlightParts(item.title, keyword)" :key="i">
              <mark v-if="part.hit">{{ part.text }}</mark>
              <span v-else>{{ part.text }}</span>
            </template>
          </h3>

          <div class="card__meta">
            <span class="card__meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <rect x="3" y="5" width="18" height="16" rx="3" />
                <path d="M8 3v4M16 3v4M3 10h18" />
              </svg>
              {{ item.date }}
            </span>
            <span v-if="item.clock" class="card__meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 2" />
              </svg>
              {{ item.clock }}
            </span>
          </div>

          <span class="card__cta">
            播放
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M8 5.5v13l11-6.5z" />
            </svg>
          </span>
        </router-link>
      </div>

      <!-- 分页 -->
      <nav v-if="!loading && !error && totalPages > 1" class="pager" aria-label="分页">
        <button type="button" class="pager__btn" :disabled="page === 1" @click="go(page - 1)">上一页</button>

        <div class="pager__pages">
          <template v-for="(p, i) in pages" :key="`${p}-${i}`">
            <span v-if="p === '…'" class="pager__gap">…</span>
            <button
              v-else
              type="button"
              class="pager__page"
              :class="{ 'pager__page--active': p === page }"
              :aria-current="p === page ? 'page' : undefined"
              @click="go(p)"
            >
              {{ p }}
            </button>
          </template>
        </div>

        <button type="button" class="pager__btn" :disabled="page === totalPages" @click="go(page + 1)">
          下一页
        </button>

        <span class="pager__info">第 {{ page }} / {{ totalPages }} 页</span>
      </nav>
    </section>
  </div>
</template>

<style scoped>
/* ------------------------------ Hero ------------------------------ */
.hero {
  position: relative;
  padding: 44px 0 26px;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  inset: -40% 40% 40% -10%;
  background: radial-gradient(closest-side, rgba(99, 102, 241, 0.22), transparent);
  filter: blur(10px);
  pointer-events: none;
}

.hero__inner {
  position: relative;
}

.hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-2);
  box-shadow: var(--shadow-sm);
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}

.hero__title {
  margin-top: 16px;
  font-size: clamp(1.7rem, 4vw, 2.7rem);
  line-height: 1.18;
  letter-spacing: -0.02em;
  font-weight: 800;
}

.hero__sub {
  margin-top: 10px;
  color: var(--text-2);
  font-size: 14px;
}

.hero__sub strong {
  color: var(--text);
  font-weight: 600;
}

/* ------------------------------ 搜索框 ------------------------------ */
.search {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 22px;
  padding: 0 16px;
  height: 56px;
  border-radius: var(--r-lg);
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
  transition: border-color 0.2s var(--ease), box-shadow 0.2s var(--ease);
}

.search--active {
  border-color: var(--brand-500);
  box-shadow: var(--shadow-md), var(--ring);
}

.search__icon {
  flex: none;
  width: 20px;
  height: 20px;
  color: var(--text-3);
}

.search__input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  background: none;
  font-size: 15px;
  color: var(--text);
}

.search__input::placeholder {
  color: var(--text-3);
}

.search__input::-webkit-search-cancel-button {
  display: none;
}

.search__clear {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: var(--surface-2);
  color: var(--text-2);
  transition: background-color 0.2s var(--ease);
}

.search__clear:hover {
  background: var(--surface-3);
}

.search__clear svg {
  width: 15px;
  height: 15px;
}

.search__kbd {
  flex: none;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text-3);
}

/* ------------------------------ 工具栏 ------------------------------ */
.toolbar {
  position: sticky;
  top: 62px;
  z-index: 30;
  padding: 10px 0;
  background: var(--bg);
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: saturate(180%) blur(12px);
  -webkit-backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--border);
}

.toolbar__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.chips {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  padding: 2px;
  scrollbar-width: none;
}

.chips::-webkit-scrollbar {
  display: none;
}

.chip {
  flex: none;
  padding: 6px 13px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  white-space: nowrap;
  transition: all 0.18s var(--ease);
}

.chip:hover {
  color: var(--text);
  border-color: var(--border-strong);
  transform: translateY(-1px);
}

.chip--active {
  color: #fff;
  background: var(--chip, var(--brand-600));
  border-color: transparent;
  box-shadow: 0 6px 14px -8px var(--chip, var(--brand-600));
}

.chip:first-child.chip--active {
  background: var(--text);
  box-shadow: none;
}

.toolbar__selects {
  display: flex;
  align-items: center;
  gap: 8px;
}

.select {
  position: relative;
  display: inline-flex;
}

.select select {
  appearance: none;
  height: 34px;
  padding: 0 30px 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s var(--ease), color 0.2s var(--ease);
}

.select select:hover {
  border-color: var(--border-strong);
  color: var(--text);
}

.select::after {
  content: '';
  position: absolute;
  right: 12px;
  top: 50%;
  width: 6px;
  height: 6px;
  border-right: 1.6px solid currentColor;
  border-bottom: 1.6px solid currentColor;
  color: var(--text-3);
  transform: translateY(-70%) rotate(45deg);
  pointer-events: none;
}

.select--sm select {
  height: 30px;
  font-size: 12.5px;
}

/* ------------------------------ 结果区 ------------------------------ */
.results {
  padding-top: 20px;
  min-height: 50vh;
}

.results__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.results__count {
  font-size: 13.5px;
  color: var(--text-2);
}

.results__head .select {
  margin-left: auto;
}

.results__hint {
  color: var(--text-3);
}

.link-btn {
  padding: 0;
  border: none;
  background: none;
  color: var(--brand-600);
  font-size: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* ------------------------------ 卡片 ------------------------------ */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(248px, 1fr));
  gap: 14px;
}

.card {
  --accent: var(--brand-500);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px 16px 14px;
  border-radius: var(--r-lg);
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  color: var(--text);
  overflow: hidden;
  transition: transform 0.22s var(--ease), box-shadow 0.22s var(--ease), border-color 0.22s var(--ease);
}

.card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--accent);
  opacity: 0.9;
}

.card:hover {
  transform: translateY(-3px);
  border-color: var(--border-strong);
  border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  box-shadow: var(--shadow-lg);
  color: var(--text);
}

.card:hover .card__cta {
  color: var(--accent);
  gap: 6px;
}

.card__top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.2px;
  color: var(--accent);
  background: var(--surface-2);
  background: color-mix(in srgb, var(--accent) 12%, transparent);
}

.tag--ghost {
  color: var(--text-3);
  background: var(--surface-2);
  font-weight: 500;
}

.card__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: -0.01em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 2.9em;
}

.card__title mark {
  background: linear-gradient(transparent 58%, rgba(99, 102, 241, 0.38) 58%);
  color: inherit;
  padding: 0;
  border-radius: 2px;
}

.card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  font-size: 12.5px;
  color: var(--text-3);
}

.card__meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.card__meta-item svg {
  width: 13px;
  height: 13px;
}

.card__cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: auto;
  padding-top: 4px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-3);
  transition: color 0.2s var(--ease), gap 0.2s var(--ease);
}

.card__cta svg {
  width: 13px;
  height: 13px;
}

/* 骨架屏 */
.card--skeleton {
  gap: 12px;
  pointer-events: none;
}

.card--skeleton::before {
  opacity: 0.35;
}

.sk {
  border-radius: 6px;
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface-3) 37%, var(--surface-2) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.sk--tag {
  width: 54px;
  height: 22px;
  border-radius: 999px;
}

.sk--line {
  height: 14px;
  width: 100%;
}

.sk--line.short {
  width: 62%;
}

.sk--meta {
  height: 12px;
  width: 45%;
  margin-top: 6px;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: 0 0;
  }
}

/* ------------------------------ 空态 / 错误 ------------------------------ */
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 56px 20px 64px;
  text-align: center;
}

.state h2 {
  font-size: 17px;
  font-weight: 650;
}

.state p {
  max-width: 420px;
  font-size: 13.5px;
  color: var(--text-2);
}

.state__icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  margin-bottom: 6px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger);
  font-size: 22px;
  font-weight: 700;
}

.state__icon--muted {
  background: var(--surface-2);
  color: var(--text-3);
}

.state__icon svg {
  width: 22px;
  height: 22px;
}

.btn {
  margin-top: 8px;
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text);
  transition: all 0.2s var(--ease);
}

.btn:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
}

.btn--primary {
  border-color: transparent;
  color: #fff;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  box-shadow: 0 10px 20px -12px var(--brand-600);
}

/* ------------------------------ 分页 ------------------------------ */
.pager {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 28px;
  padding-top: 8px;
}

.pager__btn,
.pager__page {
  height: 34px;
  min-width: 34px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  color: var(--text-2);
  transition: all 0.18s var(--ease);
}

.pager__btn:hover:not(:disabled),
.pager__page:hover {
  border-color: var(--border-strong);
  color: var(--text);
  transform: translateY(-1px);
}

.pager__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.pager__pages {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pager__page {
  padding: 0 10px;
}

.pager__page--active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  box-shadow: 0 8px 18px -10px var(--brand-600);
}

.pager__gap {
  padding: 0 4px;
  color: var(--text-3);
}

.pager__info {
  margin-left: 8px;
  font-size: 12.5px;
  color: var(--text-3);
}

/* ------------------------------ 响应式 ------------------------------ */
@media (max-width: 900px) {
  .toolbar {
    top: 56px;
  }

  .toolbar__inner {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .toolbar__selects {
    justify-content: flex-end;
  }
}

@media (max-width: 600px) {
  .hero {
    padding: 30px 0 18px;
  }

  .search {
    height: 50px;
  }

  .search__kbd {
    display: none;
  }

  .grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
  }

  .card {
    padding: 13px 13px 12px;
  }

  .card__title {
    font-size: 14px;
  }

  .pager__info {
    width: 100%;
    text-align: center;
    margin: 6px 0 0;
  }
}
</style>
