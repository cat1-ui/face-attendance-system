"""WebSocket 连接管理 - 公告实时推送

维护一个在线客户端连接池，发布公告时广播给所有在线客户端。
"""
from typing import Set

from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接池：管理所有在线客户端"""

    def __init__(self):
        # 用 Set 存 WebSocket，天然去重
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """新客户端接入"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """客户端断开"""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """广播给所有在线客户端（失败连接自动清理）"""
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        # 清理已断开的连接
        for conn in dead:
            self.active_connections.discard(conn)


# 全局单例：所有地方共用同一个连接池
manager = ConnectionManager()
