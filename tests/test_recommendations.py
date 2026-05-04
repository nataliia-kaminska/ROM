from datetime import date, timedelta


def test_profile_opportunity_recommendation_flow(client):
    profile_response = client.post(
        "/profiles",
        json={
            "full_name": "Ada Kovalenko",
            "email": "ada@example.com",
            "career_stage": "phd",
            "country": "Ukraine",
            "disciplines": ["Computer Science", "Bioinformatics"],
            "keywords": ["machine learning", "genomics"],
            "preferred_countries": ["Germany"],
            "orcid_id": "0000-0002-1825-0097",
        },
    )

    assert profile_response.status_code == 201
    profile_id = profile_response.json()["id"]

    opportunity_response = client.post(
        "/opportunities",
        json={
            "title": "AI for Genomics Exchange Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/fellowship",
            "summary": "Exchange fellowship for AI methods in genomics.",
            "eligibility": "Open to PhD researchers.",
            "disciplines": ["Computer Science", "Bioinformatics"],
            "keywords": ["machine learning", "genomics"],
            "countries": ["Germany"],
            "career_stages": ["phd"],
            "deadline": str(date.today() + timedelta(days=30)),
        },
    )

    assert opportunity_response.status_code == 201

    recommendations_response = client.get(f"/recommendations/{profile_id}")

    assert recommendations_response.status_code == 200
    recommendations = recommendations_response.json()
    assert recommendations[0]["match_score"] >= 90
    assert "AI for Genomics Exchange Fellowship" == recommendations[0]["opportunity"]["title"]
    assert recommendations[0]["reasons"]

    paged_response = client.get(f"/recommendations/{profile_id}", params={"min_score": 90, "limit": 1})

    assert paged_response.status_code == 200
    assert len(paged_response.json()) == 1


def test_recommendations_use_profile_details_and_hide_ignored_status(client):
    profile_response = client.post(
        "/profiles",
        json={
            "full_name": "Iryna Melnyk",
            "career_stage": "early_career",
            "country": "Ukraine",
            "disciplines": ["Environmental Science"],
            "keywords": ["climate adaptation"],
            "preferred_countries": ["Germany"],
        },
    )
    profile_id = profile_response.json()["id"]
    client.put(
        f"/profiles/{profile_id}/details",
        json={
            "research_summary": "Research on climate adaptation and urban heat resilience.",
            "funding_interests": ["urban resilience"],
            "preferred_opportunity_types": ["grant"],
            "unavailable_countries": ["United States"],
        },
    )

    good_opportunity = client.post(
        "/opportunities",
        json={
            "title": "Urban Resilience Climate Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/climate",
            "summary": "Funding for urban heat and climate adaptation projects.",
            "disciplines": ["Environmental Science"],
            "keywords": ["urban resilience"],
            "countries": ["Germany"],
            "career_stages": ["early_career"],
        },
    ).json()
    ignored_opportunity = client.post(
        "/opportunities",
        json={
            "title": "Unwanted US Climate Grant",
            "opportunity_type": "grant",
            "source": "manual_seed",
            "url": "https://example.org/us-climate",
            "disciplines": ["Environmental Science"],
            "keywords": ["climate adaptation"],
            "countries": ["United States"],
            "career_stages": ["early_career"],
        },
    ).json()

    client.put(
        f"/profiles/{profile_id}/opportunities/{ignored_opportunity['id']}/status",
        json={"status": "ignored"},
    )

    recommendations = client.get(f"/recommendations/{profile_id}").json()

    assert [item["opportunity"]["id"] for item in recommendations] == [good_opportunity["id"]]
    assert recommendations[0]["match_score"] >= 80
    assert any("preferred opportunity type" in reason for reason in recommendations[0]["reasons"])

    recommendations_with_ignored = client.get(f"/recommendations/{profile_id}?include_ignored=true").json()

    assert {item["opportunity"]["id"] for item in recommendations_with_ignored} == {
        good_opportunity["id"],
        ignored_opportunity["id"],
    }


def test_recommendations_include_semantic_similarity_signal(client):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Marta Semeniv",
            "career_stage": "postdoc",
            "disciplines": ["Medicine"],
            "keywords": ["clinical AI"],
        },
    ).json()
    client.put(
        f"/profiles/{profile['id']}/details",
        json={
            "research_summary": "Neural language models for emergency triage and clinical decision support.",
            "publications": ["Transformer models for hospital emergency triage"],
        },
    )
    related = client.post(
        "/opportunities",
        json={
            "title": "Emergency Triage AI Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/triage-ai",
            "summary": "Support for neural language models in hospital emergency triage workflows.",
            "eligibility": "Open to researchers developing clinical decision support.",
            "disciplines": ["Health Informatics"],
            "keywords": ["decision support"],
        },
    ).json()
    unrelated = client.post(
        "/opportunities",
        json={
            "title": "Marine Robotics Training",
            "opportunity_type": "training",
            "source": "manual_seed",
            "url": "https://example.org/marine-robotics",
            "summary": "Field training for autonomous underwater navigation and marine robotics.",
            "disciplines": ["Engineering"],
            "keywords": ["robotics"],
        },
    ).json()

    recommendations = client.get(f"/recommendations/{profile['id']}").json()

    assert recommendations[0]["opportunity"]["id"] == related["id"]
    assert recommendations[0]["semantic_score"] > recommendations[1]["semantic_score"]
    assert any("Semantic similarity" in reason for reason in recommendations[0]["reasons"])
