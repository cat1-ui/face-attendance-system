import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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

export default router
