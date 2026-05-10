import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings


@pytest.fixture
def client() -> TestClient:
    original_email_verification_required = settings.email_verification_required
    settings.email_verification_required = False
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
        app.dependency_overrides.clear()
        if hasattr(app.state, "testing_session_factory"):
            delattr(app.state, "testing_session_factory")
