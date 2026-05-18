import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings
from app.core.rate_limit import reset_rate_limits


@pytest.fixture
def client() -> TestClient:
    original_email_verification_required = settings.email_verification_required
    original_rate_limit_enabled = settings.auth_rate_limit_enabled
    original_embedding_provider = settings.embedding_provider
    original_opportunity_embedding_on_import = settings.opportunity_embedding_on_import
    original_embedding_prewarm_on_startup = settings.embedding_prewarm_on_startup
    original_opportunity_extraction_provider = settings.opportunity_extraction_provider
    original_opportunity_page_enrichment_enabled = settings.opportunity_page_enrichment_enabled
    settings.email_verification_required = False
    settings.auth_rate_limit_enabled = False
    settings.embedding_provider = "hash"
    settings.opportunity_embedding_on_import = True
    settings.embedding_prewarm_on_startup = False
    settings.opportunity_extraction_provider = "deterministic"
    settings.opportunity_page_enrichment_enabled = False
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
        reset_rate_limits()
        app.dependency_overrides.clear()
        if hasattr(app.state, "testing_session_factory"):
            delattr(app.state, "testing_session_factory")
