from datetime import date

from app.db.models import Notification
from app.main import app
from app.workers.jobs import send_high_match_alerts_job, send_reminder_email_job, send_weekly_digest_job


def _register(client):
    response = client.post(
        "/auth/register",
        json={"email": "notify@example.com", "password": "strong-password-123", "full_name": "Notify User"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _current_user_id(client, headers: dict[str, str]) -> int:
    return client.get("/auth/me", headers=headers).json()["id"]


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


def test_reminder_email_job_records_notification(client, monkeypatch, admin_headers):
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
        headers=admin_headers,
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
    assert result["provider"] == "console"
    assert result["message_id"].startswith("console-")
    response = client.get("/notifications?include_read=true", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["notification_type"] == "deadline_reminder"
    assert response.json()[0]["delivery_attempts"] == 1


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


def test_weekly_digest_job_records_notification(client, monkeypatch, admin_headers):
    headers = _register(client)
    profile = client.post(
        "/profiles",
        headers=headers,
        json={
            "full_name": "Digest User",
            "email": "notify@example.com",
            "career_stage": "phd",
            "disciplines": ["Computer Science"],
            "keywords": ["machine learning"],
        },
    ).json()
    client.post(
        "/opportunities",
        headers=admin_headers,
        json={
            "title": "Machine Learning Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/ml-digest",
            "disciplines": ["Computer Science"],
            "keywords": ["machine learning"],
            "career_stages": ["phd"],
        },
    )
    monkeypatch.setattr("app.workers.jobs.SessionLocal", app.state.testing_session_factory)

    result = send_weekly_digest_job(user_id=_current_user_id(client, headers))

    assert result["processed"] == 1
    response = client.get("/notifications?include_read=true", headers=headers)
    assert any(item["notification_type"] == "weekly_digest" for item in response.json())


def test_high_match_alert_job_respects_threshold(client, monkeypatch, admin_headers):
    headers = _register(client)
    client.put(
        "/notifications/preferences",
        headers=headers,
        json={
            "email_enabled": True,
            "deadline_reminders_enabled": True,
            "weekly_digest_enabled": True,
            "high_match_alerts_enabled": True,
            "min_alert_score": 50,
        },
    )
    profile = client.post(
        "/profiles",
        headers=headers,
        json={
            "full_name": "Alert User",
            "email": "notify@example.com",
            "career_stage": "phd",
            "disciplines": ["Physics"],
            "keywords": ["quantum"],
        },
    ).json()
    client.post(
        "/opportunities",
        headers=admin_headers,
        json={
            "title": "Quantum Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/quantum-alert",
            "disciplines": ["Physics"],
            "keywords": ["quantum"],
            "career_stages": ["phd"],
        },
    )
    monkeypatch.setattr("app.workers.jobs.SessionLocal", app.state.testing_session_factory)

    result = send_high_match_alerts_job(user_id=_current_user_id(client, headers))

    assert result["processed"] == 1
    response = client.get("/notifications?include_read=true", headers=headers)
    assert any(item["notification_type"] == "high_match_alert" for item in response.json())


def test_delivery_failure_is_recorded(client, monkeypatch, admin_headers):
    class FailingProvider:
        def send(self, recipient: str, subject: str, body: str):
            from app.services.email_delivery import EmailDeliveryResult

            return EmailDeliveryResult(provider="smtp", message_id="smtp-test", status="failed", error="connection refused")

    headers = _register(client)
    profile = client.post(
        "/profiles",
        headers=headers,
        json={"full_name": "Fail User", "email": "notify@example.com", "career_stage": "phd"},
    ).json()
    opportunity = client.post(
        "/opportunities",
        headers=admin_headers,
        json={
            "title": "Failure Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/failure-grant",
        },
    ).json()
    reminder = client.post(
        f"/profiles/{profile['id']}/reminders",
        headers=headers,
        json={"opportunity_id": opportunity["id"], "remind_on": str(date.today())},
    ).json()
    monkeypatch.setattr("app.workers.jobs.SessionLocal", app.state.testing_session_factory)
    monkeypatch.setattr("app.workers.jobs.get_email_provider", lambda: FailingProvider())

    result = send_reminder_email_job(reminder["id"])

    assert result["status"] == "pending"
    assert result["error"] == "connection refused"
    response = client.get("/notifications?include_read=true", headers=headers)
    assert response.json()[0]["last_error"] == "connection refused"
