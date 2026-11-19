import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { title: '登录', public: true } },
  { path: '/', redirect: '/students' },
  { path: '/students', name: 'students', component: () => import('../views/StudentList.vue'), meta: { title: '学生管理' } },
  { path: '/faces', name: 'faces', component: () => import('../views/FaceEnroll.vue'), meta: { title: '人脸录入' } },
  { path: '/checkin', name: 'checkin', component: () => import('../views/Checkin.vue'), meta: { title: '考勤签到' } },
  { path: '/attendance', name: 'attendance', component: () => import('../views/AttendanceList.vue'), meta: { title: '考勤记录' } },
  { path: '/stats', name: 'stats', component: () => import('../views/StatsDashboard.vue'), meta: { title: '信息汇总' } },
  { path: '/notices', name: 'notices', component: () => import('../views/NoticeBoard.vue'), meta: { title: '公告管理' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录一律回登录页，并记住原本想去的地址
// 这里读的是 Pinia 里的 token（初始化时从 localStorage 恢复）
router.beforeEach((to) => {
  const userStore = useUserStore()
  if (!to.meta.public && !userStore.token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && userStore.token) {
    return { path: '/students' }
  }
  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 学生刷脸考勤系统` : '学生刷脸考勤系统'
})

export default router
