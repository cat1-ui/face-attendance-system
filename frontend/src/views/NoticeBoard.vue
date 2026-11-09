<template>
  <div>
    <el-card class="mb">
      <el-form inline>
        <el-form-item>
          <el-button type="primary" @click="openAdd">发布公告</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="publisher" label="发布人" width="120" />
        <el-table-column prop="created_at" label="发布时间" width="200" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑公告' : '发布公告'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="发布人">
          <el-input v-model="form.publisher" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getNotices, createNotice, updateNotice, deleteNotice } from '../api/notice'
import { useNoticeStore } from '../stores/notice'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({})
const query = reactive({ page: 1, page_size: 10 })
const noticeStore = useNoticeStore()

async function load() {
  loading.value = true
  try {
    const data = await getNotices(query)
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
  noticeStore.markRead()
}

function openAdd() {
  form.value = {}
  dialogVisible.value = true
}

function openEdit(row) {
  form.value = { ...row }
  dialogVisible.value = true
}

async function submit() {
  if (!form.value.title) {
    ElMessage.warning('标题必填')
    return
  }
  if (form.value.id) {
    await updateNotice(form.value.id, form.value)
    ElMessage.success('更新成功')
  } else {
    await createNotice(form.value)
    ElMessage.success('发布成功')
  }
  dialogVisible.value = false
  load()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除这条公告？', '提示', { type: 'warning' })
  await deleteNotice(row.id)
  ElMessage.success('删除成功')
  load()
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
