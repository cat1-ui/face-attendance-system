<template>
  <div>
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card>
          <div class="stat-label">学生总数</div>
          <div class="stat-value">{{ summary.total_students }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-label">已录脸</div>
          <div class="stat-value">{{ coverage.enrolled }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-label">未录脸</div>
          <div class="stat-value">{{ coverage.not_enrolled }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-label">录入覆盖率</div>
          <div class="stat-value">{{ (coverage.coverage_rate * 100).toFixed(1) }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 -->
    <el-row :gutter="16" class="mt">
      <el-col :span="12">
        <el-card>
          <template #header>班级分布</template>
          <div ref="classChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>性别分布</template>
          <div ref="genderChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt">
      <el-col :span="12">
        <el-card>
          <template #header>专业分布</template>
          <div ref="majorChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>脸照数量分布</template>
          <div ref="faceChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getSummary, getFaceCoverage, getFaceCount } from '../api/stats'

const summary = reactive({ total_students: 0, by_class: {}, by_gender: {}, by_major: {} })
const coverage = reactive({ enrolled: 0, not_enrolled: 0, coverage_rate: 0 })
const faceCount = reactive({ zero_face: 0, one_face: 0, multiple_faces: 0 })

const classChart = ref(null)
const genderChart = ref(null)
const majorChart = ref(null)
const faceChart = ref(null)

function renderPie(el, data) {
  const chart = echarts.init(el)
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: Object.entries(data).map(([name, value]) => ({ name, value })),
    }],
  })
  return chart
}

function renderBar(el, categories, values) {
  const chart = echarts.init(el)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: values, barMaxWidth: 50 }],
  })
  return chart
}

onMounted(async () => {
  const [s, c, fc] = await Promise.all([getSummary(), getFaceCoverage(), getFaceCount()])
  Object.assign(summary, s)
  Object.assign(coverage, c)
  Object.assign(faceCount, fc)

  await nextTick()
  renderPie(classChart.value, summary.by_class)
  renderPie(genderChart.value, summary.by_gender)
  renderPie(majorChart.value, summary.by_major)
  renderBar(faceChart.value, ['0张', '1张', '多张'], [faceCount.zero_face, faceCount.one_face, faceCount.multiple_faces])
})
</script>

<style scoped>
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
