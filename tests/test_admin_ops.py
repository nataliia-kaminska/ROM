from app.db.models import User, UserRole


def _admin_headers(client) -> dict[str, str]:
    auth = client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "strong-password-123", "full_name": "Admin User"},
    ).json()
    SessionLocal = client.app.state.testing_session_factory
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "admin@example.com").first()
        user.role = UserRole.admin
        db.commit()
    login = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "strong-password-123"},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_admin_dashboard_and_manual_opportunity_edit(client):
    headers = _admin_headers(client)
    created = client.post(
        "/opportunities",
        json={
            "title": "Original Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/original-grant",
            "keywords": ["climate"],
        },
    ).json()

    dashboard = client.get("/admin/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["analytics"]["total_opportunities"] == 1

    edited = client.put(
        f"/admin/opportunities/{created['id']}",
        headers=headers,
        json={
            "title": "Edited Grant",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/original-grant",
            "summary": "Edited summary",
        },
    )
    assert edited.status_code == 200
    assert edited.json()["title"] == "Edited Grant"

    audit = client.get("/admin/audit-log", headers=headers)
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "edit"


def test_admin_duplicate_merge_moves_status_records(client):
    headers = _admin_headers(client)
    profile = client.post(
        "/profiles",
        json={"full_name": "Merge User", "career_stage": "phd"},
    ).json()
    target = client.post(
        "/opportunities",
        json={
            "title": "Duplicate Grant",
            "opportunity_type": "grant",
            "source": "source_a",
            "url": "https://example.org/duplicate-a",
        },
    ).json()
    duplicate = client.post(
        "/opportunities",
        json={
            "title": "Duplicate Grant",
            "opportunity_type": "grant",
            "source": "source_a",
            "url": "https://example.org/duplicate-b",
        },
    ).json()
    client.put(
        f"/profiles/{profile['id']}/opportunities/{duplicate['id']}/status",
        json={"status": "saved"},
    )

    duplicates = client.get("/admin/opportunities/duplicates", headers=headers)
    assert duplicates.status_code == 200
    assert len(duplicates.json()) == 1

    merged = client.post(
        "/admin/opportunities/merge",
        headers=headers,
        json={"target_opportunity_id": target["id"], "duplicate_opportunity_ids": [duplicate["id"]]},
    )
    assert merged.status_code == 200

    statuses = client.get(f"/profiles/{profile['id']}/opportunities/statuses").json()
    assert statuses[0]["opportunity_id"] == target["id"]


def test_admin_duplicate_merge_handles_status_and_reminder_conflicts(client):
    headers = _admin_headers(client)
    profile = client.post(
        "/profiles",
        json={"full_name": "Conflict Merge User", "career_stage": "postdoc"},
    ).json()
    target = client.post(
        "/opportunities",
        json={
            "title": "Conflict Grant",
            "opportunity_type": "grant",
            "source": "source_a",
            "url": "https://example.org/conflict-a",
            "deadline": "2026-08-01",
        },
    ).json()
    duplicate = client.post(
        "/opportunities",
        json={
            "title": "Conflict Grant",
            "opportunity_type": "grant",
            "source": "source_a",
            "url": "https://example.org/conflict-b",
            "deadline": "2026-08-01",
        },
    ).json()
    client.put(
        f"/profiles/{profile['id']}/opportunities/{target['id']}/status",
        json={"status": "saved", "notes": "target note"},
    )
    client.put(
        f"/profiles/{profile['id']}/opportunities/{duplicate['id']}/status",
        json={"status": "planned", "notes": "duplicate note"},
    )
    client.post(
        f"/profiles/{profile['id']}/reminders",
        json={"opportunity_id": target["id"], "remind_on": "2026-07-01", "message": "target reminder"},
    )
    client.post(
        f"/profiles/{profile['id']}/reminders",
        json={"opportunity_id": duplicate["id"], "remind_on": "2026-07-01", "message": "duplicate reminder"},
    )

    merged = client.post(
        "/admin/opportunities/merge",
        headers=headers,
        json={"target_opportunity_id": target["id"], "duplicate_opportunity_ids": [duplicate["id"]]},
    )

    assert merged.status_code == 200
    statuses = client.get(f"/profiles/{profile['id']}/opportunities/statuses").json()
    assert len(statuses) == 1
    assert statuses[0]["opportunity_id"] == target["id"]
    assert statuses[0]["status"] == "planned"
    assert "target note" in statuses[0]["notes"]
    assert "duplicate note" in statuses[0]["notes"]

    reminders = client.get(f"/profiles/{profile['id']}/reminders", params={"include_completed": True}).json()
    custom_reminders = [reminder for reminder in reminders if reminder["remind_on"] == "2026-07-01"]
    assert len(custom_reminders) == 1
    assert custom_reminders[0]["opportunity_id"] == target["id"]
    assert "target reminder" in custom_reminders[0]["message"]
    assert "duplicate reminder" in custom_reminders[0]["message"]
