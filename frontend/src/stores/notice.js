import { defineStore } from 'pinia'
import { ref } from 'vue'

// 公告状态（含 WebSocket 推送数据）
export const useNoticeStore = defineStore('notice', () => {
  const hasNew = ref(false) // 是否有未读公告（铃铛红点）
  const latest = ref(null) // 最新推送的公告

  function markRead() {
    hasNew.value = false
  }

  function onPush(notice) {
    latest.value = notice
    hasNew.value = true
  }

  return { hasNew, latest, markRead, onPush }
})
