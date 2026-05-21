import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings
from app.core.rate_limit import reset_rate_limits
from app.db.models import User, UserRole


@pytest.fixture
def client() -> TestClient:
    original_email_verification_required = settings.email_verification_required
    original_rate_limit_enabled = settings.auth_rate_limit_enabled
    original_embedding_provider = settings.embedding_provider
    original_opportunity_embedding_on_import = settings.opportunity_embedding_on_import
    original_embedding_prewarm_on_startup = settings.embedding_prewarm_on_startup
    original_opportunity_extraction_provider = settings.opportunity_extraction_provider
    original_opportunity_page_enrichment_enabled = settings.opportunity_page_enrichment_enabled
    original_advisor_provider = settings.advisor_provider
    original_email_provider = settings.email_provider
    original_elasticsearch_enabled = settings.elasticsearch_enabled
    original_elasticsearch_index_on_import = settings.elasticsearch_index_on_import
    original_profile_enrichment_auto_openalex = settings.profile_enrichment_auto_openalex
    original_profile_enrichment_provider = settings.profile_enrichment_provider
    original_groq_api_key = settings.groq_api_key
    settings.email_verification_required = False
    settings.auth_rate_limit_enabled = False
    settings.embedding_provider = "hash"
    settings.opportunity_embedding_on_import = True
    settings.embedding_prewarm_on_startup = False
    settings.opportunity_extraction_provider = "deterministic"
    settings.opportunity_page_enrichment_enabled = False
    settings.advisor_provider = "deterministic"
    settings.email_provider = "console"
    settings.elasticsearch_enabled = False
    settings.elasticsearch_index_on_import = False
    settings.profile_enrichment_auto_openalex = False
    settings.profile_enrichment_provider = "deterministic"
    settings.groq_api_key = ""
    reset_rate_limits()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    app.state.testing_session_factory = TestingSessionLocal

    def override_get_db():
        db: Session = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        settings.email_verification_required = original_email_verification_required
        settings.auth_rate_limit_enabled = original_rate_limit_enabled
        settings.embedding_provider = original_embedding_provider
        settings.opportunity_embedding_on_import = original_opportunity_embedding_on_import
        settings.embedding_prewarm_on_startup = original_embedding_prewarm_on_startup
        settings.opportunity_extraction_provider = original_opportunity_extraction_provider
        settings.opportunity_page_enrichment_enabled = original_opportunity_page_enrichment_enabled
        settings.advisor_provider = original_advisor_provider
        settings.email_provider = original_email_provider
        settings.elasticsearch_enabled = original_elasticsearch_enabled
        settings.elasticsearch_index_on_import = original_elasticsearch_index_on_import
        settings.profile_enrichment_auto_openalex = original_profile_enrichment_auto_openalex
        settings.profile_enrichment_provider = original_profile_enrichment_provider
        settings.groq_api_key = original_groq_api_key
        reset_rate_limits()
        app.dependency_overrides.clear()
        if hasattr(app.state, "testing_session_factory"):
            delattr(app.state, "testing_session_factory")


def _register_user(client: TestClient, email: str, role: UserRole = UserRole.researcher) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password-123", "full_name": "Test User"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]

    if role != UserRole.researcher:
        SessionLocal = client.app.state.testing_session_factory
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).one()
            user.role = role
            db.commit()
        login = client.post(
            "/auth/login",
            json={"email": email, "password": "strong-password-123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def researcher_headers(client: TestClient) -> dict[str, str]:
    return _register_user(client, "researcher@example.com")


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    return _register_user(client, "admin@example.com", UserRole.admin)
