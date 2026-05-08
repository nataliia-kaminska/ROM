import json
import logging
import threading
import asyncio
from dataclasses import asdict, dataclass

from fastapi import WebSocket

from app.core.config import settings
from app.core.redis import get_redis_connection
from app.db.models import Notification


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RealtimeNotificationEvent:
    id: int
    user_id: int | None
    profile_id: int | None
    opportunity_id: int | None
    notification_type: str
    subject: str
    body: str
    status: str


class NotificationConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int | None, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int | None = None) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        for user_connections in self._connections.values():
            user_connections.discard(websocket)

    async def broadcast(self, event: RealtimeNotificationEvent) -> None:
        payload = asdict(event)
        recipients = set(self._connections.get(None, set()))
        if event.user_id is not None:
            recipients.update(self._connections.get(event.user_id, set()))
        disconnected = []
        for websocket in recipients:
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(websocket)


notification_connection_manager = NotificationConnectionManager()


def event_from_notification(notification: Notification) -> RealtimeNotificationEvent:
    return RealtimeNotificationEvent(
        id=notification.id,
        user_id=notification.user_id,
        profile_id=notification.profile_id,
        opportunity_id=notification.opportunity_id,
        notification_type=notification.notification_type.value,
        subject=notification.subject,
        body=notification.body,
        status=notification.status.value,
    )


def publish_notification_event(notification: Notification) -> None:
    if not settings.websocket_redis_enabled:
        return
    try:
        get_redis_connection().publish(
            settings.websocket_notifications_channel,
            json.dumps(asdict(event_from_notification(notification))),
        )
    except Exception:
        logger.exception("failed to publish realtime notification event")


def start_redis_notification_listener(app) -> None:
    if not settings.websocket_redis_enabled:
        return

    stop_event = threading.Event()
    loop = asyncio.get_running_loop()
    app.state.websocket_listener_stop = stop_event

    def listen() -> None:
        redis = get_redis_connection()
        pubsub = redis.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(settings.websocket_notifications_channel)
        while not stop_event.is_set():
            message = pubsub.get_message(timeout=1.0)
            if not message:
                continue
            try:
                payload = json.loads(message["data"])
                event = RealtimeNotificationEvent(**payload)
                asyncio.run_coroutine_threadsafe(notification_connection_manager.broadcast(event), loop)
            except Exception:
                logger.exception("failed to dispatch realtime notification event")

    thread = threading.Thread(target=listen, daemon=True)
    app.state.websocket_listener_thread = thread
    thread.start()


def stop_redis_notification_listener(app) -> None:
    stop_event = getattr(app.state, "websocket_listener_stop", None)
    if stop_event is not None:
        stop_event.set()
