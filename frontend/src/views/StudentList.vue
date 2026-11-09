<template>
  <div>
    <!-- 搜索栏 -->
    <el-card class="mb">
      <el-form inline>
        <el-form-item label="姓名">
          <el-input v-model="query.name" placeholder="模糊搜索" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="query.student_no" placeholder="模糊搜索" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select
            v-model="query.class_name"
            placeholder="模糊搜索"
            clearable
            filterable
            allow-create
            default-first-option
            style="width: 180px"
          >
            <el-option v-for="c in enums.classes" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄">
          <el-select v-model="query.age" placeholder="精确" clearable style="width: 110px">
            <el-option v-for="a in ageOptions" :key="a" :label="a" :value="a" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">搜索</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="openAdd">新增学生</el-button>
          <el-upload :show-file-list="false" :before-upload="handleImport" accept=".csv">
            <el-button>批量导入</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 学生表格 -->
    <el-card>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="age" label="年龄" width="70" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="major" label="专业" />
        <el-table-column prop="enroll_year" label="入学年份" width="90" />
        <el-table-column prop="phone" label="联系方式" width="130" />
        <el-table-column label="人脸状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.face_status === 1 ? 'success' : 'info'">
              {{ row.face_status === 1 ? '已录' : '未录' }}
            </el-tag>
          </template>
        </el-table-column>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑学生' : '新增学生'" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="学号" required>
          <el-input v-model="form.student_no" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="男">男</el-radio>
            <el-radio value="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="form.age" :min="18" :max="28" placeholder="18~28" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="form.class_name" placeholder="选择班级" clearable>
            <el-option v-for="c in enums.classes" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业">
          <el-select v-model="form.major" placeholder="选择专业" clearable>
            <el-option v-for="m in enums.majors" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="入学年份">
          <el-input-number v-model="form.enroll_year" :min="2000" :max="2030" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.phone" />
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
import { getStudents, createStudent, updateStudent, deleteStudent, importStudents, getEnums } from '../api/student'

const list = ref([])
const total = ref(0)
const loading = ref(false)
const enums = reactive({ classes: [], majors: [] })

const query = reactive({ page: 1, page_size: 10, name: '', student_no: '', class_name: '', age: '' })
// 年龄下拉可选项：18~28
const ageOptions = Array.from({ length: 11 }, (_, i) => i + 18)

const dialogVisible = ref(false)
const form = ref({})

async function load() {
  // 前端预校验：模糊字段不足最短长度时直接提示，不发请求
  const minLenMap = { name: 2, student_no: 3, class_name: 2 }
  for (const [field, minLen] of Object.entries(minLenMap)) {
    const val = query[field]
    if (val && val.trim().length < minLen) {
      ElMessage.warning(`「${field === 'name' ? '姓名' : field === 'student_no' ? '学号' : '班级'}」至少输入 ${minLen} 个字符`)
      return
    }
  }
  loading.value = true
  // 只把「有值」的条件发给后端：空字符串会让后端 int 参数（age）校验失败返回 422
  const params = { page: query.page, page_size: query.page_size }
  for (const key of ['name', 'student_no', 'class_name', 'age']) {
    const val = query[key]
    if (val !== '' && val !== null && val !== undefined) params[key] = val
  }
  try {
    const data = await getStudents(params)
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function reset() {
  query.name = ''
  query.student_no = ''
  query.class_name = ''
  query.age = ''
  query.page = 1
  load()
}

function openAdd() {
  form.value = { gender: '男' }
  dialogVisible.value = true
}

function openEdit(row) {
  form.value = { ...row }
  dialogVisible.value = true
}

async function submit() {
  if (!form.value.student_no || !form.value.name) {
    ElMessage.warning('学号和姓名必填')
    return
  }
  if (form.value.id) {
    await updateStudent(form.value.id, form.value)
    ElMessage.success('更新成功')
  } else {
    await createStudent(form.value)
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  load()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除学生「${row.name}」？其脸照会一并删除`, '提示', { type: 'warning' })
  await deleteStudent(row.id)
  ElMessage.success('删除成功')
  load()
}

async function handleImport(file) {
  const fd = new FormData()
  fd.append('file', file)
  const result = await importStudents(fd)
  ElMessage.success(`导入完成：成功 ${result.success} 条，跳过 ${result.skipped} 条`)
  load()
  return false // 阻止自动上传
}

onMounted(async () => {
  const e = await getEnums()
  enums.classes = e.classes
  enums.majors = e.majors
  load()
})
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
.mt {
  margin-top: 16px;
}
</style>
