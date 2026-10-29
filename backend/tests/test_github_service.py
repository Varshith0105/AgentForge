import pytest


def test_github_invalid_url(client):
    client.post("/api/v1/auth/register", json={
        "email": "gh_user@example.com",
        "name": "GH User",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "gh_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/github/repo-info?repo_url=invalid", headers=headers)
    assert resp.status_code == 400
