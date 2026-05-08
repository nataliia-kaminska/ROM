from sqlalchemy.orm import Session

from app.db.models import NotificationPreference, User
from app.repositories import notifications as notification_repository


def get_or_create_preferences(db: Session, user: User) -> NotificationPreference:
    return notification_repository.get_or_create_preferences(db, user)


def preferences_allow_deadline_email(preferences: NotificationPreference | None) -> bool:
    if preferences is None:
        return True
    return preferences.email_enabled and preferences.deadline_reminders_enabled


def preferences_allow_digest_email(preferences: NotificationPreference | None) -> bool:
    if preferences is None:
        return True
    return preferences.email_enabled and preferences.weekly_digest_enabled


def preferences_allow_high_match_email(preferences: NotificationPreference | None) -> bool:
    if preferences is None:
        return True
    return preferences.email_enabled and preferences.high_match_alerts_enabled
