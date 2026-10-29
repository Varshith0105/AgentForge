import pytest


def test_project_summary(client):
    client.post("/api/v1/auth/register", json={
        "email": "summary_user@example.com",
        "name": "Summary User",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "summary_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj = client.post("/api/v1/projects", json={
        "name": "Summary Test Repo"
    }, headers=headers).json()

    resp = client.get(f"/api/v1/projects/{proj['id']}/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"]["name"] == "Summary Test Repo"
