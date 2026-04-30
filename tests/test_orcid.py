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

