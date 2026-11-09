"""WebSocket 端点 - 公告实时推送通道

WS /ws/notices：客户端连上后加入连接池，服务端发布公告时广播。
心跳：服务端发 ping，客户端回 pong 维持连接。
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/notices")
async def ws_notices(websocket: WebSocket):
    """公告推送通道"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息（主要用于心跳 pong）
            data = await websocket.receive_json()
            # 客户端发 pong 就回 ping（也可主动发 ping 心跳）
            if data.get("type") == "pong":
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
