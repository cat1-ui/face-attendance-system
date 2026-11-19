import request from './request'

// 登录：走 JSON 版接口，前端不用拼 form-data
export function login(username, password) {
  return request.post('/api/auth/login-json', { username, password })
}

// 当前登录用户（刷新页面后用它恢复用户信息 / 验证 token 是否还有效）
export function fetchMe() {
  return request.get('/api/auth/me')
}
