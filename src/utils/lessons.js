/**
 * 课程数据层
 * ------------------------------------------------------------
 * lesson.json 的结构是 { title, id, time, url }：
 *   title: "高二语文：习题课"
 *   time:  "2025.07.16 15-07-16-10"
 *   url:   .../ynfz6_18752181_24630107.ts   ← 单个 1.3GB 的 MPEG-TS
 *
 * CDN 同时提供同名的 .m3u8（VOD 播放列表，用 EXT-X-BYTERANGE 指向那个 .ts），
 * CORS 为 *，所以浏览器必须走 m3u8 + HLS，不能直接播放 .ts。
 */

export const SUBJECTS = [
  { name: '语文', color: '#f43f5e' },
  { name: '数学', color: '#6366f1' },
  { name: '英语', color: '#0ea5e9' },
  { name: '物理', color: '#8b5cf6' },
  { name: '化学', color: '#14b8a6' },
  { name: '生物', color: '#22c55e' },
  { name: '历史', color: '#f59e0b' },
  { name: '地理', color: '#06b6d4' },
  { name: '政治', color: '#ec4899' },
  { name: '其他', color: '#64748b' }
]

export const GRADES = ['高一', '高二', '高三', '初一', '初二', '初三']

export const SORTS = [
  { value: 'time-desc', label: '最新在前' },
  { value: 'time-asc', label: '最早在前' },
  { value: 'title', label: '按标题排序' }
]

const SUBJECT_COLOR = SUBJECTS.reduce((acc, cur) => {
  acc[cur.name] = cur.color
  return acc
}, {})

// 长的放前面，避免"语文"被"文"之类误伤（这里列的都是两字词，保持显式顺序即可）
const SUBJECT_RE = new RegExp(SUBJECTS.filter((s) => s.name !== '其他').map((s) => s.name).join('|'))
const GRADE_RE = /(高[一二三]|初[一二三])/

export function subjectColor(name) {
  return SUBJECT_COLOR[name] || SUBJECT_COLOR['其他']
}

/**
 * 把 .ts 换成同名的 .m3u8；其它后缀（mp4 之类）原样返回。
 */
