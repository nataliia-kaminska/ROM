from datetime import date, timedelta

from app.services.requirements import extract_requirements_text


def test_requirement_parser_extracts_structured_signals():
    requirements = extract_requirements_text(
        "MSCA Postdoctoral Fellowship",
        "Mobility fellowship hosted in Germany.",
        "Applicants must hold a PhD, speak English, have publications, and be within 8 years since PhD.",
    )

    assert requirements.required_degree == "phd"
    assert "postdoc" in requirements.career_stages
    assert "Germany" in requirements.countries
    assert "English" in requirements.languages
    assert requirements.years_since_phd == 8
    assert requirements.confidence >= 60


def test_opportunity_read_exposes_extracted_requirements(client):
    response = client.post(
        "/opportunities",
        json={
            "title": "DAAD Doctoral Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/daad-doctoral",
            "summary": "Funding for doctoral researchers in Germany.",
            "eligibility": "Open to PhD applicants. English required.",
            "deadline": str(date.today() + timedelta(days=60)),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["requirements_confidence"] > 0
    assert "phd" in body["extracted_requirements"]["career_stages"]
    assert "Germany" in body["extracted_requirements"]["countries"]


def test_recommendations_use_extracted_requirements_when_metadata_is_sparse(client):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Requirement Match",
            "career_stage": "phd",
            "country": "Ukraine",
            "keywords": ["climate"],
        },
    ).json()
    client.post(
        "/opportunities",
        json={
            "title": "Climate Doctoral Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/climate-doctoral",
            "summary": "Climate research fellowship.",
            "eligibility": "Open to PhD researchers from Ukraine. English required.",
            "keywords": ["climate"],
        },
    )

    recommendations = client.get(f"/recommendations/{profile['id']}").json()

    assert recommendations[0]["score_breakdown"]["eligibility"] >= 55
    assert recommendations[0]["readiness_score"] >= 60
    assert any("Eligible career stage" in reason for reason in recommendations[0]["reasons"])


def test_application_assistant_returns_gap_analysis(client):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Gap User",
            "career_stage": "master",
            "country": "Ukraine",
            "keywords": ["AI"],
        },
    ).json()
    opportunity = client.post(
        "/opportunities",
        json={
            "title": "Postdoctoral AI Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/postdoc-ai",
            "summary": "AI fellowship.",
            "eligibility": "Applicants must hold a PhD, have publications, and speak English.",
            "keywords": ["AI"],
        },
    ).json()

    response = client.post(
        "/application-assistant",
        json={"profile_id": profile["id"], "opportunity_id": opportunity["id"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["readiness_score"] < 70
    assert any("required degree" in gap.lower() or "publication" in gap.lower() for gap in body["gap_analysis"])
    assert "## Readiness and Gaps" in body["exported_notes"]
