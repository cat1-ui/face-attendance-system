<template>
  <div>
    <!-- 筛选栏 -->
    <el-card class="mb">
      <el-form inline>
        <el-form-item label="日期">
          <el-date-picker
            v-model="query.day"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="全部日期"
            clearable
            style="width: 160px"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="query.check_type" placeholder="全部" clearable style="width: 130px">
            <el-option label="签到" value="checkin" />
            <el-option label="签退" value="checkout" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 130px">
            <el-option label="正常" value="normal" />
            <el-option label="迟到" value="late" />
            <el-option label="早退" value="early" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 记录表格 -->
    <el-card>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="student_no" label="学号" width="130" />
        <el-table-column prop="student_name" label="姓名" width="100" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.check_type === 'checkin' ? 'success' : 'warning'">
              {{ row.check_type === 'checkin' ? '签到' : '签退' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="check_time" label="打卡时间" width="200">
          <template #default="{ row }">{{ formatTime(row.check_time) }}</template>
        </el-table-column>
        <el-table-column label="相似度" width="100">
          <template #default="{ row }">
            {{ row.similarity != null ? (row.similarity * 100).toFixed(1) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
      </el-table>

      <el-pagination
        class="mt"
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="query.page_size"
        v-model:current-page="query.page"
        @current-change="load"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAttendance } from '../api/attendance'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const query = reactive({ page: 1, page_size: 10, day: '', check_type: '', status: '' })

async function load() {
  loading.value = true
  try {
    const data = await getAttendance(query)
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function reset() {
  query.day = ''
  query.check_type = ''
  query.status = ''
  query.page = 1
  load()
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

onMounted(load)
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
.mt {
  margin-top: 16px;
}
</style>
