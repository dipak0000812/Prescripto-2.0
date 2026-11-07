"""
Real-time Notifications Router: WebSocket endpoint for live updates.
Handles review queue changes, safety alerts, and system notifications.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session

from prescripto.db.session import get_db
from prescripto.auth.dependencies import get_current_user_ws
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role

router = APIRouter(prefix="/notifications", tags=["Real-time Notifications"])


class ConnectionManager:
    """Manages WebSocket connections per user."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Track user roles for role-based broadcasting
        self.user_roles: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_roles[user_id] = role

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.user_roles.pop(user_id, None)

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to all connections for a specific user."""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.add(connection)
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast_to_role(self, message: dict, role: str):
        """Broadcast message to all users with a specific role."""
        for user_id, user_role in self.user_roles.items():
            if user_role == role or user_role == Role.ADMIN.value:
                await self.send_personal_message(message, user_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time notifications.
    Connect with: ws://host/api/v1/notifications/ws?token=<access_token>
    """
    # Authenticate user via token
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = str(user.id)
    await manager.connect(websocket, user_id, user.role)

    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user_id,
            "role": user.role,
            "timestamp": datetime.utcnow().isoformat(),
        }))

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_client_message(message, user_id, db)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


async def handle_client_message(message: dict, user_id: str, db: Session):
    """Handle incoming messages from client."""
    msg_type = message.get("type")

    if msg_type == "ping":
        # Respond to ping with pong
        pass  # Handled by WebSocket keepalive

    elif msg_type == "subscribe":
        # Handle subscription to specific channels
        channels = message.get("channels", [])
        # In production, track user subscriptions per channel
        pass

    elif msg_type == "mark_read":
        # Mark notification as read
        notification_id = message.get("notification_id")
        # Update notification read status in DB
        pass


# Utility functions for other services to send notifications

async def notify_review_queue_update(analysis_id: str, status: str, reviewer_id: str | None = None):
    """Notify about review queue changes."""
    message = {
        "type": "review_queue_update",
        "analysis_id": analysis_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if reviewer_id:
        await manager.send_personal_message(message, reviewer_id)
    else:
        # Broadcast to all reviewers/admins
        await manager.broadcast_to_role(message, Role.REVIEWER.value)
        await manager.broadcast_to_role(message, Role.ADMIN.value)


async def notify_safety_alert(patient_id: str, finding_type: str, severity: str):
    """Notify about new safety findings."""
    message = {
        "type": "safety_alert",
        "patient_id": patient_id,
        "finding_type": finding_type,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
    }
    # Broadcast to relevant doctors/admins
    await manager.broadcast_to_role(message, Role.REVIEWER.value)
    await manager.broadcast_to_role(message, Role.ADMIN.value)


async def notify_patient_message(patient_id: str, doctor_id: str, message_preview: str):
    """Notify patient of new message from doctor."""
    message = {
        "type": "new_message",
        "from_doctor_id": doctor_id,
        "preview": message_preview,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await manager.send_personal_message(message, patient_id)


async def notify_system_announcement(title: str, message: str, target_roles: List[str] = None):
    """Send system-wide announcement."""
    payload = {
        "type": "system_announcement",
        "title": title,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if target_roles:
        for role in target_roles:
            await manager.broadcast_to_role(payload, role)
    else:
        await manager.broadcast_to_all(payload)