from app.services.notification_alerts import send_high_match_alerts
from app.services.notification_delivery import (
    mark_notification_delivery_attempt,
    mark_notification_read,
    mark_notification_sent,
    mark_notification_skipped,
    send_reminder_email,
)
from app.services.notification_digests import send_weekly_digest
from app.services.notification_factory import create_deadline_notification, create_digest_notification
from app.services.notification_preferences import (
    get_or_create_preferences,
    preferences_allow_deadline_email,
    preferences_allow_digest_email,
    preferences_allow_high_match_email,
)
from app.services.notification_recommendations import top_recommendation_matches

__all__ = [
    "create_deadline_notification",
    "create_digest_notification",
    "get_or_create_preferences",
    "mark_notification_delivery_attempt",
    "mark_notification_read",
    "mark_notification_sent",
    "mark_notification_skipped",
    "preferences_allow_deadline_email",
    "preferences_allow_digest_email",
    "preferences_allow_high_match_email",
    "send_high_match_alerts",
    "send_reminder_email",
    "send_weekly_digest",
    "top_recommendation_matches",
]
