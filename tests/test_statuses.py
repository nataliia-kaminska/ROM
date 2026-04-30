def test_profile_can_save_opportunity_status(client):
    profile_response = client.post(
        "/profiles",
        json={
            "full_name": "Marta Ivanenko",
            "career_stage": "postdoc",
            "disciplines": ["Chemistry"],
            "keywords": ["materials"],
        },
    )
    opportunity_response = client.post(
        "/opportunities",
        json={
            "title": "Materials Science Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/materials",
            "disciplines": ["Chemistry"],
            "keywords": ["materials"],
            "career_stages": ["postdoc"],
        },
    )

    profile_id = profile_response.json()["id"]
    opportunity_id = opportunity_response.json()["id"]

    status_response = client.put(
        f"/profiles/{profile_id}/opportunities/{opportunity_id}/status",
        json={"status": "saved", "notes": "Interesting fit"},
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "saved"

    list_response = client.get(f"/profiles/{profile_id}/opportunities/statuses")

    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1
