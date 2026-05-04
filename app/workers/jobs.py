import logging
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.models import Opportunity, OpportunityReminder, ReminderStatus, ResearcherProfile, User
from app.db.models import ResearcherProfileDetails
from app.db.session import SessionLocal
from app.services.embeddings import ensure_opportunity_embedding, ensure_profile_embedding, vector_literal
from app.services.grants_gov_ingestion import ingest_grants_gov
from app.services.notifications import (
    create_deadline_notification,
    get_or_create_preferences,
    mark_notification_sent,
    mark_notification_skipped,
    preferences_allow_deadline_email,
)


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

        logger.info(
            "email notification reminder_id=%s email=%s opportunity_id=%s title=%s",
            reminder.id,
            profile.email,
            reminder.opportunity_id,
            opportunity.title if opportunity else "",
        )
        mark_notification_sent(notification)
        db.commit()
        return {"reminder_id": reminder_id, "status": "sent", "email": profile.email, "notification_id": notification.id}
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
