<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <span class="dot"></span>
        <span class="title">学生刷脸考勤系统</span>
      </div>
      <p class="subtitle">请登录后使用</p>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" clearable>
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password>
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-button type="primary" size="large" class="submit" :loading="loading" @click="onSubmit">
          登 录
        </el-button>
      </el-form>

      <p class="hint">首次使用请在服务器执行 tools/init_admin.py 创建账号</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const data = await login(form.username, form.password)
    userStore.setToken(data.access_token)
    userStore.setProfile(data.user)
    ElMessage.success(`欢迎，${data.user.username}`)
    // 回到被守卫拦下前想访问的页面
    router.replace(route.query.redirect || '/students')
  } catch (e) {
    // 错误提示由 axios 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef2f7 0%, #dde5ee 100%);
}

.login-card {
  width: 380px;
  padding: 36px 34px 26px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 12px 40px rgba(43, 54, 68, 0.12);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #5b7a99;
  box-shadow: 0 0 0 4px rgba(91, 122, 153, 0.12);
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #2b3644;
  letter-spacing: 0.5px;
}

.subtitle {
  margin: 6px 0 22px;
  font-size: 13px;
  color: #8a94a3;
}

.submit {
  width: 100%;
  margin-top: 6px;
}

.hint {
  margin-top: 18px;
  font-size: 12px;
  color: #a3abb8;
  text-align: center;
  line-height: 1.6;
}
</style>
