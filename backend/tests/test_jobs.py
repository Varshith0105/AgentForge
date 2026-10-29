import pytest


def test_list_jobs(client):
    client.post("/api/v1/auth/register", json={
        "email": "jobs_user@example.com",
        "name": "Jobs User",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "jobs_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/jobs", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
