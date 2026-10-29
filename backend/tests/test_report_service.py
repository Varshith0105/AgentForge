import pytest


def test_observability_metrics(client):
    client.post("/api/v1/auth/register", json={
        "email": "obs_user@example.com",
        "name": "Obs User",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "obs_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/observability/metrics", headers=headers)
    assert resp.status_code == 200
    assert "timestamp" in resp.json()
