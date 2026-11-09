import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  baseURL: '', // 走 vite 代理，不写域名
  timeout: 30000,
})

// 响应拦截器：统一处理 {code, message, data}
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端统一响应格式
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 0) {
        return res.data
      }
      // 业务错误
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  (error) => {
    // HTTP 错误（4xx/5xx），后端已统一成 {code, message}
    const msg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
