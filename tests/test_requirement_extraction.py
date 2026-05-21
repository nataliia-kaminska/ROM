from datetime import date, timedelta

from app.core.config import settings
from app.db.models import Opportunity, OpportunityType
from app.services.requirements import extract_requirements_text, refresh_opportunity_requirements


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


def test_opportunity_read_exposes_extracted_requirements(client, admin_headers):
    response = client.post(
        "/opportunities",
        headers=admin_headers,
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


def test_ai_requirement_extraction_enriches_database_metadata(client, monkeypatch, admin_headers):
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
                              "disciplines": ["Computer Science", "Public Health"],
                              "keywords": ["clinical AI", "medical imaging"],
                              "countries": ["Germany"],
                              "career_stages": ["postdoc"],
                              "required_degree": "phd",
                              "languages": ["English"],
                              "publication_expectation": "Applicants should show a publication record.",
                              "mobility": "Host institution in Germany.",
                              "citizenship": "",
                              "years_since_phd": 5,
                              "snippets": ["Applicants must hold a PhD."],
                              "confidence": 88
                            }
                            """
                        }
                    }
                ]
            }

    monkeypatch.setattr(settings, "opportunity_extraction_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.services.requirements.httpx.post", lambda *args, **kwargs: FakeResponse())

    response = client.post(
        "/opportunities",
        headers=admin_headers,
        json={
            "title": "Clinical AI Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/clinical-ai-extraction",
            "summary": "A sparse call description.",
            "eligibility": "See call page.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "Computer Science" in body["disciplines"]
    assert "clinical AI" in body["keywords"]
    assert "Germany" in body["countries"]
    assert "postdoc" in body["career_stages"]
    assert body["extracted_requirements"]["required_degree"] == "phd"
    assert body["requirements_confidence"] == 88


def test_ai_extraction_can_polish_public_card_fields(monkeypatch):
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
                              "title": "MSCA Postdoctoral Fellowships 2026",
                              "summary": "A European fellowship call for postdoctoral researchers to develop an international research project with a host institution.",
                              "eligibility": "Applicants should hold a doctoral degree and comply with MSCA mobility rules.",
                              "disciplines": ["Research"],
                              "keywords": ["postdoctoral fellowship", "mobility"],
                              "countries": ["European Union"],
                              "career_stages": ["postdoc"],
                              "required_degree": "phd",
                              "languages": ["English"],
                              "publication_expectation": "",
                              "mobility": "MSCA mobility rules apply.",
                              "citizenship": "",
                              "years_since_phd": null,
                              "snippets": ["Applicants should hold a doctoral degree."],
                              "confidence": 84
                            }
                            """
                        }
                    }
                ]
            }

    opportunity = Opportunity(
        title="Apply now",
        opportunity_type=OpportunityType.fellowship,
        source="eu_funding_tenders",
        url="https://ec.europa.eu/info/funding-tenders/opportunities/example",
        summary="See call page.",
        eligibility="See call page.",
        disciplines="",
        keywords="",
        countries="",
        career_stages="",
    )
    monkeypatch.setattr(settings, "opportunity_extraction_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.services.requirements.httpx.post", lambda *args, **kwargs: FakeResponse())

    refresh_opportunity_requirements(opportunity, page_preview="MSCA Postdoctoral Fellowships 2026. Applicants should hold a doctoral degree.")

    assert opportunity.title == "MSCA Postdoctoral Fellowships 2026"
    assert "European fellowship call" in opportunity.summary
    assert "doctoral degree" in opportunity.eligibility
    assert opportunity.requirements_confidence == 84


def test_recommendations_use_extracted_requirements_when_metadata_is_sparse(client, admin_headers):
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
        headers=admin_headers,
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


def test_application_assistant_returns_gap_analysis(client, admin_headers):
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
        headers=admin_headers,
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
