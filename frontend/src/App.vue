<template>
  <el-container class="layout">
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
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import { useNoticeStore } from './stores/notice'
import { createNoticeSocket } from './utils/websocket'

const router = useRouter()
const noticeStore = useNoticeStore()
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

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)

  // 连接 WebSocket，收到公告推送
  closeSocket = createNoticeSocket((notice) => {
    noticeStore.onPush(notice)
    ElNotification({
      title: '新公告',
      message: notice.title,
      type: 'info',
    })
  })
})

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
