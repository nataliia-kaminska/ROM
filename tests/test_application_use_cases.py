from types import SimpleNamespace

from app.application.use_cases.ingestion import ExternalSourceIngestionUseCase, GrantsGovIngestionUseCase
from app.application.use_cases.recommendations import ListRecommendationsUseCase
from app.schemas.ingestion import ExternalSourceImportRequest


def test_recommendation_use_case_orchestrates_business_logic_with_mocks(monkeypatch):
    profile = SimpleNamespace(id=42, user_id=7)
    current_user = SimpleNamespace(id=7)
    query = SimpleNamespace(min_score=60)
    expected = [SimpleNamespace(match_score=91)]

    monkeypatch.setattr("app.application.use_cases.recommendations.profile_repository.get_profile", lambda db, profile_id: profile)
    monkeypatch.setattr("app.application.use_cases.recommendations.list_recommendations", lambda db, selected_profile, selected_query: expected)

    result = ListRecommendationsUseCase(db=object()).execute(profile_id=42, current_user=current_user, query=query)

    assert result == expected


def test_ingestion_use_cases_delegate_to_strategy_ports():
    class FakeGrantsStrategy:
        def __init__(self):
            self.calls = []

        def ingest(self, command, db):
            self.calls.append((command, db))
            return {"source": "grants.gov"}

    class FakeExternalStrategy:
        def __init__(self):
            self.calls = []

        def ingest(self, request, db):
            self.calls.append((request, db))
            return {"source": request.source_name}

    db = object()
    grants_command = SimpleNamespace(keyword="climate", limit=2, import_results=True)
    external_request = ExternalSourceImportRequest(
        source_name="euraxess",
        source_url="https://example.org/feed.json",
        source_kind="json",
    )
    grants_strategy = FakeGrantsStrategy()
    external_strategy = FakeExternalStrategy()

    grants_result = GrantsGovIngestionUseCase(db=db, strategy=grants_strategy).execute(grants_command)
    external_result = ExternalSourceIngestionUseCase(db=db, strategy=external_strategy).execute(external_request)

    assert grants_result == {"source": "grants.gov"}
    assert external_result == {"source": "euraxess"}
    assert grants_strategy.calls == [(grants_command, db)]
    assert external_strategy.calls == [(external_request, db)]
