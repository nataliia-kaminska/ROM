from sqlalchemy.orm import Session

from app.db.models import Notification, NotificationPreference, NotificationStatus, ResearcherProfile, User


def get_or_create_preferences(db: Session, user: User) -> NotificationPreference:
    preferences = db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
    if preferences:
        return preferences
    preferences = NotificationPreference(user_id=user.id)
    db.add(preferences)
    db.flush()
    return preferences


def list_notifications_for_user(
    db: Session,
    user: User,
    include_read: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Notification]:
    profile_ids = [row[0] for row in db.query(ResearcherProfile.id).filter(ResearcherProfile.user_id == user.id).all()]
    query = db.query(Notification).filter((Notification.user_id == user.id) | (Notification.profile_id.in_(profile_ids)))
    if not include_read:
        query = query.filter(Notification.status != NotificationStatus.read)
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


def get_user_notification(db: Session, notification_id: int, user: User) -> Notification | None:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        return None
    return notification
