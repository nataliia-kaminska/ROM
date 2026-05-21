from app.services.openalex import extract_openalex_profile
from app.core.config import settings
from app.services.profile_enrichment import normalize_profile_concepts


AUTHOR = {
    "id": "https://openalex.org/A123",
    "display_name": "Ada Kovalenko",
    "works_count": 42,
    "x_concepts": [
        {"display_name": "Machine learning"},
        {"display_name": "Bioinformatics"},
    ],
}

WORKS = [
    {
        "display_name": "Graph neural networks for genomics",
        "concepts": [{"display_name": "Genomics"}],
    }
]


def test_extract_openalex_profile_payload():
    payload = extract_openalex_profile(AUTHOR, WORKS)

    assert payload["display_name"] == "Ada Kovalenko"
    assert payload["openalex_author_id"] == "https://openalex.org/A123"
    assert "Machine learning" in payload["concepts"]
    assert "Graph neural networks for genomics" in payload["works"]


def test_openalex_import_enriches_profile_details(client, monkeypatch):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Ada Kovalenko",
            "career_stage": "postdoc",
            "orcid_id": "0000-0002-1825-0097",
            "disciplines": ["Computer Science"],
        },
    ).json()

    class FakeOpenAlexClient:
        def read_author(self, author_id=None, orcid_id=None):
            assert orcid_id == "0000-0002-1825-0097"
            return AUTHOR

        def read_works(self, author_id: str, limit: int = 10):
            assert author_id == "https://openalex.org/A123"
            return WORKS

    monkeypatch.setattr("app.api.openalex.OpenAlexClient", lambda: FakeOpenAlexClient())

    response = client.post(
        "/integrations/openalex/import",
        json={"profile_id": profile["id"], "max_works": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert "Bioinformatics" in body["profile"]["keywords"]
    assert "Bioinformatics" in body["profile"]["disciplines"]
    assert "Graph neural networks for genomics" in body["details"]["publications"]
    assert "Genomics" in body["details"]["funding_interests"]


def test_openalex_preview_shows_merge_plan_without_persisting(client, monkeypatch):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Preview User",
            "career_stage": "phd",
            "keywords": ["existing"],
        },
    ).json()

    class FakeOpenAlexClient:
        def read_author(self, author_id=None, orcid_id=None):
            assert author_id == "https://openalex.org/A123"
            return AUTHOR

        def read_works(self, author_id: str, limit: int = 10):
            assert author_id == "https://openalex.org/A123"
            return WORKS

    monkeypatch.setattr("app.api.openalex.OpenAlexClient", lambda: FakeOpenAlexClient())

    response = client.post(
        "/integrations/openalex/preview",
        json={"profile_id": profile["id"], "openalex_author_id": "https://openalex.org/A123", "max_works": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Ada Kovalenko"
    assert body["works_count"] == 1
    assert "Graph neural networks for genomics" in body["new_publications"]
    assert "Bioinformatics" in body["suggested_disciplines"]

    details = client.get(f"/profiles/{profile['id']}/details").json()
    assert details["publications"] == []


def test_profile_concept_normalizer_can_use_ai(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": """
                            {
                              "disciplines": ["Computer Science", "Medicine"],
                              "keywords": ["clinical AI", "medical imaging"],
                              "funding_interests": ["digital health"]
                            }
                            """
                        }
                    }
                ]
            }

    monkeypatch.setattr(settings, "profile_enrichment_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.services.profile_enrichment.httpx.post", lambda *args, **kwargs: FakeResponse())

    result = normalize_profile_concepts(["Machine learning", "Radiology"])

    assert result.provider == "groq"
    assert "Computer Science" in result.disciplines
    assert "clinical AI" in result.keywords
    assert "digital health" in result.funding_interests
