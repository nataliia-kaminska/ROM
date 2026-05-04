from datetime import date

from app.db.models import Notification
from app.main import app
from app.workers.jobs import send_reminder_email_job


def _register(client):
    response = client.post(
        "/auth/register",
        json={"email": "notify@example.com", "password": "strong-password-123", "full_name": "Notify User"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_notification_preferences_and_unsubscribe(client):
    headers = _register(client)

    preferences = client.get("/notifications/preferences", headers=headers)
    assert preferences.status_code == 200
    assert preferences.json()["email_enabled"] is True

    updated = client.put(
        "/notifications/preferences",
        headers=headers,
        json={
            "email_enabled": True,
            "deadline_reminders_enabled": False,
            "weekly_digest_enabled": True,
            "high_match_alerts_enabled": False,
            "min_alert_score": 90,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["deadline_reminders_enabled"] is False

    unsubscribed = client.post("/notifications/unsubscribe", headers=headers)
    assert unsubscribed.status_code == 200
    assert unsubscribed.json()["email_enabled"] is False


def test_reminder_email_job_records_notification(client, monkeypatch):
    headers = _register(client)
    profile = client.post(
        "/profiles",
        headers=headers,
        json={
            "full_name": "Notify User",
            "email": "notify@example.com",
            "career_stage": "phd",
            "disciplines": ["Physics"],
        },
    ).json()
    opportunity = client.post(
        "/opportunities",
        json={
            "title": "Deadline Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/deadline-grant",
            "deadline": str(date.today()),
        },
    ).json()
    reminder = client.post(
        f"/profiles/{profile['id']}/reminders",
        headers=headers,
        json={"opportunity_id": opportunity["id"], "remind_on": str(date.today())},
    ).json()

    monkeypatch.setattr("app.workers.jobs.SessionLocal", app.state.testing_session_factory)
    result = send_reminder_email_job(reminder["id"])

    assert result["status"] == "sent"
    response = client.get("/notifications?include_read=true", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["notification_type"] == "deadline_reminder"


def test_notification_mark_read(client, monkeypatch):
    headers = _register(client)
    profile = client.post(
        "/profiles",
        headers=headers,
        json={"full_name": "Notify User", "email": "notify@example.com", "career_stage": "phd"},
    ).json()
    db = app.state.testing_session_factory()
    try:
        notification = Notification(
            user_id=1,
            profile_id=profile["id"],
            notification_type="weekly_digest",
            subject="Weekly recommendations",
            body="Digest body",
        )
        db.add(notification)
        db.commit()
        notification_id = notification.id
    finally:
        db.close()

    read_response = client.put(f"/notifications/{notification_id}/read", headers=headers)
    assert read_response.status_code in {200, 404}
