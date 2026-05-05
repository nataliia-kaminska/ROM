import httpx

from app.services.advisor_provider import AdvisorFacts, GroqAdvisorProvider, deterministic_advisor_memo


def _facts() -> AdvisorFacts:
    return AdvisorFacts(
        profile_name="Ada",
        opportunity_title="AI Fellowship",
        opportunity_type="fellowship",
        deadline="2026-06-01",
        readiness_score=72,
        strengths=["Topic overlap: AI."],
        gaps=["Add publication highlights."],
        warnings=["Career stage may need review."],
        missing_fields=["degrees"],
        checklist=["Confirm eligibility.", "Draft fit statement."],
        motivation_outline=["Connect AI to fellowship goals."],
        fit_statement="Ada has a credible AI fit.",
    )


def test_deterministic_advisor_memo_uses_structured_facts():
    memo = deterministic_advisor_memo(_facts())

    assert "AI Fellowship" in memo
    assert "72% readiness" in memo
    assert "Add publication highlights" in memo


def test_groq_provider_falls_back_without_api_key(monkeypatch):
    monkeypatch.setattr("app.services.advisor_provider.settings.groq_api_key", "")

    memo = GroqAdvisorProvider().generate_memo(_facts())

    assert "AI Fellowship" in memo
    assert "Recommended next actions" in memo


def test_groq_provider_falls_back_on_network_failure(monkeypatch):
    monkeypatch.setattr("app.services.advisor_provider.settings.groq_api_key", "test-key")

    def fail_post(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("app.services.advisor_provider.httpx.post", fail_post)

    memo = GroqAdvisorProvider().generate_memo(_facts())

    assert "AI Fellowship" in memo
    assert "Recommended next actions" in memo
