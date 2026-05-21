from app.db.models import Opportunity, OpportunityType
from app.services.web_research import _research_queries, research_opportunity_web


def test_web_research_disabled_by_default(monkeypatch):
    opportunity = Opportunity(
        title="AI Fellowship",
        opportunity_type=OpportunityType.fellowship,
        source="manual_seed",
        url="https://example.org/ai-fellowship",
    )
    monkeypatch.setattr("app.services.web_research.settings.assistant_web_research_enabled", False)

    assert research_opportunity_web(opportunity) == []


def test_web_research_uses_duckduckgo_provider(monkeypatch):
    opportunity = Opportunity(
        title="AI Fellowship",
        opportunity_type=OpportunityType.fellowship,
        source="manual_seed",
        url="https://example.org/ai-fellowship",
    )
    monkeypatch.setattr("app.services.web_research.settings.assistant_web_research_enabled", True)
    monkeypatch.setattr("app.services.web_research._duckduckgo_search", lambda query, max_results: [f"Web research: {query}"])

    results = research_opportunity_web(opportunity)

    assert results[0] == "Web research: AI Fellowship manual seed official call eligibility deadline"
    assert len(results) == 3


def test_web_research_falls_back_to_flexible_queries(monkeypatch):
    opportunity = Opportunity(
        title="NIJ FY25 Research and Evaluation of Artificial Intelligence for Criminal Justice Purposes",
        opportunity_type=OpportunityType.grant,
        source="grants.gov",
        url="https://grants.gov/search-results-detail/123",
        keywords="artificial intelligence,criminal justice",
        disciplines="Law,Computer Science",
    )
    calls = []

    def fake_search(query: str, max_results: int):
        calls.append(query)
        if "official call eligibility" in query:
            return []
        return [f"Web research: {query}"]

    monkeypatch.setattr("app.services.web_research.settings.assistant_web_research_enabled", True)
    monkeypatch.setattr("app.services.web_research.settings.assistant_web_research_max_results", 2)
    monkeypatch.setattr("app.services.web_research._duckduckgo_search", fake_search)

    results = research_opportunity_web(opportunity)

    assert results
    assert len(calls) > 1
    assert any("Artificial Intelligence" in query and "Criminal Justice" in query for query in calls)
    assert any(query.startswith("site:grants.gov") for query in _research_queries(opportunity))
