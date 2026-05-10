import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Notification, NotificationStatus, Opportunity, OpportunityReminder, ResearcherProfile, User
from app.services.email_delivery import EmailProvider, get_email_provider
from app.services.notification_factory import create_deadline_notification
from app.services.notification_preferences import get_or_create_preferences, preferences_allow_deadline_email


logger = logging.getLogger(__name__)


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


def mark_notification_read(notification: Notification) -> Notification:
    notification.status = NotificationStatus.read
    notification.read_at = datetime.utcnow()
    return notification


def send_reminder_email(
    db: Session,
    reminder: OpportunityReminder,
    provider: EmailProvider | None = None,
) -> dict:
    opportunity = db.get(Opportunity, reminder.opportunity_id)
    profile = db.get(ResearcherProfile, reminder.profile_id)
    notification = create_deadline_notification(db, reminder, profile, opportunity)
    if profile is None or not profile.email:
        mark_notification_skipped(notification, "missing_profile_email")
        db.commit()
        logger.info("reminder notification skipped reminder_id=%s reason=missing_profile_email", reminder.id)
        return {"reminder_id": reminder.id, "status": "skipped", "reason": "missing_profile_email"}

    preferences = None
    if profile.user_id:
        user = db.get(User, profile.user_id)
        if user:
            preferences = get_or_create_preferences(db, user)
    if not preferences_allow_deadline_email(preferences):
        mark_notification_skipped(notification, "email_disabled")
        db.commit()
        logger.info("reminder notification skipped reminder_id=%s reason=email_disabled", reminder.id)
        return {"reminder_id": reminder.id, "status": "skipped", "reason": "email_disabled"}

    result = (provider or get_email_provider()).send(profile.email, notification.subject, notification.body)
    mark_notification_delivery_attempt(
        notification,
        provider=result.provider,
        recipient=profile.email,
        message_id=result.message_id,
        error=result.error,
    )
    db.commit()
    logger.info(
        "reminder notification delivery attempted reminder_id=%s notification_id=%s status=%s provider=%s error=%s",
        reminder.id,
        notification.id,
        notification.status.value,
        notification.provider,
        bool(notification.last_error),
    )
    return {
        "reminder_id": reminder.id,
        "status": notification.status.value,
        "email": profile.email,
        "notification_id": notification.id,
        "provider": notification.provider,
        "message_id": notification.provider_message_id,
        "error": notification.last_error,
    }
