import httpx

from app.services.grants_gov import GrantsGovClient, normalize_grants_gov_hit


def test_grants_gov_client_extracts_hits_from_api_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "oppHits": [
                        {
                            "id": "123",
                            "title": "Research Infrastructure Grant",
                            "agency": "NSF",
                            "closeDate": "2026-07-01",
                        }
                    ]
                }
            },
        )

    client = GrantsGovClient(httpx.Client(transport=httpx.MockTransport(handler)))

    hits = client.search("research infrastructure", limit=10)

    assert len(hits) == 1
    assert hits[0]["title"] == "Research Infrastructure Grant"


def test_normalize_grants_gov_hit_maps_to_internal_opportunity():
    opportunity = normalize_grants_gov_hit(
        {
            "id": "123",
            "title": "Research Infrastructure Grant",
            "agency": "NSF",
            "closeDate": "2026-07-01",
            "summary": "Supports research infrastructure.",
        },
        "research infrastructure",
    )

    assert opportunity.title == "Research Infrastructure Grant"
    assert opportunity.source == "grants.gov"
    assert opportunity.deadline.isoformat() == "2026-07-01"
    assert "123" in opportunity.url


def test_grants_gov_ingestion_records_source_and_batch(client, monkeypatch):
    class FakeGrantsGovClient:
        def search(self, keyword: str, limit: int):
            assert keyword == "machine learning"
            assert limit == 1
            return [
                {
                    "id": "123",
                    "title": "Machine Learning Grant",
                    "agency": "NSF",
                    "closeDate": "2026-07-01",
                }
            ]

    monkeypatch.setattr("app.services.grants_gov_ingestion.GrantsGovClient", lambda: FakeGrantsGovClient())

    response = client.post(
        "/ingestion/grants-gov/search",
        json={"keyword": "machine learning", "limit": 1, "import_results": True},
    )

    assert response.status_code == 200
    assert response.json()["batch_id"] is not None
    assert response.json()["imported_count"] == 1

    sources_response = client.get("/sources")
    batches_response = client.get("/sources/batches", params={"source_name": "grants.gov"})

    assert sources_response.status_code == 200
    assert sources_response.json()[0]["name"] == "grants.gov"
    assert batches_response.status_code == 200
    assert batches_response.json()[0]["imported_count"] == 1
