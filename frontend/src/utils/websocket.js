// WebSocket 封装：连接公告推送通道，自动重连
export function createNoticeSocket(onMessage) {
  // 浏览器原生 WebSocket 不能带自定义请求头，token 只能放 query
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const token = localStorage.getItem('attendance_token') || ''
  const url = `${proto}://${location.host}/ws/notices?token=${encodeURIComponent(token)}`
  let ws = null
  let timer = null
  let closed = false

  function connect() {
    ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket 已连接')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }))
        } else if (msg.type === 'notice') {
          onMessage(msg.data)
        }
      } catch (e) {
        console.error('WS 消息解析失败', e)
      }
    }

    ws.onclose = () => {
      // 非主动关闭才重连
      if (!closed) {
        console.log('WebSocket 断开，3 秒后重连')
        timer = setTimeout(connect, 3000)
      }
    }

    ws.onerror = (e) => {
      console.error('WebSocket 错误', e)
    }
  }

  connect()

  // 返回关闭函数
  return () => {
    closed = true
    clearTimeout(timer)
    if (ws) ws.close()
  }
}
