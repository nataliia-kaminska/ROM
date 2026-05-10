import logging

from sqlalchemy.orm import Session

from app.db.models import NotificationType, ResearcherProfile, User
from app.services.email_delivery import EmailProvider, get_email_provider
from app.services.notification_delivery import mark_notification_delivery_attempt
from app.services.notification_factory import create_digest_notification
from app.services.notification_preferences import get_or_create_preferences, preferences_allow_digest_email
from app.services.notification_recommendations import top_recommendation_matches


logger = logging.getLogger(__name__)


def send_weekly_digest(
    db: Session,
    user_id: int | None = None,
    provider: EmailProvider | None = None,
) -> dict:
    users = [db.get(User, user_id)] if user_id else db.query(User).filter(User.is_active.is_(True)).all()
    results = []
    for user in [item for item in users if item is not None]:
        preferences = get_or_create_preferences(db, user)
        if not preferences_allow_digest_email(preferences):
            logger.info("weekly digest skipped user_id=%s reason=weekly_digest_disabled", user.id)
            results.append({"user_id": user.id, "status": "skipped", "reason": "weekly_digest_disabled"})
            continue
        profile = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == user.id).first()
        if profile is None:
            logger.info("weekly digest skipped user_id=%s reason=missing_profile", user.id)
            results.append({"user_id": user.id, "status": "skipped", "reason": "missing_profile"})
            continue
        top_matches = top_recommendation_matches(db, profile, limit=5)
        if not top_matches:
            logger.info("weekly digest skipped user_id=%s reason=no_matches", user.id)
            results.append({"user_id": user.id, "status": "skipped", "reason": "no_matches"})
            continue
        body = "Your top research opportunities this week:\n\n" + "\n".join(
            f"- {item['title']} ({item['score']}%): {item['reason']}" for item in top_matches
        )
        notification = create_digest_notification(
            db,
            user,
            profile,
            subject="Weekly research opportunity digest",
            body=body,
            notification_type=NotificationType.weekly_digest,
        )
        result = (provider or get_email_provider()).send(user.email, notification.subject, notification.body)
        mark_notification_delivery_attempt(notification, result.provider, user.email, result.message_id, result.error)
        db.commit()
        logger.info("weekly digest sent user_id=%s notification_id=%s matches=%s", user.id, notification.id, len(top_matches))
        results.append({"user_id": user.id, "status": notification.status.value, "notification_id": notification.id})
    return {"processed": len(results), "results": results}
