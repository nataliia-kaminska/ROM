from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import (
    Notification,
    NotificationPreference,
    NotificationStatus,
    NotificationType,
    Opportunity,
    OpportunityReminder,
    ResearcherProfile,
    User,
)


def get_or_create_preferences(db: Session, user: User) -> NotificationPreference:
    preferences = db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
    if preferences:
        return preferences
    preferences = NotificationPreference(user_id=user.id)
    db.add(preferences)
    db.flush()
    return preferences


def create_deadline_notification(
    db: Session,
    reminder: OpportunityReminder,
    profile: ResearcherProfile | None,
    opportunity: Opportunity | None,
) -> Notification:
    subject = f"Deadline reminder: {opportunity.title if opportunity else 'Opportunity'}"
    notification = Notification(
        user_id=profile.user_id if profile else None,
        profile_id=reminder.profile_id,
        opportunity_id=reminder.opportunity_id,
        reminder_id=reminder.id,
        notification_type=NotificationType.deadline_reminder,
        recipient=profile.email if profile and profile.email else "",
        subject=subject,
        body=reminder.message or subject,
    )
    db.add(notification)
    db.flush()
    return notification


def mark_notification_sent(notification: Notification) -> Notification:
    notification.status = NotificationStatus.sent
    notification.sent_at = datetime.utcnow()
    return notification


def mark_notification_skipped(notification: Notification, reason: str) -> Notification:
    notification.status = NotificationStatus.skipped
    notification.skip_reason = reason
    return notification


def mark_notification_delivery_attempt(
    notification: Notification,
    provider: str,
    recipient: str,
    message_id: str = "",
    error: str = "",
) -> Notification:
    notification.provider = provider
    notification.recipient = recipient
    notification.provider_message_id = message_id
    notification.delivery_attempts += 1
    notification.last_error = error
    if error:
        notification.status = NotificationStatus.pending
    else:
        mark_notification_sent(notification)
    return notification


def create_digest_notification(
    db: Session,
    user: User,
    profile: ResearcherProfile | None,
    subject: str,
    body: str,
    notification_type: NotificationType,
) -> Notification:
    notification = Notification(
        user_id=user.id,
        profile_id=profile.id if profile else None,
        notification_type=notification_type,
        recipient=user.email,
        subject=subject,
        body=body,
    )
    db.add(notification)
    db.flush()
    return notification


def mark_notification_read(notification: Notification) -> Notification:
    notification.status = NotificationStatus.read
    notification.read_at = datetime.utcnow()
    return notification


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
