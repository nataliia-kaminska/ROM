def test_bulk_import_creates_and_updates_opportunities(client):
    payload = {
        "source": "euraxess_curated",
        "dry_run": False,
        "opportunities": [
            {
                "title": "European Research Exchange",
                "opportunity_type": "exchange",
                "source": "ignored_source",
                "url": "https://example.org/euraxess/exchange",
                "summary": "Exchange for data science researchers.",
                "disciplines": ["Computer Science"],
                "keywords": ["data science"],
                "countries": ["Germany"],
                "career_stages": ["phd"],
            },
            {
                "title": "European Research Exchange Duplicate",
                "opportunity_type": "exchange",
                "source": "ignored_source",
                "url": "https://example.org/euraxess/exchange",
            },
        ],
    }

    response = client.post("/opportunities/bulk-import", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["batch_id"] is not None
    assert body["imported_count"] == 1
    assert body["updated_count"] == 0
    assert body["skipped_count"] == 1
    assert body["opportunities"][0]["source"] == "euraxess_curated"

    update_response = client.post(
        "/opportunities/bulk-import",
        json={
            "source": "euraxess_curated",
            "opportunities": [
                {
                    "title": "European Research Exchange Updated",
                    "opportunity_type": "exchange",
                    "source": "ignored_source",
                    "url": "https://example.org/euraxess/exchange",
                    "keywords": ["mobility"],
                }
            ],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["updated_count"] == 1
    assert update_response.json()["opportunities"][0]["title"] == "European Research Exchange Updated"

    sources_response = client.get("/sources")
    batches_response = client.get("/sources/batches", params={"source_name": "euraxess_curated"})

    assert sources_response.status_code == 200
    assert sources_response.json()[0]["name"] == "euraxess_curated"
    assert batches_response.status_code == 200
    assert len(batches_response.json()) == 2


def test_bulk_import_dry_run_does_not_persist(client):
    response = client.post(
        "/opportunities/bulk-import",
        json={
            "source": "fulbright_curated",
            "dry_run": True,
            "opportunities": [
                {
                    "title": "Fulbright Visiting Scholar Program",
                    "opportunity_type": "fellowship",
                    "source": "ignored_source",
                    "url": "https://example.org/fulbright/visiting-scholar",
                    "keywords": ["visiting scholar"],
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["batch_id"] is not None
    assert response.json()["imported_count"] == 1

    list_response = client.get("/opportunities")

    assert list_response.status_code == 200
    assert list_response.json() == []

    batches_response = client.get("/sources/batches", params={"source_name": "fulbright_curated"})

    assert batches_response.status_code == 200
    assert batches_response.json()[0]["status"] == "dry_run"
