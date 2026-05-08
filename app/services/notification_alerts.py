from sqlalchemy.orm import Session

from app.db.models import NotificationType, ResearcherProfile, User
from app.services.email_delivery import EmailProvider, get_email_provider
from app.services.notification_delivery import mark_notification_delivery_attempt
from app.services.notification_factory import create_digest_notification
from app.services.notification_preferences import get_or_create_preferences, preferences_allow_high_match_email
from app.services.notification_recommendations import top_recommendation_matches


def send_high_match_alerts(
    db: Session,
    user_id: int | None = None,
    provider: EmailProvider | None = None,
) -> dict:
    users = [db.get(User, user_id)] if user_id else db.query(User).filter(User.is_active.is_(True)).all()
    results = []
    for user in [item for item in users if item is not None]:
        preferences = get_or_create_preferences(db, user)
        if not preferences_allow_high_match_email(preferences):
            results.append({"user_id": user.id, "status": "skipped", "reason": "high_match_alerts_disabled"})
            continue
        profile = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == user.id).first()
        if profile is None:
            results.append({"user_id": user.id, "status": "skipped", "reason": "missing_profile"})
            continue
        matches = [
            item
            for item in top_recommendation_matches(db, profile, limit=3)
            if item["score"] >= preferences.min_alert_score
        ]
        if not matches:
            results.append({"user_id": user.id, "status": "skipped", "reason": "no_high_matches"})
            continue
        body = "New high-match opportunities:\n\n" + "\n".join(
            f"- {item['title']} ({item['score']}%): {item['reason']}" for item in matches
        )
        notification = create_digest_notification(
            db,
            user,
            profile,
            subject="New high-match research opportunities",
            body=body,
            notification_type=NotificationType.high_match_alert,
        )
        result = (provider or get_email_provider()).send(user.email, notification.subject, notification.body)
        mark_notification_delivery_attempt(notification, result.provider, user.email, result.message_id, result.error)
        db.commit()
        results.append({"user_id": user.id, "status": notification.status.value, "notification_id": notification.id})
    return {"processed": len(results), "results": results}
