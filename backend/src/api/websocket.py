"""
WebSocket API - 实时通信
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio

from src.core.logging import logger
from src.core.security import verify_websocket_token
# TODO: 在完成Celery配置后启用
# from src.workers.base import app as celery_app

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 活跃连接 {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 连接元数据 {user_id: {connection_id: metadata}}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # 任务订阅 {task_id: {user_id: set of connection_ids}}
        self.task_subscriptions: Dict[str, Dict[str, set]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """接受连接"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        self.active_connections[user_id][connection_id] = websocket

        # 保存连接元数据
        self.connection_metadata[user_id] = self.connection_metadata.get(user_id, {})
        self.connection_metadata[user_id][connection_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat(),
        }

        logger.info(f"WebSocket连接建立: user_id={user_id}, connection_id={connection_id}")

        # 发送欢迎消息
        await self.send_to_connection(user_id, connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def disconnect(self, user_id: str, connection_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # 清理元数据
        if user_id in self.connection_metadata:
            self.connection_metadata[user_id].pop(connection_id, None)
            if not self.connection_metadata[user_id]:
                del self.connection_metadata[user_id]

        # 清理任务订阅
        for task_id, subscribers in self.task_subscriptions.items():
            if user_id in subscribers:
                subscribers[user_id].discard(connection_id)
                if not subscribers[user_id]:
                    del subscribers[user_id]
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]

        logger.info(f"WebSocket连接断开: user_id={user_id}, connection_id={connection_id}")

    async def send_to_connection(self, user_id: str, connection_id: str, message: dict):
        """向特定连接发送消息"""
        if (user_id in self.active_connections and
            connection_id in self.active_connections[user_id]):
            websocket = self.active_connections[user_id][connection_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                self.disconnect(user_id, connection_id)

    async def send_to_user(self, user_id: str, message: dict, exclude_connection: Optional[str] = None):
        """向用户的所有连接发送消息"""
        if user_id in self.active_connections:
            for connection_id in list(self.active_connections[user_id].keys()):
                if exclude_connection and connection_id == exclude_connection:
                    continue
                await self.send_to_connection(user_id, connection_id, message)

    async def subscribe_to_task(self, user_id: str, connection_id: str, task_id: str):
        """订阅任务进度"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = {}
        if user_id not in self.task_subscriptions[task_id]:
            self.task_subscriptions[task_id][user_id] = set()

        self.task_subscriptions[task_id][user_id].add(connection_id)

        await self.send_to_connection(user_id, connection_id, {
            "type": "task_subscribed",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_task_subscribers(self, task_id: str) -> Dict[str, set]:
        """获取任务订阅者"""
        return self.task_subscriptions.get(task_id, {})

    async def broadcast_task_update(self, task_id: str, update_data: dict):
        """广播任务更新"""
        subscribers = self.get_task_subscribers(task_id)
        message = {
            "type": "task_update",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            **update_data
        }

        for user_id, connection_ids in subscribers.items():
            for connection_id in connection_ids:
                await self.send_to_connection(user_id, connection_id, message)

    async def ping_all(self):
        """向所有连接发送ping"""
        for user_id in list(self.active_connections.keys()):
            for connection_id in list(self.active_connections[user_id].keys()):
                await self.send_to_connection(user_id, connection_id, {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    def get_stats(self) -> dict:
        """获取连接统计信息"""
        total_connections = sum(
            len(connections) for connections in self.active_connections.values()
        )
        active_users = len(self.active_connections)

        return {
            "active_users": active_users,
            "total_connections": total_connections,
            "task_subscriptions": len(self.task_subscriptions),
            "timestamp": datetime.utcnow().isoformat(),
        }


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket连接端点"""
    # 验证token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = verify_websocket_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4003, reason="Invalid token")
            return
    except Exception as e:
        logger.error(f"WebSocket token验证失败: {e}")
        await websocket.close(code=4003, reason="Invalid token")
        return

    connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"

    try:
        await manager.connect(websocket, user_id, connection_id)

        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理不同类型的消息
                await handle_websocket_message(user_id, connection_id, message)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_to_connection(user_id, connection_id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息时出错: {e}")
                await manager.send_to_connection(user_id, connection_id, {
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, connection_id)


async def handle_websocket_message(user_id: str, connection_id: str, message: dict):
    """处理WebSocket消息"""
    message_type = message.get("type")

    if message_type == "ping":
        # 响应ping
        await manager.send_to_connection(user_id, connection_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # 更新最后ping时间
        if (user_id in manager.connection_metadata and
            connection_id in manager.connection_metadata[user_id]):
            manager.connection_metadata[user_id][connection_id]["last_ping"] = datetime.utcnow().isoformat()

    elif message_type == "subscribe_task":
        # 订阅任务进度
        task_id = message.get("task_id")
        if task_id:
            await manager.subscribe_to_task(user_id, connection_id, task_id)
        else:
            await manager.send_to_connection(user_id, connection_id, {
                "type": "error",
                "message": "Missing task_id for subscription",
                "timestamp": datetime.utcnow().isoformat(),
            })

    elif message_type == "unsubscribe_task":
        # 取消订阅任务进度
        task_id = message.get("task_id")
        if task_id and task_id in manager.task_subscriptions:
            if user_id in manager.task_subscriptions[task_id]:
                manager.task_subscriptions[task_id][user_id].discard(connection_id)
                if not manager.task_subscriptions[task_id][user_id]:
                    del manager.task_subscriptions[task_id][user_id]

            await manager.send_to_connection(user_id, connection_id, {
                "type": "task_unsubscribed",
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

    else:
        # 未知消息类型
        await manager.send_to_connection(user_id, connection_id, {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat(),
        })


# Celery事件处理 - 任务进度更新
async def setup_celery_events():
    """设置Celery事件监听"""
    from celery.events.state import State
    from celery.events import EventReceiver

    async def handle_event(event):
        event_type = event.get("type")
        task_id = event.get("uuid")

        if not task_id:
            return

        # 处理任务相关事件
        if event_type in ["task-succeeded", "task-failed", "task-retried", "task-revoked"]:
            update_data = {
                "event_type": event_type,
                "status": event_type.split("-")[1],  # succeeded, failed, etc.
                "timestamp": datetime.utcnow().isoformat(),
            }

            if event_type == "task-succeeded":
                update_data["result"] = event.get("result")
            elif event_type == "task-failed":
                update_data["error"] = event.get("exception")

            await manager.broadcast_task_update(task_id, update_data)

    # 这里需要设置实际的事件监听
    # 由于复杂性和当前范围，暂时使用简化版本
    logger.info("Celery事件监听器已设置")


# 定期ping任务
async def periodic_ping():
    """定期ping任务"""
    while True:
        try:
            await manager.ping_all()
            await asyncio.sleep(30)  # 每30秒ping一次
        except Exception as e:
            logger.error(f"定期ping任务失败: {e}")
            await asyncio.sleep(60)


# 获取WebSocket统计信息
@router.get("/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计"""
    return manager.get_stats()


# 向特定任务发送进度更新 (供Celery任务调用)
async def send_task_progress(task_id: str, progress: int, message: str = None):
    """发送任务进度更新"""
    update_data = {
        "progress": progress,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await manager.broadcast_task_update(task_id, update_data)


# 向特定任务发送状态更新
async def send_task_status(task_id: str, status: str, details: dict = None):
    """发送任务状态更新"""
    update_data = {
        "status": status,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    await manager.broadcast_task_update(task_id, update_data)


# 导出管理器实例供其他模块使用
__all__ = [
    "manager",
    "send_task_progress",
    "send_task_status",
]