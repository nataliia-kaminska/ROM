def test_create_opportunity_rejects_duplicate_url(client, admin_headers):
    payload = {
        "title": "Duplicate Guard Grant",
        "opportunity_type": "grant",
        "source": "manual_seed",
        "url": "https://example.org/duplicate-guard",
    }

    first_response = client.post("/opportunities", headers=admin_headers, json=payload)
    second_response = client.post("/opportunities", headers=admin_headers, json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_list_opportunities_supports_filters_and_pagination(client, admin_headers):
    opportunities = [
        {
            "title": "German AI Fellowship",
            "opportunity_type": "fellowship",
            "source": "daad_curated",
            "url": "https://example.org/daad-ai",
            "summary": "AI research in Germany.",
            "disciplines": ["Computer Science"],
            "keywords": ["artificial intelligence"],
            "countries": ["Germany"],
            "career_stages": ["phd"],
            "deadline": "2026-09-01",
        },
        {
            "title": "French Climate Grant",
            "opportunity_type": "grant",
            "source": "campus_france",
            "url": "https://example.org/france-climate",
            "summary": "Climate research in France.",
            "disciplines": ["Environmental Science"],
            "keywords": ["climate"],
            "countries": ["France"],
            "career_stages": ["postdoc"],
            "deadline": "2026-10-01",
        },
    ]
    for opportunity in opportunities:
        assert client.post("/opportunities", headers=admin_headers, json=opportunity).status_code == 201

    filtered = client.get(
        "/opportunities",
        params={
            "source": "daad_curated",
            "opportunity_type": "fellowship",
            "country": "Germany",
            "career_stage": "phd",
            "keyword": "AI",
            "limit": 1,
            "offset": 0,
        },
    )

    assert filtered.status_code == 200
    body = filtered.json()
    assert len(body) == 1
    assert body[0]["title"] == "German AI Fellowship"
