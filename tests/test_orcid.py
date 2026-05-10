from app.services.orcid import extract_profile_payload


ORCID_RECORD = {
    "person": {
        "name": {
            "given-names": {"value": "Ada"},
            "family-name": {"value": "Kovalenko"},
        },
        "keywords": {
            "keyword": [
                {"content": "machine learning"},
                {"content": "bioinformatics"},
            ]
        },
        "addresses": {
            "address": [
                {"country": {"value": "UA"}},
            ]
        },
        "researcher-urls": {
            "researcher-url": [
                {"url": {"value": "https://scholar.google.com/citations?user=abc"}},
                {"url": {"value": "https://www.linkedin.com/in/ada-kovalenko"}},
            ]
        },
    }
}


def test_extract_profile_payload_from_orcid_record():
    payload = extract_profile_payload("0000-0002-1825-0097", ORCID_RECORD)

    assert payload["full_name"] == "Ada Kovalenko"
    assert payload["country"] == "UA"
    assert payload["keywords"] == ["machine learning", "bioinformatics"]
    assert "scholar.google" in payload["google_scholar_url"]
    assert "linkedin.com" in payload["linkedin_url"]


def test_orcid_import_creates_profile(client, monkeypatch):
    class FakeOrcidClient:
        def read_public_record(self, orcid_id: str):
            assert orcid_id == "0000-0002-1825-0097"
            return ORCID_RECORD

    monkeypatch.setattr("app.api.orcid.OrcidClient", lambda: FakeOrcidClient())

    response = client.post(
        "/integrations/orcid/import",
        json={
            "orcid_id": "0000-0002-1825-0097",
            "career_stage": "phd",
            "disciplines": ["Computer Science"],
            "preferred_countries": ["Germany"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["imported"] is True
    assert body["profile"]["full_name"] == "Ada Kovalenko"
    assert body["profile"]["keywords"] == ["bioinformatics", "machine learning"]


def test_orcid_import_can_auto_enrich_from_openalex(client, monkeypatch):
    from app.core.config import settings

    class FakeOrcidClient:
        def read_public_record(self, orcid_id: str):
            assert orcid_id == "0000-0002-1825-0097"
            return ORCID_RECORD

    class FakeOpenAlexClient:
        def read_author(self, author_id=None, orcid_id=None):
            assert orcid_id == "0000-0002-1825-0097"
            return {
                "id": "https://openalex.org/A123",
                "display_name": "Ada Kovalenko",
                "works_count": 1,
                "x_concepts": [{"display_name": "Machine learning"}],
            }

        def read_works(self, author_id: str, limit: int = 20):
            return [
                {
                    "display_name": "Clinical AI for genomics",
                    "concepts": [{"display_name": "Genomics"}],
                }
            ]

    monkeypatch.setattr(settings, "profile_enrichment_auto_openalex", True)
    monkeypatch.setattr("app.api.orcid.OrcidClient", lambda: FakeOrcidClient())
    monkeypatch.setattr("app.services.profile_enrichment.OpenAlexClient", lambda: FakeOpenAlexClient())

    response = client.post(
        "/integrations/orcid/import",
        json={
            "orcid_id": "0000-0002-1825-0097",
            "career_stage": "phd",
            "disciplines": ["Computer Science"],
            "preferred_countries": ["Germany"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "machine learning" in [item.lower() for item in body["profile"]["keywords"]]
    assert "Bioinformatics" in body["profile"]["disciplines"]
