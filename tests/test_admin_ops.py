def test_admin_dashboard_and_manual_opportunity_edit(client):
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

    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["analytics"]["total_opportunities"] == 1

    edited = client.put(
        f"/admin/opportunities/{created['id']}",
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

    audit = client.get("/admin/audit-log")
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "edit"


def test_admin_duplicate_merge_moves_status_records(client):
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

    duplicates = client.get("/admin/opportunities/duplicates")
    assert duplicates.status_code == 200
    assert len(duplicates.json()) == 1

    merged = client.post(
        "/admin/opportunities/merge",
        json={"target_opportunity_id": target["id"], "duplicate_opportunity_ids": [duplicate["id"]]},
    )
    assert merged.status_code == 200

    statuses = client.get(f"/profiles/{profile['id']}/opportunities/statuses").json()
    assert statuses[0]["opportunity_id"] == target["id"]
