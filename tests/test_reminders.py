from datetime import date, timedelta


def _create_profile_and_opportunity(client, admin_headers):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Oleh Danylenko",
            "career_stage": "phd",
            "disciplines": ["Physics"],
            "keywords": ["quantum"],
        },
    ).json()
    opportunity = client.post(
        "/opportunities",
        headers=admin_headers,
        json={
            "title": "Quantum Research Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/quantum",
            "disciplines": ["Physics"],
            "keywords": ["quantum"],
            "deadline": str(date.today() + timedelta(days=21)),
        },
    ).json()
    return profile, opportunity


def test_manual_reminder_can_be_created_listed_and_completed(client, admin_headers):
    profile, opportunity = _create_profile_and_opportunity(client, admin_headers)
    remind_on = date.today()

    create_response = client.post(
        f"/profiles/{profile['id']}/reminders",
        json={
            "opportunity_id": opportunity["id"],
            "remind_on": str(remind_on),
            "message": "Draft proposal outline",
        },
    )

    assert create_response.status_code == 201
    reminder = create_response.json()
    assert reminder["status"] == "pending"

    due_response = client.get(f"/profiles/{profile['id']}/reminders?due_only=true")

    assert due_response.status_code == 200
    assert len(due_response.json()) == 1

    complete_response = client.put(f"/profiles/{profile['id']}/reminders/{reminder['id']}/complete")

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    active_response = client.get(f"/profiles/{profile['id']}/reminders")

    assert active_response.status_code == 200
    assert active_response.json() == []


def test_saving_opportunity_creates_deadline_reminder(client, admin_headers):
    profile, opportunity = _create_profile_and_opportunity(client, admin_headers)

    status_response = client.put(
        f"/profiles/{profile['id']}/opportunities/{opportunity['id']}/status",
        json={"status": "saved"},
    )

    assert status_response.status_code == 200

    reminders_response = client.get(f"/profiles/{profile['id']}/reminders")

    assert reminders_response.status_code == 200
    reminders = reminders_response.json()
    assert len(reminders) == 1
    assert reminders[0]["opportunity_id"] == opportunity["id"]
    assert reminders[0]["remind_on"] == str(date.today() + timedelta(days=14))
