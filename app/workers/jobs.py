import logging
from datetime import date

from app.db.models import OpportunityReminder
from app.db.session import SessionLocal
from app.services.email_delivery import get_email_provider
from app.services.embeddings import refresh_all_embeddings, refresh_opportunity_embeddings, refresh_profile_embeddings
from app.services.grants_gov_ingestion import ingest_grants_gov
from app.services.notifications import send_high_match_alerts, send_reminder_email, send_weekly_digest
from app.services.reminders import list_due_reminders


logger = logging.getLogger(__name__)


def ingest_grants_gov_job(keyword: str, limit: int = 10, import_results: bool = True) -> dict:
    logger.info("job start ingest_grants_gov keyword=%s limit=%s import_results=%s", keyword, limit, import_results)
    result = ingest_grants_gov(keyword=keyword, limit=limit, import_results=import_results)
    payload = result.model_dump(mode="json")
    logger.info(
        "job complete ingest_grants_gov keyword=%s imported=%s skipped=%s",
        keyword,
        payload.get("imported_count"),
        payload.get("skipped_count"),
    )
    return payload


def scan_due_reminders_job(today: str | None = None) -> dict:
    scan_date = date.fromisoformat(today) if today else date.today()
    logger.info("job start scan_due_reminders scan_date=%s", scan_date.isoformat())
    db = SessionLocal()
    try:
        reminders = list_due_reminders(db, scan_date)
        notification_results = [send_reminder_email_job(reminder.id) for reminder in reminders]
        logger.info("job complete scan_due_reminders scan_date=%s due_count=%s", scan_date.isoformat(), len(reminders))
        return {
            "scan_date": scan_date.isoformat(),
            "due_count": len(reminders),
            "notifications": notification_results,
        }
    finally:
        db.close()


def send_reminder_email_job(reminder_id: int) -> dict:
    logger.info("job start send_reminder_email reminder_id=%s", reminder_id)
    db = SessionLocal()
    try:
        reminder = db.get(OpportunityReminder, reminder_id)
        if reminder is None:
            logger.warning("job skipped send_reminder_email reminder_id=%s reason=not_found", reminder_id)
            return {"reminder_id": reminder_id, "status": "skipped", "reason": "not_found"}
        result = send_reminder_email(db, reminder, provider=get_email_provider())
        logger.info("job complete send_reminder_email reminder_id=%s status=%s", reminder_id, result.get("status"))
        return result
    finally:
        db.close()


def send_weekly_digest_job(user_id: int | None = None) -> dict:
    logger.info("job start send_weekly_digest user_id=%s", user_id)
    db = SessionLocal()
    try:
        result = send_weekly_digest(db, user_id=user_id, provider=get_email_provider())
        logger.info("job complete send_weekly_digest processed=%s", result.get("processed"))
        return result
    finally:
        db.close()


def send_high_match_alerts_job(user_id: int | None = None) -> dict:
    logger.info("job start send_high_match_alerts user_id=%s", user_id)
    db = SessionLocal()
    try:
        result = send_high_match_alerts(db, user_id=user_id, provider=get_email_provider())
        logger.info("job complete send_high_match_alerts processed=%s", result.get("processed"))
        return result
    finally:
        db.close()


def refresh_opportunity_embeddings_job() -> dict:
    logger.info("job start refresh_opportunity_embeddings")
    db = SessionLocal()
    try:
        result = refresh_opportunity_embeddings(db)
        logger.info("job complete refresh_opportunity_embeddings count=%s", result.get("opportunity_count"))
        return result
    finally:
        db.close()


def refresh_profile_embeddings_job() -> dict:
    logger.info("job start refresh_profile_embeddings")
    db = SessionLocal()
    try:
        result = refresh_profile_embeddings(db)
        logger.info("job complete refresh_profile_embeddings count=%s", result.get("profile_count"))
        return result
    finally:
        db.close()


def refresh_all_embeddings_job() -> dict:
    logger.info("job start refresh_all_embeddings")
    db = SessionLocal()
    try:
        result = refresh_all_embeddings(db)
        logger.info("job complete refresh_all_embeddings profiles=%s opportunities=%s", result["profiles"], result["opportunities"])
        return result
    finally:
        db.close()
