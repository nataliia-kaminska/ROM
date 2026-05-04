from app.services.openalex import extract_openalex_profile


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
    assert "Graph neural networks for genomics" in body["details"]["publications"]
    assert "Genomics" in body["details"]["funding_interests"]
