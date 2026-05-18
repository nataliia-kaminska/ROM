import httpx

from app.db.models import User, UserRole
from app.core.exceptions import BadRequestError
from app.schemas.ingestion import ExternalSourceImportRequest
from app.services.external_sources import ExternalSourceClient, normalize_external_source, validate_external_source_url
from app.services.source_connectors import get_source_connector


def _admin_headers(client) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": "source-admin@example.com", "password": "strong-password-123", "full_name": "Source Admin"},
    )
    SessionLocal = client.app.state.testing_session_factory
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "source-admin@example.com").first()
        user.role = UserRole.admin
        db.commit()
    login = client.post(
        "/auth/login",
        json={"email": "source-admin@example.com", "password": "strong-password-123"},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_normalize_external_rss_source_to_opportunities():
    raw = """
    <rss><channel>
      <item>
        <title>DAAD Climate Fellowship</title>
        <link>https://example.org/daad/climate</link>
        <description>Funding for climate adaptation researchers.</description>
        <category>climate adaptation</category>
        <deadline>2026-09-01</deadline>
      </item>
    </channel></rss>
    """
    payload = ExternalSourceImportRequest(
        source_name="daad",
        source_url="https://example.org/feed.xml",
        source_kind="rss",
        default_opportunity_type="fellowship",
        default_country="Germany",
        default_career_stage="phd",
    )

    opportunities = normalize_external_source(raw, payload)

    assert opportunities[0].title == "DAAD Climate Fellowship"
    assert opportunities[0].countries == ["Germany"]
    assert opportunities[0].career_stages == ["phd"]
    assert opportunities[0].deadline.isoformat() == "2026-09-01"


def test_normalize_external_html_source_to_opportunities():
    raw = """
    <main>
      <a href="/en/opportunities">Opportunities</a>
      <a href="/en/search">Scholarship database</a>
      <a href="/en/opportunity/research-grant">Research grant for Ukrainian scholars</a>
      <a href="/about">About the organization</a>
      <a href="mailto:hello@example.org">Email us</a>
    </main>
    """
    payload = ExternalSourceImportRequest(
        source_name="house_of_europe",
        source_url="https://houseofeurope.org.ua/en/opportunities",
        source_kind="html",
        default_opportunity_type="grant",
    )

    opportunities = normalize_external_source(raw, payload)

    assert len(opportunities) == 1
    assert opportunities[0].title == "Research grant for Ukrainian scholars"
    assert str(opportunities[0].url) == "https://houseofeurope.org.ua/en/opportunity/research-grant"
    assert opportunities[0].countries == ["Ukraine", "European Union"]
    assert "house of europe" in opportunities[0].keywords


def test_normalize_external_html_source_rejects_generic_listing_pages():
    raw = """
    <main>
      <a href="/en/opportunities">Opportunities</a>
      <a href="/en/grants">Grants</a>
      <a href="/en/news/open-call-2026-research-mobility">Open call 2026 for research mobility</a>
      <a href="/en/programs">Programs</a>
    </main>
    """
    payload = ExternalSourceImportRequest(
        source_name="nrfu",
        source_url="https://nrfu.org.ua/en/opportunities",
        source_kind="html",
        default_opportunity_type="grant",
    )

    opportunities = normalize_external_source(raw, payload)

    assert [opportunity.title for opportunity in opportunities] == ["Open call 2026 for research mobility"]
    assert str(opportunities[0].url) == "https://nrfu.org.ua/en/news/open-call-2026-research-mobility"


def test_european_html_import_rejects_generic_provider_pages():
    erasmus_raw = """
    <main>
      <a href="/opportunities/opportunities-for-individuals/applying-by-yourself">Applying by yourself</a>
      <a href="/opportunities/individuals/trainees/students/search-the-erasmus-mundus-catalogue">search the Erasmus Mundus catalogue</a>
      <a href="/news/future-skills-start-here-2026-erasmus-funding-call-is-open">Future skills start here - 2026 Erasmus+ funding call is open</a>
    </main>
    """
    horizon_raw = """
    <main>
      <a href="/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals">Calls for proposals</a>
    </main>
    """
    erasmus_payload = ExternalSourceImportRequest(
        source_name="erasmus",
        source_url="https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals",
        source_kind="html",
        default_opportunity_type="exchange",
    )
    horizon_payload = ExternalSourceImportRequest(
        source_name="horizon_europe",
        source_url="https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals",
        source_kind="html",
        default_opportunity_type="grant",
    )

    erasmus_opportunities = normalize_external_source(erasmus_raw, erasmus_payload)
    horizon_opportunities = normalize_external_source(horizon_raw, horizon_payload)

    assert [opportunity.title for opportunity in erasmus_opportunities] == ["Future skills start here - 2026 Erasmus+ funding call is open"]
    assert horizon_opportunities == []


def test_external_source_import_records_batch(client, monkeypatch):
    headers = _admin_headers(client)

    class FakeExternalSourceClient:
        def fetch(self, url: str) -> str:
            assert url == "https://example.org/euraxess.json"
            return """
            {
              "results": [
                {
                  "title": "EURAXESS AI Postdoc",
                  "url": "https://example.org/euraxess/ai-postdoc",
                  "summary": "Mobility postdoc for trustworthy AI.",
                  "type": "research_position",
                  "country": "France",
                  "keywords": ["AI", "mobility"]
                }
              ]
            }
            """

    monkeypatch.setattr("app.services.external_sources.ExternalSourceClient", lambda: FakeExternalSourceClient())

    response = client.post(
        "/ingestion/external-source/import",
        headers=headers,
        json={
            "source_name": "euraxess",
            "source_url": "https://example.org/euraxess.json",
            "source_kind": "json",
            "import_results": True,
            "limit": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "euraxess"
    assert body["imported_count"] == 1
    assert body["opportunities"][0]["title"] == "EURAXESS AI Postdoc"

    sources_response = client.get("/sources")
    assert sources_response.status_code == 200
    assert sources_response.json()[0]["name"] == "euraxess"


def test_external_source_import_requires_admin(client):
    response = client.post(
        "/ingestion/external-source/import",
        json={
            "source_name": "euraxess",
            "source_url": "https://example.org/euraxess.json",
            "source_kind": "json",
        },
    )

    assert response.status_code == 401


def test_external_source_url_blocks_private_networks():
    blocked_urls = [
        "http://127.0.0.1/feed.xml",
        "http://localhost/feed.xml",
        "http://10.0.0.5/feed.xml",
        "http://user:password@example.org/feed.xml",
    ]

    for url in blocked_urls:
        try:
            validate_external_source_url(url)
        except BadRequestError as exc:
            assert "External source" in str(exc)
        else:
            raise AssertionError(f"Expected URL to be blocked: {url}")


def test_source_specific_connectors_normalize_fixture_payloads():
    euraxess = get_source_connector("euraxess").normalize(
        {
            "title": "AI Mobility Postdoc",
            "applyUrl": "https://example.org/euraxess/apply",
            "offerDescription": "Postdoctoral mobility role for trustworthy AI.",
            "hosting_country": "France",
            "researcherProfile": "postdoc",
        }
    )
    daad = get_source_connector("daad").normalize(
        {
            "name": "Climate Adaptation Fellowship",
            "link": "https://example.org/daad/climate",
            "programmeDescription": "Funding for climate adaptation research.",
            "applicationDeadline": "2026-10-01",
        }
    )
    fulbright = get_source_connector("fulbright").normalize(
        {
            "title": "Visiting Scholar Award",
            "url": "https://example.org/fulbright/scholar",
            "award_description": "Exchange award for visiting scholars.",
            "host_country": "United States",
        }
    )
    msca = get_source_connector("msca").normalize(
        {
            "title": "Postdoctoral Fellowships",
            "url": "https://example.org/msca/postdoc",
            "callAbstract": "Horizon Europe fellowship call.",
            "deadlineDate": "2026-09-10",
        }
    )
    nrfu = get_source_connector("nrfu").normalize(
        {
            "title": "Competition for young scientists",
            "url": "https://example.org/nrfu/young-scientists",
            "description": "Research grant for young scientists in Ukraine.",
        }
    )
    house = get_source_connector("house_of_europe").normalize(
        {
            "title": "Mobility grant for Ukrainian researchers",
            "url": "https://example.org/house/mobility",
            "teaser": "EU mobility support for Ukrainian researchers.",
        }
    )
    science_for_ukraine = get_source_connector("science_for_ukraine").normalize(
        {
            "title": "Postdoctoral research position for displaced scholars",
            "url": "https://example.org/scienceforukraine/postdoc",
            "location": "Poland",
        }
    )
    msca4ukraine = get_source_connector("msca4ukraine").normalize(
        {
            "title": "MSCA4Ukraine fellowship",
            "url": "https://example.org/msca4ukraine/fellowship",
            "deadlineDate": "2026-11-01",
        }
    )
    horizon = get_source_connector("horizon_europe").normalize(
        {
            "title": "Horizon Europe climate research call",
            "url": "https://example.org/horizon/climate",
            "topicDescription": "Collaborative research and innovation action.",
            "deadlineDate": "2026-12-10",
            "destination": "Climate, Energy and Mobility",
        }
    )
    erasmus = get_source_connector("erasmus").normalize(
        {
            "title": "Erasmus+ mobility for doctoral researchers",
            "url": "https://example.org/erasmus/mobility",
            "description": "Mobility exchange for doctoral candidates and university staff.",
        }
    )
    nawa = get_source_connector("nawa").normalize(
        {
            "title": "Banach NAWA Programme 2026",
            "url": "https://example.org/nawa/banach",
            "programmeDescription": "Scholarship programme for second-cycle studies in Poland.",
            "applicationDeadline": "2026-06-25",
        }
    )

    assert euraxess.opportunity_type.value == "research_position"
    assert euraxess.url == "https://example.org/euraxess/apply"
    assert euraxess.countries == ["France"]
    assert "euraxess" in euraxess.keywords
    assert daad.countries == ["Germany"]
    assert daad.deadline == "2026-10-01"
    assert fulbright.countries == ["United States"]
    assert "exchange" in fulbright.keywords
    assert msca.countries == ["European Union"]
    assert "horizon europe" in msca.keywords
    assert nrfu.countries == ["Ukraine"]
    assert nrfu.opportunity_type.value == "grant"
    assert "early-career" in nrfu.career_stages
    assert house.countries == ["Ukraine", "European Union"]
    assert "house of europe" in house.keywords
    assert science_for_ukraine.countries == ["Poland"]
    assert "postdoc" in science_for_ukraine.career_stages
    assert msca4ukraine.countries == ["Ukraine", "European Union"]
    assert "msca4ukraine" in msca4ukraine.keywords
    assert horizon.countries == ["European Union"]
    assert horizon.opportunity_type.value == "grant"
    assert "horizon europe" in horizon.keywords
    assert horizon.deadline == "2026-12-10"
    assert erasmus.countries == ["European Union"]
    assert erasmus.opportunity_type.value == "exchange"
    assert "phd" in erasmus.career_stages
    assert nawa.countries == ["Poland"]
    assert nawa.deadline == "2026-06-25"
    assert "nawa" in nawa.keywords