export function toPlayUrl(url) {
  if (!url) return ''
  return String(url).replace(/\.ts(\?[^#]*)?(#.*)?$/i, '.m3u8$1$2')
}

/**
 * "2025.07.16 15-07-16-10" → { date: "2025.07.16", clock: "15:07", stamp }
 * time 字段本身不规范（时-分-秒-毫秒用减号连接），这里只取时和分。
 */
function parseTime(timeStr) {
  const raw = String(timeStr || '').trim()
  const [datePart = '', timePart = ''] = raw.split(/\s+/)
  const dateMatch = datePart.match(/^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})$/)
  const date = dateMatch
    ? `${dateMatch[1]}.${String(dateMatch[2]).padStart(2, '0')}.${String(dateMatch[3]).padStart(2, '0')}`
    : datePart

  let clock = ''
  const timeMatch = timePart.match(/^(\d{1,2})[-:](\d{1,2})/)
  if (timeMatch) {
    clock = `${String(timeMatch[1]).padStart(2, '0')}:${String(timeMatch[2]).padStart(2, '0')}`
  }

  let stamp = 0
  if (dateMatch) {
    const [, y, m, d] = dateMatch
    stamp = new Date(Number(y), Number(m) - 1, Number(d), timeMatch ? Number(timeMatch[1]) : 0, timeMatch ? Number(timeMatch[2]) : 0).getTime()
  }

  return { date, clock, stamp }
}

/**
 * 把 lesson.json 的一条原始记录规范化，顺带抽学科、年级、日期。
 */
export function parseLesson(raw) {
  const title = String(raw && raw.title ? raw.title : '').trim()
  const subjectMatch = title.match(SUBJECT_RE)
  const gradeMatch = title.match(GRADE_RE)
  const { date, clock, stamp } = parseTime(raw && raw.time)

  return {
    id: Number(raw && raw.id),
    title,
    time: String((raw && raw.time) || ''),
    url: String((raw && raw.url) || ''),
    playUrl: toPlayUrl(raw && raw.url),
    subject: subjectMatch ? subjectMatch[0] : '其他',
    grade: gradeMatch ? gradeMatch[0] : '',
    date,
    clock,
    stamp,
    color: subjectColor(subjectMatch ? subjectMatch[0] : '其他')
  }
}

let cache = null

/**
 * 加载并缓存课程数据。首页和播放页共用同一个 Promise，不会重复请求。
 */
export function loadLessons() {
  if (cache) return cache

  cache = (async () => {
    const res = await fetch('lesson.json', { cache: 'no-cache' })
    if (!res.ok) throw new Error(`课程数据加载失败（HTTP ${res.status}）`)
    const raw = await res.json()
    if (!Array.isArray(raw)) throw new Error('课程数据格式不正确')

    // 原始数据里有重复：2096 条记录只有 1956 个唯一 id，最多重复 4 次。
    // 重复 id 会让 v-for 的 :key 撞车，也就会在列表里出现同一节课好几次，这里按 id 去重。
    const seen = new Set()
    const list = []
    for (const entry of raw) {
      const item = parseLesson(entry)
      if (!Number.isFinite(item.id) || seen.has(item.id)) continue
      seen.add(item.id)
      list.push(item)
    }

    list.sort((a, b) => b.stamp - a.stamp)
    return list
  })()

  // 失败时清掉缓存，方便"重试"按钮真的重新请求
  cache.catch(() => {
    cache = null
  })

  return cache
}

export function findLesson(list, id) {
  const target = Number(id)
  return list.find((item) => item.id === target) || null
}

/* ------------------------------------------------------------------ */
/* 搜索                                                                */
/* ------------------------------------------------------------------ */

export function tokenize(keyword) {
  return String(keyword || '')
    .toLowerCase()
    .split(/[\s,，、]+/)
    .map((token) => token.trim())
    .filter(Boolean)
}

/**
 * 所有关键词都命中才算匹配（AND），并按命中位置给出得分，越小越靠前。
 */
function scoreOf(title, tokens) {
  const lower = title.toLowerCase()
  let score = 0
  for (const token of tokens) {
    const at = lower.indexOf(token)
    if (at === -1) return -1
    score += at
  }
  return score + title.length / 200
}

export function filterLessons(list, { keyword = '', subject = '', grade = '' } = {}) {
  const tokens = tokenize(keyword)

  const matched = []
  for (const item of list) {
    if (subject && item.subject !== subject) continue
    if (grade && item.grade !== grade) continue

    if (tokens.length === 0) {
      matched.push({ item, score: 0 })
      continue
    }

    const score = scoreOf(item.title, tokens)
    if (score >= 0) matched.push({ item, score })
  }

  if (tokens.length > 0) {
    matched.sort((a, b) => a.score - b.score || b.item.stamp - a.item.stamp)
  }

  return matched.map((entry) => entry.item)
}

export function sortLessons(list, mode) {
  const copy = list.slice()
  if (mode === 'time-asc') copy.sort((a, b) => a.stamp - b.stamp)
  else if (mode === 'title') copy.sort((a, b) => a.title.localeCompare(b.title, 'zh-Hans-CN'))
  else copy.sort((a, b) => b.stamp - a.stamp)
  return copy
}

/**
 * 把命中片段切出来，供模板里用 <mark> 高亮：
 * highlightParts("高二语文：习题课", "语文") → [{text:"高二"},{text:"语文",hit:true},{text:"：习题课"}]
 */
export function highlightParts(title, keyword) {
  const tokens = tokenize(keyword)
  if (!tokens.length) return [{ text: title, hit: false }]

  const lower = title.toLowerCase()
  const hits = []
  for (const token of tokens) {
    let from = 0
    while (from <= lower.length) {
      const at = lower.indexOf(token, from)
      if (at === -1) break
      hits.push([at, at + token.length])
      from = at + token.length
      if (hits.length > 40) break
    }
  }
  if (!hits.length) return [{ text: title, hit: false }]

  hits.sort((a, b) => a[0] - b[0])
  const merged = []
  for (const [start, end] of hits) {
    const last = merged[merged.length - 1]
    if (last && start <= last[1]) last[1] = Math.max(last[1], end)
    else merged.push([start, end])
  }

  const parts = []
  let cursor = 0
  for (const [start, end] of merged) {
    if (start > cursor) parts.push({ text: title.slice(cursor, start), hit: false })
    parts.push({ text: title.slice(start, end), hit: true })
    cursor = end
  }
  if (cursor < title.length) parts.push({ text: title.slice(cursor), hit: false })

  return parts
}

/* ------------------------------------------------------------------ */
/* 统计 / 相关推荐                                                      */
/* ------------------------------------------------------------------ */

export function summarize(list) {
  const subjects = new Set()
  const grades = new Set()
  let latest = ''
  for (const item of list) {
    subjects.add(item.subject)
    if (item.grade) grades.add(item.grade)
    if (item.date > latest) latest = item.date
  }
  return {
    total: list.length,
    subjects: subjects.size,
    grades: [...grades].sort(),
    latest
  }
}

/**
 * 同科目、日期最接近的课程。
 */
export function relatedLessons(list, current, limit = 10) {
  if (!current) return []
  return list
    .filter((item) => item.id !== current.id && item.subject === current.subject)
    .sort((a, b) => Math.abs(a.stamp - current.stamp) - Math.abs(b.stamp - current.stamp))
    .slice(0, limit)
}

/**
 * 按时间顺序的上一节 / 下一节。
 */
export function neighbours(list, current) {
  if (!current) return { prev: null, next: null }
  const ordered = list.slice().sort((a, b) => a.stamp - b.stamp || a.id - b.id)
  const at = ordered.findIndex((item) => item.id === current.id)
  if (at === -1) return { prev: null, next: null }
  return {
    prev: at > 0 ? ordered[at - 1] : null,
    next: at < ordered.length - 1 ? ordered[at + 1] : null
  }
}
