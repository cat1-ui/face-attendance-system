<template>
  <div>
    <el-row :gutter="16">
      <!-- 左侧：摄像头 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>摄像头</span>
              <el-button v-if="!streaming" type="primary" @click="startCamera">开启摄像头</el-button>
              <el-button v-else type="danger" @click="stopCamera">关闭摄像头</el-button>
            </div>
          </template>
          <div class="camera-box">
            <video ref="video" autoplay playsinline class="camera"></video>
            <canvas ref="canvas" style="display: none"></canvas>
          </div>
          <div class="actions">
            <el-button type="success" size="large" :disabled="!streaming" @click="capture('checkin')">
              签到打卡
            </el-button>
            <el-button type="warning" size="large" :disabled="!streaming" @click="capture('checkout')">
              签退打卡
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：识别结果 -->
      <el-col :span="12">
        <el-card>
          <template #header>识别结果</template>
          <div v-if="!result" class="placeholder">
            <el-icon :size="48" color="#c0c4cc"><Camera /></el-icon>
            <p>开启摄像头并打卡后，这里显示识别结果</p>
          </div>
          <div v-else-if="result.matched" class="result-box">
            <el-result icon="success" title="识别成功">
              <template #sub-title>
                <div class="result-info">
                  <p class="name">{{ result.student_name }}（{{ result.student_no }}）</p>
                  <p>
                    <el-tag :type="statusTagType(result.status)">{{ statusLabel(result.status) }}</el-tag>
                    <el-tag type="info" class="ml">{{ result.check_type === 'checkin' ? '签到' : '签退' }}</el-tag>
                  </p>
                  <p class="detail">相似度：{{ (result.similarity * 100).toFixed(1) }}%</p>
                  <p class="detail">打卡时间：{{ formatTime(result.check_time) }}</p>
                </div>
              </template>
            </el-result>
          </div>
          <div v-else class="result-box">
            <el-result icon="error" title="识别失败">
              <template #sub-title>
                <p class="detail">{{ result.reason }}</p>
              </template>
            </el-result>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 今日统计 -->
    <el-card class="mt">
      <template #header>今日考勤概览</template>
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-label">应到人数</div>
          <div class="stat-value">{{ stats.total_students }}</div>
        </el-col>
        <el-col :span="6">
          <div class="stat-label">已签到</div>
          <div class="stat-value">{{ stats.checked_in }}</div>
        </el-col>
        <el-col :span="6">
          <div class="stat-label">缺勤</div>
          <div class="stat-value">{{ stats.absent }}</div>
        </el-col>
        <el-col :span="6">
          <div class="stat-label">出勤率</div>
          <div class="stat-value">{{ (stats.attendance_rate * 100).toFixed(1) }}%</div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { checkin, getAttendanceStats } from '../api/attendance'

const video = ref(null)
const canvas = ref(null)
const streaming = ref(false)
const result = ref(null)
const stats = reactive({ total_students: 0, checked_in: 0, absent: 0, attendance_rate: 0 })

let stream = null

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 480 },
    })
    video.value.srcObject = stream
    streaming.value = true
  } catch (e) {
    // 区分具体失败原因，给出针对性提示
    const name = e && e.name
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
      ElMessage.error('摄像头权限被拒绝，请点击地址栏左侧的摄像头图标 → 选择「允许」')
    } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
      ElMessage.error('未检测到摄像头设备，请确认摄像头已连接')
    } else if (name === 'NotReadableError' || name === 'TrackStartError') {
      ElMessage.error('摄像头被其他程序占用，请关闭占用摄像头的程序后重试')
    } else if (e && e.message && e.message.includes('secure')) {
      ElMessage.error('当前非安全上下文，请用 http://localhost:5173 访问（不能用 IP 地址）')
    } else {
      ElMessage.error('无法访问摄像头，请用 localhost 访问并检查浏览器权限')
    }
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
  streaming.value = false
}

function capture(checkType) {
  const v = video.value
  const c = canvas.value
  c.width = v.videoWidth
  c.height = v.videoHeight
  c.getContext('2d').drawImage(v, 0, 0, c.width, c.height)
  // canvas 转 blob → FormData
  c.toBlob(async (blob) => {
    if (!blob) {
      ElMessage.error('拍照失败，请重试')
      return
    }
    const fd = new FormData()
    fd.append('file', blob, `checkin_${Date.now()}.jpg`)
    try {
      const data = await checkin(fd, checkType)
      result.value = { ...data, check_type: checkType }
      if (data.matched) {
        ElMessage.success('打卡成功')
        loadStats()
      }
    } catch (e) {
      // 错误已由拦截器提示
    }
  }, 'image/jpeg')
}

function statusLabel(status) {
  const map = { normal: '正常', late: '迟到', early: '早退', absent: '缺勤' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { normal: 'success', late: 'warning', early: 'warning', absent: 'danger' }
  return map[status] || 'info'
}

function formatTime(t) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

async function loadStats() {
  const s = await getAttendanceStats()
  Object.assign(stats, s)
}

onMounted(loadStats)
onUnmounted(stopCamera)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.camera-box {
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  aspect-ratio: 4 / 3;
}
.camera {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 16px;
}
.placeholder {
  text-align: center;
  color: #909399;
  padding: 60px 0;
}
.result-info .name {
  font-size: 20px;
  font-weight: 600;
  margin: 8px 0;
}
.result-info .detail {
  color: #909399;
  margin: 4px 0;
}
.ml {
  margin-left: 8px;
}
.mt {
  margin-top: 16px;
}
.stat-label {
  color: #8a94a1;
  font-size: 13px;
  letter-spacing: 0.5px;
}
.stat-value {
  font-size: 30px;
  font-weight: 300;
  margin-top: 6px;
  color: #2b3644;
}
</style>
