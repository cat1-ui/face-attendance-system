import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

// token 存 localStorage：刷新页面不掉登录态
// （这不是「最安全」的存法——XSS 能读到；生产更推荐 HttpOnly Cookie + CSRF token）
const TOKEN_KEY = 'attendance_token'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const profile = ref(null) // { id, username, role }

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => profile.value?.role === 'admin')

  function setToken(t) {
    token.value = t
    localStorage.setItem(TOKEN_KEY, t)
  }

  function setProfile(p) {
    profile.value = p
  }

  function logout() {
    token.value = ''
    profile.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, profile, isLoggedIn, isAdmin, setToken, setProfile, logout }
})
