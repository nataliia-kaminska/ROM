from jwt import InvalidTokenError
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import SessionLocal
from app.services.realtime_notifications import notification_connection_manager


router = APIRouter(tags=["realtime notifications"])


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket, token: str | None = None) -> None:
    user_id = _user_id_from_token(token)
    if token and user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await notification_connection_manager.connect(websocket, user_id=user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_connection_manager.disconnect(websocket)


def _user_id_from_token(token: str | None) -> int | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        return None
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None or not user.is_active:
            return None
        return user.id
    finally:
        db.close()
