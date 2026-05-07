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
