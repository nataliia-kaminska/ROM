from datetime import date, timedelta


def test_application_assistant_generates_notes_and_warnings(client, admin_headers):
    profile = client.post(
        "/profiles",
        json={
            "full_name": "Ada Kovalenko",
            "career_stage": "phd",
            "country": "Ukraine",
            "disciplines": ["Computer Science"],
            "keywords": ["machine learning"],
        },
    ).json()
    client.put(
        f"/profiles/{profile['id']}/details",
        json={
            "research_summary": "I build machine learning systems for genomics and clinical data.",
            "publications": ["ML for genomics"],
            "languages": ["English"],
        },
    )
    opportunity = client.post(
        "/opportunities",
        headers=admin_headers,
        json={
            "title": "AI Fellowship",
            "opportunity_type": "fellowship",
            "source": "manual_seed",
            "url": "https://example.org/ai-fellowship",
            "summary": "Fellowship for applied AI.",
            "keywords": ["AI"],
            "countries": ["Germany"],
            "career_stages": ["postdoc"],
            "deadline": str(date.today() + timedelta(days=20)),
        },
    ).json()

    response = client.post(
        "/application-assistant",
        json={"profile_id": profile["id"], "opportunity_id": opportunity["id"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["retrieved_context"]
    assert body["profile_name"] == "Ada Kovalenko"
    assert body["opportunity_title"] == "AI Fellowship"
    assert "web_research" in body
    assert any("Opportunity" in snippet for snippet in body["retrieved_context"])
    assert body["application_checklist"]
    assert body["motivation_letter_outline"]
    assert "AI Fellowship" in body["research_fit_statement"]
    assert "degrees" in body["missing_profile_fields"]
    assert any("Career stage" in warning for warning in body["eligibility_warnings"])
    assert body["advisor_provider"] == "deterministic"
    assert "AI Fellowship" in body["advisor_memo"]
    assert "Best angle" in body["advisor_memo"]
    assert "Reviewer concerns" in body["advisor_memo"]
    assert "Draft snippets" in body["advisor_memo"]
    assert "## Retrieved Context" in body["exported_notes"]
    assert "## Checklist" in body["exported_notes"]
    assert "## Advisor Memo" in body["exported_notes"]
