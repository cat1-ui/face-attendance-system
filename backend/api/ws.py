"""WebSocket 端点 - 公告实时推送通道

WS /ws/notices?token=xxx：连上后加入连接池，服务端发布公告时广播。

为什么用 query 参数传 token 而不是 Authorization 头：
浏览器原生 WebSocket 构造函数不支持自定义请求头，只能把凭证放 URL 上
（生产环境应配合 wss 使用，避免 token 在链路上明文传输）。
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from core.security import decode_token
from core.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/notices")
async def ws_notices(websocket: WebSocket, token: str | None = Query(None)):
    """公告推送通道（需登录）"""
    # 握手阶段就校验，不合法直接拒绝，不占用连接池
    try:
        if not token:
            raise ValueError("missing token")
        decode_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息（主要用于心跳 pong）
            data = await websocket.receive_json()
            if data.get("type") == "pong":
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
