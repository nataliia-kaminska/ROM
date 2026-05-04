import httpx

from app.schemas.ingestion import ExternalSourceImportRequest
from app.services.external_sources import ExternalSourceClient, normalize_external_source


def test_normalize_external_rss_source_to_opportunities():
    raw = """
    <rss><channel>
      <item>
        <title>DAAD Climate Fellowship</title>
        <link>https://example.org/daad/climate</link>
        <description>Funding for climate adaptation researchers.</description>
        <category>climate adaptation</category>
        <deadline>2026-09-01</deadline>
      </item>
    </channel></rss>
    """
    payload = ExternalSourceImportRequest(
        source_name="daad",
        source_url="https://example.org/feed.xml",
        source_kind="rss",
        default_opportunity_type="fellowship",
        default_country="Germany",
        default_career_stage="phd",
    )

    opportunities = normalize_external_source(raw, payload)

    assert opportunities[0].title == "DAAD Climate Fellowship"
    assert opportunities[0].countries == ["Germany"]
    assert opportunities[0].career_stages == ["phd"]
    assert opportunities[0].deadline.isoformat() == "2026-09-01"


def test_external_source_import_records_batch(client, monkeypatch):
    class FakeExternalSourceClient:
        def fetch(self, url: str) -> str:
            assert url == "https://example.org/euraxess.json"
            return """
            {
              "results": [
                {
                  "title": "EURAXESS AI Postdoc",
                  "url": "https://example.org/euraxess/ai-postdoc",
                  "summary": "Mobility postdoc for trustworthy AI.",
                  "type": "research_position",
                  "country": "France",
                  "keywords": ["AI", "mobility"]
                }
              ]
            }
            """

    monkeypatch.setattr("app.services.external_sources.ExternalSourceClient", lambda: FakeExternalSourceClient())

    response = client.post(
        "/ingestion/external-source/import",
        json={
            "source_name": "euraxess",
            "source_url": "https://example.org/euraxess.json",
            "source_kind": "json",
            "import_results": True,
            "limit": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "euraxess"
    assert body["imported_count"] == 1
    assert body["opportunities"][0]["title"] == "EURAXESS AI Postdoc"

    sources_response = client.get("/sources")
    assert sources_response.status_code == 200
    assert sources_response.json()[0]["name"] == "euraxess"
