def _register(client, email: str, password: str = "strong-password-123"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


def test_register_login_and_me(client):
    registered = _register(client, "ada@example.com")

    assert registered["access_token"]
    assert registered["user"]["email"] == "ada@example.com"

    login_response = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "strong-password-123"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ada@example.com"


def test_refresh_token_cookie_rotates_and_logout_revokes(client):
    registered = _register(client, "refresh@example.com")
    assert registered["access_token"]

    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"]
    assert refreshed["user"]["email"] == "refresh@example.com"
    assert refreshed["access_token"] != registered["access_token"]

    logout_response = client.post("/auth/logout", headers={"Authorization": f"Bearer {refreshed['access_token']}"})
    assert logout_response.status_code == 204

    denied_refresh = client.post("/auth/refresh")
    assert denied_refresh.status_code == 401


def test_auth_rate_limit_blocks_repeated_attempts(client):
    from app.core.config import settings
    from app.core.rate_limit import reset_rate_limits

    _register(client, "limited@example.com")
    original_enabled = settings.auth_rate_limit_enabled
    original_max = settings.auth_rate_limit_max_requests
    original_window = settings.auth_rate_limit_window_seconds
    settings.auth_rate_limit_enabled = True
    settings.auth_rate_limit_max_requests = 2
    settings.auth_rate_limit_window_seconds = 60
    reset_rate_limits()
    try:
        payload = {"email": "limited@example.com", "password": "wrong-password"}
        assert client.post("/auth/login", json=payload).status_code == 401
        assert client.post("/auth/login", json=payload).status_code == 401
        limited = client.post("/auth/login", json=payload)
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "http_error"
    finally:
        settings.auth_rate_limit_enabled = original_enabled
        settings.auth_rate_limit_max_requests = original_max
        settings.auth_rate_limit_window_seconds = original_window
        reset_rate_limits()


def test_orcid_start_requires_configuration(client):
    response = client.get("/auth/orcid/start")

    assert response.status_code == 503


def test_auth_providers_report_orcid_availability(client):
    response = client.get("/auth/providers")

    assert response.status_code == 200
    assert response.json()["orcid_oauth_enabled"] is False


def test_orcid_callback_creates_passwordless_user(client, monkeypatch):
    from app.api import auth as auth_api
    from app.core.config import settings
    from app.services.orcid_oauth import create_orcid_state

    original_frontend_base_url = settings.frontend_base_url
    settings.frontend_base_url = "http://frontend.test"

    def fake_exchange_authorization_code(code: str):
        assert code == "auth-code"
        return {"orcid": "0000-0002-1825-0097", "name": "Ada Lovelace"}

    class FakeImportResult:
        class Profile:
            id = 1

        profile = Profile()

    monkeypatch.setattr(auth_api, "exchange_authorization_code", fake_exchange_authorization_code)
    monkeypatch.setattr(auth_api, "import_orcid_profile_service", lambda *args, **kwargs: FakeImportResult())
    try:
        response = client.get(
            "/auth/orcid/callback",
            params={"code": "auth-code", "state": create_orcid_state()},
            follow_redirects=False,
        )
    finally:
        settings.frontend_base_url = original_frontend_base_url

    assert response.status_code == 302
    assert response.headers["location"].startswith("http://frontend.test/orcid-callback?token=")

    token = response.headers["location"].split("token=", 1)[1]
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    user = me_response.json()
    assert user["auth_provider"] == "orcid"
    assert user["orcid_id"] == "0000-0002-1825-0097"
    assert user["password_login_enabled"] is False
    assert user["email_verified"] is True


def test_authenticated_profile_is_owned_and_visible_in_my_profiles(client):
    auth = _register(client, "owner@example.com")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    profile_response = client.post(
        "/profiles",
        json={
            "full_name": "Owner Researcher",
            "career_stage": "phd",
            "disciplines": ["Computer Science"],
            "keywords": ["machine learning"],
        },
        headers=headers,
    )

    assert profile_response.status_code == 201
    profile = profile_response.json()
    assert profile["user_id"] == auth["user"]["id"]

    my_profiles_response = client.get("/profiles/me", headers=headers)

    assert my_profiles_response.status_code == 200
    assert my_profiles_response.json()[0]["id"] == profile["id"]


def test_owned_profile_can_be_updated(client):
    auth = _register(client, "updater@example.com")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    profile = client.post(
        "/profiles",
        json={"full_name": "Draft Researcher", "career_stage": "phd"},
        headers=headers,
    ).json()

    response = client.put(
        f"/profiles/{profile['id']}",
        json={
            "full_name": "Updated Researcher",
            "career_stage": "postdoc",
            "country": "Ukraine",
            "disciplines": ["Computer Science", "Public Health"],
            "keywords": ["machine learning", "clinical decision support"],
            "preferred_countries": ["Germany"],
        },
        headers=headers,
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == profile["id"]
    assert updated["full_name"] == "Updated Researcher"
    assert updated["disciplines"] == ["Computer Science", "Public Health"]
    assert set(updated["keywords"]) == {"machine learning", "clinical decision support"}


def test_owned_profile_rejects_cross_user_access(client):
    owner = _register(client, "owner2@example.com")
    intruder = _register(client, "intruder@example.com")
    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
    intruder_headers = {"Authorization": f"Bearer {intruder['access_token']}"}

    profile = client.post(
        "/profiles",
        json={
            "full_name": "Private Researcher",
            "career_stage": "postdoc",
            "disciplines": ["Physics"],
            "keywords": ["quantum"],
        },
        headers=owner_headers,
    ).json()

    denied_response = client.get(f"/profiles/{profile['id']}", headers=intruder_headers)
    anonymous_response = client.get(f"/profiles/{profile['id']}")
    owner_response = client.get(f"/profiles/{profile['id']}", headers=owner_headers)

    assert denied_response.status_code == 403
    assert anonymous_response.status_code == 403
    assert owner_response.status_code == 200
