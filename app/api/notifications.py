from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.repositories import notifications as notification_repository
from app.schemas.notifications import NotificationPreferenceRead, NotificationPreferenceUpdate, NotificationRead
from app.services.notification_delivery import mark_notification_read
from app.services.notification_preferences import get_or_create_preferences


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    include_read: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
    return notification_repository.list_notifications_for_user(
        db,
        current_user,
        include_read=include_read,
        limit=limit,
        offset=offset,
    )


@router.put("/{notification_id}/read", response_model=NotificationRead)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationRead:
    notification = notification_repository.get_user_notification(db, notification_id, current_user)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    mark_notification_read(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/preferences", response_model=NotificationPreferenceRead)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceRead:
    preferences = get_or_create_preferences(db, current_user)
    db.commit()
    db.refresh(preferences)
    return preferences


@router.put("/preferences", response_model=NotificationPreferenceRead)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceRead:
    preferences = get_or_create_preferences(db, current_user)
    preferences.email_enabled = payload.email_enabled
    preferences.deadline_reminders_enabled = payload.deadline_reminders_enabled
    preferences.weekly_digest_enabled = payload.weekly_digest_enabled
    preferences.high_match_alerts_enabled = payload.high_match_alerts_enabled
    preferences.min_alert_score = payload.min_alert_score
    db.commit()
    db.refresh(preferences)
    return preferences


@router.post("/unsubscribe", response_model=NotificationPreferenceRead)
def unsubscribe(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceRead:
    preferences = get_or_create_preferences(db, current_user)
    preferences.email_enabled = False
    preferences.deadline_reminders_enabled = False
    preferences.weekly_digest_enabled = False
    preferences.high_match_alerts_enabled = False
    db.commit()
    db.refresh(preferences)
    return preferences
