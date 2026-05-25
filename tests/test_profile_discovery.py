def _create_profile(client, headers):
    response = client.post(
        "/profiles",
        headers=headers,
        json={
            "full_name": "Ada Kovalenko",
            "email": "ada@example.com",
            "career_stage": "postdoc",
            "country": "Ukraine",
            "disciplines": ["Computer Science"],
            "keywords": ["machine learning"],
            "preferred_countries": ["Germany"],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_profile_discovery_returns_confirmable_candidates(client, researcher_headers, monkeypatch):
    profile = _create_profile(client, researcher_headers)

    monkeypatch.setattr(
        "app.services.profile_discovery.duckduckgo_search_results",
        lambda query, max_results: [
            {
                "title": "Ada Kovalenko - University researcher profile",
                "href": "https://example.edu/ada-kovalenko",
                "body": "Ada Kovalenko publishes research in machine learning and bioinformatics.",
            }
        ],
    )

    response = client.get(f"/profiles/{profile['id']}/discovery", headers=researcher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body[0]["title"] == "Ada Kovalenko - University researcher profile"
    assert body[0]["confidence"] >= 35


def test_profile_discovery_apply_merges_confirmed_metadata(client, researcher_headers, monkeypatch):
    profile = _create_profile(client, researcher_headers)

    class FakeExternalSourceClient:
        def fetch(self, url: str) -> str:
            assert url == "https://example.edu/ada-kovalenko"
            return "<html><body>Ada Kovalenko researches graph neural networks. PhD. English.</body></html>"

    monkeypatch.setattr("app.services.profile_discovery.ExternalSourceClient", FakeExternalSourceClient)
    monkeypatch.setattr(
        "app.services.profile_discovery.extract_profile_metadata_from_text",
        lambda profile_name, source_title, source_url, text: {
            "research_summary": "Ada Kovalenko researches graph neural networks for genomics.",
            "disciplines": ["Bioinformatics"],
            "keywords": ["graph neural networks"],
            "publications": ["Graph neural networks for genomics"],
            "degrees": ["PhD"],
            "languages": ["English"],
            "funding_interests": ["genomics research"],
        },
    )

    response = client.post(
        f"/profiles/{profile['id']}/discovery/apply",
        headers=researcher_headers,
        json={
            "title": "Ada Kovalenko - University researcher profile",
            "url": "https://example.edu/ada-kovalenko",
            "snippet": "Ada Kovalenko publishes research in machine learning and bioinformatics.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Bioinformatics" in body["profile"]["disciplines"]
    assert "graph neural networks" in body["profile"]["keywords"]
    assert "Graph neural networks for genomics" in body["details"]["publications"]
    assert "research_summary" in body["applied_fields"]
