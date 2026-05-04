from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import Notification, NotificationStatus, ResearcherProfile, User
from app.db.session import get_db
from app.schemas.notifications import NotificationPreferenceRead, NotificationPreferenceUpdate, NotificationRead
from app.services.notifications import get_or_create_preferences, mark_notification_read


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    include_read: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
    profile_ids = [row[0] for row in db.query(ResearcherProfile.id).filter(ResearcherProfile.user_id == current_user.id).all()]
    query = db.query(Notification).filter(
        (Notification.user_id == current_user.id) | (Notification.profile_id.in_(profile_ids))
    )
    if not include_read:
        query = query.filter(Notification.status != NotificationStatus.read)
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


@router.put("/{notification_id}/read", response_model=NotificationRead)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationRead:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
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
