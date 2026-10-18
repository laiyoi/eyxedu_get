<script setup>
const year = new Date().getFullYear()
const repo = 'https://github.com/laiyoi/eyxedu_get'
</script>

<template>
  <div class="app">
    <header class="app-nav">
      <div class="container app-nav__inner">
        <router-link to="/" class="brand" aria-label="返回课程库">
          <span class="brand__mark" aria-hidden="true">亿</span>
          <span class="brand__copy">
            <strong>亿云校</strong>
            <em>课程回放</em>
          </span>
        </router-link>

        <nav class="app-nav__links" aria-label="主导航">
          <router-link to="/" class="nav-link">课程库</router-link>
          <a :href="repo" class="nav-link" target="_blank" rel="noopener noreferrer">源码</a>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>

    <footer class="app-footer">
      <div class="container app-footer__inner">
        <p>© {{ year }} 亿云校课程回放</p>
        <p class="app-footer__note">数据每周六自动更新 · 仅供个人学习使用</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ---------------- 顶部导航 ---------------- */
.app-nav {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--surface);
  background: color-mix(in srgb, var(--surface) 82%, transparent);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--border);
}

.app-nav__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 62px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
}

.brand:hover {
  color: var(--text);
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: #fff;
  font-weight: 700;
  font-size: 17px;
  box-shadow: 0 6px 14px -6px rgba(79, 70, 229, 0.9);
}

.brand__copy {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.brand__copy strong {
  font-size: 15.5px;
  letter-spacing: 0.2px;
}

.brand__copy em {
  font-style: normal;
  font-size: 11.5px;
  color: var(--text-3);
  letter-spacing: 0.6px;
}

.app-nav__links {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link {
  padding: 7px 13px;
  border-radius: 999px;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text-2);
  transition: background-color 0.2s var(--ease), color 0.2s var(--ease);
}

.nav-link:hover {
  background: var(--surface-2);
  color: var(--text);
}

.nav-link.router-link-exact-active {
  color: var(--brand-600);
  background: var(--brand-50);
}

/* ---------------- 主体 ---------------- */
.app-main {
  flex: 1;
  width: 100%;
  min-width: 0;
}

/* ---------------- 页脚 ---------------- */
.app-footer {
  margin-top: 48px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  background: color-mix(in srgb, var(--surface) 60%, transparent);
}

.app-footer__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-block: 20px;
  font-size: 12.5px;
  color: var(--text-3);
}

.app-footer__note {
  margin: 0;
}

@media (max-width: 560px) {
  .app-nav__inner {
    height: 56px;
  }

  .brand__copy em {
    display: none;
  }
}
</style>
