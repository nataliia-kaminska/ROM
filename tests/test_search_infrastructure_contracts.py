from types import SimpleNamespace

from app.infrastructure.search.elasticsearch import ElasticsearchOpportunitySearch
from app.services.recommendations import PostgresVectorCandidateSelector, RecommendationQuery


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_elasticsearch_search_builds_full_text_query_with_filters():
    calls = []

    class FakeHttpClient:
        def post(self, url, json):
            calls.append((url, json))
            return FakeResponse(
                {
                    "hits": {
                        "hits": [
                            {"_source": {"id": "10"}},
                            {"_source": {"id": 11}},
                        ]
                    }
                }
            )

    search = ElasticsearchOpportunitySearch(
        base_url="http://elasticsearch:9200",
        index_name="research_opportunities",
        client=FakeHttpClient(),
    )

    ids = search.search_opportunity_ids(
        "climate mobility",
        limit=5,
        offset=10,
        filters={"source": "horizon_europe", "opportunity_type": "grant"},
    )

    assert ids == [10, 11]
    assert calls[0][0] == "http://elasticsearch:9200/research_opportunities/_search"
    body = calls[0][1]
    assert body["from"] == 10
    assert body["size"] == 5
    assert body["query"]["bool"]["must"][0]["multi_match"]["query"] == "climate mobility"
    assert "title^3" in body["query"]["bool"]["must"][0]["multi_match"]["fields"]
    assert {"term": {"source": "horizon_europe"}} in body["query"]["bool"]["filter"]
    assert {"term": {"opportunity_type": "grant"}} in body["query"]["bool"]["filter"]


def test_postgres_vector_candidate_selector_uses_pgvector_cosine_operator(monkeypatch):
    executed = {}
    returned_opportunities = [SimpleNamespace(id=1), SimpleNamespace(id=2)]

    class FakeRows:
        def all(self):
            return [(1,), (2,)]

    class FakeQuery:
        def filter(self, *args):
            return self

        def all(self):
            return returned_opportunities

    class FakeDb:
        bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

        def execute(self, statement, params):
            executed["sql"] = str(statement)
            executed["params"] = params
            return FakeRows()

        def query(self, model):
            return FakeQuery()

    monkeypatch.setattr("app.services.recommendations.persist_profile_embedding_vector", lambda db, profile, details: None)
    monkeypatch.setattr("app.services.recommendations.ensure_profile_embedding", lambda profile, details: [0.1, 0.2, 0.3])
    monkeypatch.setattr("app.services.recommendations.settings.semantic_candidate_limit", 25)

    results = PostgresVectorCandidateSelector().select(
        FakeDb(),
        profile=SimpleNamespace(id=1),
        details=SimpleNamespace(id=2),
        query=RecommendationQuery(),
    )

    assert results == returned_opportunities
    assert "opportunity_embedding_vector <=> CAST(:profile_vector AS vector)" in executed["sql"]
    assert executed["params"]["profile_vector"] == "[0.10000000,0.20000000,0.30000000]"
    assert executed["params"]["limit"] == 25
