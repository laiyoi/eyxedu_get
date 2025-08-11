import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../components/HomePage.vue'
import VideoPlayerPage from '../components/VideoPlayerPage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/player',
    name: 'videoPlayerPage',
    component: VideoPlayerPage
  }
]

const router = createRouter({
  history: createWebHashHistory('/eyxedu_get/'),
  routes
})

// 全局导航守卫：滚动到顶部
router.afterEach(() => {
  window.scrollTo(0, 0)
})

export default router