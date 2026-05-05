from app.db.models import User, UserRole


def _auth_headers(client, email: str, role: UserRole = UserRole.researcher) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password-123", "full_name": "Role User"},
    )
    if role != UserRole.researcher:
        SessionLocal = client.app.state.testing_session_factory
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            user.role = role
            db.commit()
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "strong-password-123"},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def test_admin_endpoints_require_admin_role(client):
    researcher_headers = _auth_headers(client, "researcher@example.com")
    admin_headers = _auth_headers(client, "real-admin@example.com", UserRole.admin)

    denied = client.get("/admin/dashboard", headers=researcher_headers)
    allowed = client.get("/admin/dashboard", headers=admin_headers)

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "forbidden"
    assert denied.json()["error"]["message"] == "Admin access required"
    assert denied.headers["X-Request-ID"] == denied.json()["error"]["request_id"]
    assert allowed.status_code == 200


def test_request_id_header_is_echoed_on_success_and_error(client):
    success = client.get("/health", headers={"X-Request-ID": "test-request-123"})
    error = client.get("/opportunities/999", headers={"X-Request-ID": "missing-opportunity-123"})

    assert success.status_code == 200
    assert success.headers["X-Request-ID"] == "test-request-123"
    assert error.status_code == 404
    assert error.headers["X-Request-ID"] == "missing-opportunity-123"
    assert error.json() == {
        "error": {
            "code": "not_found",
            "message": "Opportunity not found",
            "request_id": "missing-opportunity-123",
        }
    }


def test_validation_errors_use_standard_error_envelope(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "x", "full_name": ""},
        headers={"X-Request-ID": "validation-123"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["request_id"] == "validation-123"
    assert "email" in body["error"]["message"]
