<template>
  <div>
    <el-card>
      <template #header>人脸录入</template>
      <el-form inline>
        <el-form-item label="选择学生">
          <el-select v-model="selectedId" placeholder="请选择学生" filterable style="width: 260px">
            <el-option
              v-for="s in students"
              :key="s.id"
              :label="`${s.name}（${s.student_no}）`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="人脸照片">
          <el-upload :show-file-list="false" :before-upload="handleUpload" accept="image/*">
            <el-button type="primary" :disabled="!selectedId || hasFace">上传照片录入</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <p class="tip">{{ hasFace ? '该学生已录入人脸，如需更换请先删除旧脸照。' : '提示：上传一张清晰的正脸照片，后端会自动检测人脸并提取特征向量。' }}</p>
    </el-card>

    <el-card class="mt">
      <template #header>已录入脸照</template>
      <el-table :data="faces" border v-loading="faceLoading">
        <el-table-column label="照片" width="100" align="center">
          <template #default="{ row }">
            <el-image
              :src="faceImages[row.face_id]"
              :preview-src-list="faceImages[row.face_id] ? [faceImages[row.face_id]] : []"
              preview-teleported
              fit="cover"
              style="width: 64px; height: 64px; border-radius: 4px"
              :initial-index="0"
            >
              <template #error>
                <div class="img-error">无图</div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column prop="face_id" label="face_id" width="90" />
        <el-table-column prop="image_path" label="图片路径" />
        <el-table-column prop="created_at" label="录入时间" width="200" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDeleteFace(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!faceLoading && faces.length === 0" description="该学生还没有脸照" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStudents } from '../api/student'
import { uploadFace, getFaces, deleteFace } from '../api/face'
import { fetchImageObjectUrl } from '../utils/authImage'

const students = ref([])
const selectedId = ref(null)
const faces = ref([])
const faceLoading = ref(false)
// face_id -> object URL（受保护图片必须带 token 取，不能直接塞给 <img src>）
const faceImages = ref({})

// 该学生是否已有脸照（限制每人只录 1 张）
const hasFace = computed(() => faces.value.length >= 1)

async function loadStudents() {
  // 分页拉全量：后端 page_size 上限 100，循环翻页直到拿完
  // （此前写死 page_size:1000 会触发后端校验错误，导致下拉框无学生）
  const pageSize = 100
  let page = 1
  let all = []
  while (true) {
    const data = await getStudents({ page, page_size: pageSize })
    all = all.concat(data.items)
    if (page * pageSize >= data.total || data.items.length < pageSize) {
      break
    }
    page += 1
  }
  students.value = all
}

async function loadFaces() {
  if (!selectedId.value) {
    faces.value = []
    return
  }
  faceLoading.value = true
  try {
    faces.value = await getFaces(selectedId.value)
    await loadFaceImages(faces.value)
  } finally {
    faceLoading.value = false
  }
}

// 逐张取回脸照：请求经 axios，才会带上 Authorization
async function loadFaceImages(rows) {
  for (const row of rows) {
    if (!row.face_id || faceImages.value[row.face_id]) continue
    try {
      faceImages.value[row.face_id] = await fetchImageObjectUrl(`/api/faces/${row.face_id}/image`)
    } catch (e) {
      // 单张失败不影响列表（例如文件已丢失）
    }
  }
}

onUnmounted(() => {
  // object URL 不主动释放会一直占内存
  Object.values(faceImages.value).forEach((url) => URL.revokeObjectURL(url))
  faceImages.value = {}
})

async function handleUpload(file) {
  const fd = new FormData()
  fd.append('file', file)
  const result = await uploadFace(selectedId.value, fd)
  if (result.detected) {
    ElMessage.success('人脸录入成功')
    loadFaces()
  } else {
    ElMessage.error(result.reason || '未检测到人脸')
  }
  return false
}

async function handleDeleteFace(row) {
  await ElMessageBox.confirm('确定删除这张脸照？', '提示', { type: 'warning' })
  await deleteFace(row.face_id)
  ElMessage.success('删除成功')
  loadFaces()
}

onMounted(loadStudents)

// 选中学生变化时加载其脸照
import { watch } from 'vue'
watch(selectedId, loadFaces)
</script>

<style scoped>
.mt {
  margin-top: 16px;
}
.tip {
  color: #999;
  font-size: 13px;
}
.img-error {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
