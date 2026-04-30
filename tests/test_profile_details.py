def test_profile_details_can_be_created_and_read(client):
    profile_response = client.post(
        "/profiles",
        json={
            "full_name": "Iryna Melnyk",
            "career_stage": "early_career",
            "disciplines": ["Environmental Science"],
            "keywords": ["climate adaptation"],
        },
    )
    profile_id = profile_response.json()["id"]

    update_response = client.put(
        f"/profiles/{profile_id}/details",
        json={
            "research_summary": "I study climate adaptation and urban heat resilience.",
            "publications": ["Urban Heat Resilience in Eastern Europe"],
            "degrees": ["PhD Environmental Science"],
            "languages": ["English", "Ukrainian"],
            "funding_interests": ["climate adaptation", "urban resilience"],
            "unavailable_countries": ["United States"],
            "preferred_opportunity_types": ["grant", "fellowship"],
            "min_duration_months": 3,
            "max_duration_months": 12,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["funding_interests"] == ["climate adaptation", "urban resilience"]

    read_response = client.get(f"/profiles/{profile_id}/details")

    assert read_response.status_code == 200
    assert read_response.json()["research_summary"].startswith("I study climate adaptation")

