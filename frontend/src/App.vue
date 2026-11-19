<template>
  <!-- 登录页等公开页面不套后台布局 -->
  <router-view v-if="$route.meta.public" />

  <el-container v-else class="layout">
    <!-- 顶部工具栏 -->
    <el-header class="header">
      <div class="brand">
        <span class="brand-dot"></span>
        <span class="title">学生刷脸考勤系统</span>
      </div>
      <div class="header-right">
        <el-badge :is-dot="noticeStore.hasNew" class="bell">
          <el-icon :size="20" @click="goNotices"><Bell /></el-icon>
        </el-badge>
        <el-tag v-if="userStore.profile" size="small" :type="userStore.isAdmin ? 'success' : 'info'">
          {{ userStore.profile.username }} · {{ userStore.isAdmin ? '管理员' : '只读' }}
        </el-tag>
        <el-tooltip content="退出登录" placement="bottom">
          <el-icon :size="18" class="logout" @click="onLogout"><SwitchButton /></el-icon>
        </el-tooltip>
        <span class="datetime">{{ datetime }}</span>
      </div>
    </el-header>

    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="200px" class="aside">
        <el-menu :default-active="$route.path" router>
          <el-menu-item index="/students">
            <el-icon><User /></el-icon>
            <span>学生管理</span>
          </el-menu-item>
          <el-menu-item index="/faces">
            <el-icon><Camera /></el-icon>
            <span>人脸录入</span>
          </el-menu-item>
          <el-menu-item index="/checkin">
            <el-icon><Checked /></el-icon>
            <span>考勤签到</span>
          </el-menu-item>
          <el-menu-item index="/attendance">
            <el-icon><List /></el-icon>
            <span>考勤记录</span>
          </el-menu-item>
          <el-menu-item index="/stats">
            <el-icon><DataAnalysis /></el-icon>
            <span>信息汇总</span>
          </el-menu-item>
          <el-menu-item index="/notices">
            <el-icon><Bell /></el-icon>
            <span>公告管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 右侧工作区 -->
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import { useNoticeStore } from './stores/notice'
import { useUserStore } from './stores/user'
import { fetchMe } from './api/auth'
import { createNoticeSocket } from './utils/websocket'

const route = useRoute()
const router = useRouter()
const noticeStore = useNoticeStore()
const userStore = useUserStore()
const datetime = ref('')
let closeSocket = null
let timer = null

function updateTime() {
  const now = new Date()
  datetime.value = now.toLocaleString('zh-CN')
}

function goNotices() {
  noticeStore.markRead()
  router.push('/notices')
}

onMounted(async () => {
  updateTime()
  timer = setInterval(updateTime, 1000)

  // 必须等路由完成首次解析：App 挂载早于路由就绪，
  // 此时 route.meta 还是空对象，会把登录页误判成受保护页而去请求 /api/auth/me
  await router.isReady()

  // 公开页（登录页）不拉用户信息、不建长连接
  if (route.meta.public) return

  // 刷新后恢复用户信息；token 失效时拦截器会踢回登录页
  try {
    const me = await fetchMe()
    userStore.setProfile(me)
  } catch (e) {
    userStore.logout()
    router.replace('/login')
    return
  }

  connectSocket()
})

function connectSocket() {
  // 连接 WebSocket，收到公告推送
  closeSocket = createNoticeSocket((notice) => {
    noticeStore.onPush(notice)
    ElNotification({
      title: '新公告',
      message: notice.title,
      type: 'info',
    })
  })
}

function onLogout() {
  if (closeSocket) {
    closeSocket()
    closeSocket = null
  }
  userStore.logout()
  router.replace('/login')
}

onUnmounted(() => {
  clearInterval(timer)
  if (closeSocket) closeSocket()
})
</script>

<style scoped>
.layout {
  height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #eceff3;
  padding: 0 24px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #5b7a99;
  box-shadow: 0 0 0 4px rgba(91, 122, 153, 0.12);
}
.title {
  font-size: 17px;
  font-weight: 600;
  color: #2b3644;
  letter-spacing: 0.5px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.bell {
  cursor: pointer;
  color: #4a5563;
}
.bell:hover {
  color: #5b7a99;
}
.logout {
  cursor: pointer;
  color: #4a5563;
}
.logout:hover {
  color: #c45656;
}
.datetime {
  color: #8a94a1;
  font-size: 13px;
}
.aside {
  border-right: 1px solid #eceff3;
  background: #fff;
}
.main {
  background: #f7f8fa;
  padding: 20px;
}
</style>
