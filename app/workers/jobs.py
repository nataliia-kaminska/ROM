from datetime import date

from app.db.models import OpportunityReminder
from app.db.session import SessionLocal
from app.services.email_delivery import get_email_provider
from app.services.embeddings import refresh_all_embeddings, refresh_opportunity_embeddings, refresh_profile_embeddings
from app.services.grants_gov_ingestion import ingest_grants_gov
from app.services.notifications import send_high_match_alerts, send_reminder_email, send_weekly_digest
from app.services.reminders import list_due_reminders


def ingest_grants_gov_job(keyword: str, limit: int = 10, import_results: bool = True) -> dict:
    result = ingest_grants_gov(keyword=keyword, limit=limit, import_results=import_results)
    return result.model_dump(mode="json")


def scan_due_reminders_job(today: str | None = None) -> dict:
    scan_date = date.fromisoformat(today) if today else date.today()
    db = SessionLocal()
    try:
        reminders = list_due_reminders(db, scan_date)
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
        return send_reminder_email(db, reminder, provider=get_email_provider())
    finally:
        db.close()


def send_weekly_digest_job(user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        return send_weekly_digest(db, user_id=user_id, provider=get_email_provider())
    finally:
        db.close()


def send_high_match_alerts_job(user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        return send_high_match_alerts(db, user_id=user_id, provider=get_email_provider())
    finally:
        db.close()


def refresh_opportunity_embeddings_job() -> dict:
    db = SessionLocal()
    try:
        return refresh_opportunity_embeddings(db)
    finally:
        db.close()


def refresh_profile_embeddings_job() -> dict:
    db = SessionLocal()
    try:
        return refresh_profile_embeddings(db)
    finally:
        db.close()


def refresh_all_embeddings_job() -> dict:
    db = SessionLocal()
    try:
        return refresh_all_embeddings(db)
    finally:
        db.close()
