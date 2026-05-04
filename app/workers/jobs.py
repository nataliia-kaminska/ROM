import logging
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.models import Opportunity, OpportunityReminder, ProfileOpportunityStatus, ReminderStatus, ResearcherProfile, User
from app.db.models import NotificationType, ResearcherProfileDetails
from app.db.session import SessionLocal
from app.services.email_delivery import get_email_provider
from app.services.embeddings import ensure_opportunity_embedding, ensure_profile_embedding, vector_literal
from app.services.grants_gov_ingestion import ingest_grants_gov
from app.services.notifications import (
    create_deadline_notification,
    create_digest_notification,
    get_or_create_preferences,
    mark_notification_delivery_attempt,
    mark_notification_skipped,
    preferences_allow_deadline_email,
    preferences_allow_digest_email,
    preferences_allow_high_match_email,
)
from app.services.recommendation_engine import build_history_signals, score_opportunity


logger = logging.getLogger(__name__)


def ingest_grants_gov_job(keyword: str, limit: int = 10, import_results: bool = True) -> dict:
    result = ingest_grants_gov(keyword=keyword, limit=limit, import_results=import_results)
    return result.model_dump(mode="json")


def scan_due_reminders_job(today: str | None = None) -> dict:
    scan_date = date.fromisoformat(today) if today else date.today()
    db = SessionLocal()
    try:
        reminders = _due_reminders(db, scan_date)
        notification_results = [send_reminder_email_job(reminder.id) for reminder in reminders]
        return {
            "scan_date": scan_date.isoformat(),
            "due_count": len(reminders),
            "notifications": notification_results,
        }
    finally:
        db.close()


def send_reminder_email_job(reminder_id: int) -> dict:
    db = SessionLocal()
    try:
        reminder = db.get(OpportunityReminder, reminder_id)
        if reminder is None:
            return {"reminder_id": reminder_id, "status": "skipped", "reason": "not_found"}
        opportunity = db.get(Opportunity, reminder.opportunity_id)
        profile = db.get(ResearcherProfile, reminder.profile_id)
        notification = create_deadline_notification(db, reminder, profile, opportunity)
        if profile is None or not profile.email:
            mark_notification_skipped(notification, "missing_profile_email")
            db.commit()
            return {"reminder_id": reminder_id, "status": "skipped", "reason": "missing_profile_email"}
        preferences = None
        if profile.user_id:
            user = db.get(User, profile.user_id)
            if user:
                preferences = get_or_create_preferences(db, user)
        if not preferences_allow_deadline_email(preferences):
            mark_notification_skipped(notification, "email_disabled")
            db.commit()
            return {"reminder_id": reminder_id, "status": "skipped", "reason": "email_disabled"}

        result = get_email_provider().send(profile.email, notification.subject, notification.body)
        mark_notification_delivery_attempt(
            notification,
            provider=result.provider,
            recipient=profile.email,
            message_id=result.message_id,
            error=result.error,
        )
        db.commit()
        return {
            "reminder_id": reminder_id,
            "status": notification.status.value,
            "email": profile.email,
            "notification_id": notification.id,
            "provider": notification.provider,
            "message_id": notification.provider_message_id,
            "error": notification.last_error,
        }
    finally:
        db.close()


def send_weekly_digest_job(user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        users = [db.get(User, user_id)] if user_id else db.query(User).filter(User.is_active.is_(True)).all()
        results = []
        for user in [item for item in users if item is not None]:
            preferences = get_or_create_preferences(db, user)
            if not preferences_allow_digest_email(preferences):
                results.append({"user_id": user.id, "status": "skipped", "reason": "weekly_digest_disabled"})
                continue
            profile = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == user.id).first()
            if profile is None:
                results.append({"user_id": user.id, "status": "skipped", "reason": "missing_profile"})
                continue
            top_matches = _top_matches(db, profile, limit=5)
            if not top_matches:
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
            result = get_email_provider().send(user.email, notification.subject, notification.body)
            mark_notification_delivery_attempt(notification, result.provider, user.email, result.message_id, result.error)
            db.commit()
            results.append({"user_id": user.id, "status": notification.status.value, "notification_id": notification.id})
        return {"processed": len(results), "results": results}
    finally:
        db.close()


def send_high_match_alerts_job(user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
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
            matches = [item for item in _top_matches(db, profile, limit=3) if item["score"] >= preferences.min_alert_score]
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
            result = get_email_provider().send(user.email, notification.subject, notification.body)
            mark_notification_delivery_attempt(notification, result.provider, user.email, result.message_id, result.error)
            db.commit()
            results.append({"user_id": user.id, "status": notification.status.value, "notification_id": notification.id})
        return {"processed": len(results), "results": results}
    finally:
        db.close()


def refresh_opportunity_embeddings_job() -> dict:
    db = SessionLocal()
    try:
        opportunities = db.query(Opportunity).all()
        for opportunity in opportunities:
            opportunity.opportunity_embedding = ""
            vector = ensure_opportunity_embedding(opportunity)
            if db.bind and db.bind.dialect.name == "postgresql":
                db.execute(
                    text(
                        "UPDATE opportunities "
                        "SET opportunity_embedding_vector = CAST(:vector AS vector) "
                        "WHERE id = :id"
                    ),
                    {"vector": vector_literal(vector), "id": opportunity.id},
                )
        db.commit()
        return {"opportunity_count": len(opportunities)}
    finally:
        db.close()


def refresh_profile_embeddings_job() -> dict:
    db = SessionLocal()
    try:
        details_records = db.query(ResearcherProfileDetails).all()
        refreshed = 0
        for details in details_records:
            profile = db.get(ResearcherProfile, details.profile_id)
            if profile is None:
                continue
            details.profile_embedding = ""
            vector = ensure_profile_embedding(profile, details)
            if db.bind and db.bind.dialect.name == "postgresql":
                db.execute(
                    text(
                        "UPDATE researcher_profile_details "
                        "SET profile_embedding_vector = CAST(:vector AS vector) "
                        "WHERE id = :id"
                    ),
                    {"vector": vector_literal(vector), "id": details.id},
                )
            refreshed += 1
        db.commit()
        return {"profile_count": refreshed}
    finally:
        db.close()


def refresh_all_embeddings_job() -> dict:
    return {
        "profiles": refresh_profile_embeddings_job(),
        "opportunities": refresh_opportunity_embeddings_job(),
    }


def _top_matches(db: Session, profile: ResearcherProfile, limit: int) -> list[dict]:
    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    statuses = db.query(ProfileOpportunityStatus).filter(ProfileOpportunityStatus.profile_id == profile.id).all()
    opportunities = db.query(Opportunity).all()
    opportunities_by_id = {opportunity.id: opportunity for opportunity in opportunities}
    statuses_by_id = {status.opportunity_id: status for status in statuses}
    history = build_history_signals(statuses, opportunities_by_id)
    scored = []
    for opportunity in opportunities:
        result = score_opportunity(profile, opportunity, details, statuses_by_id.get(opportunity.id), history)
        scored.append(
            {
                "title": opportunity.title,
                "score": result.final_score,
                "reason": result.reasons[0] if result.reasons else "Recommended match",
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]


def _due_reminders(db: Session, scan_date: date) -> list[OpportunityReminder]:
    return (
        db.query(OpportunityReminder)
        .filter(
            OpportunityReminder.status == ReminderStatus.pending,
            OpportunityReminder.remind_on <= scan_date,
        )
        .order_by(OpportunityReminder.remind_on.asc())
        .all()
    )
