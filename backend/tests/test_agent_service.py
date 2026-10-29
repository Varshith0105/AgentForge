import pytest


def test_agent_status_unauthorized(client):
    response = client.get("/api/v1/agents/status")
    assert response.status_code == 401


def test_agent_status_authorized(client):
    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": "agent_test@example.com",
        "name": "Agent Tester",
        "password": "Password123!",
        "role": "developer"
    })
    assert reg.status_code == 201

    # Login
    login = client.post("/api/v1/auth/login", data={
        "username": "agent_test@example.com",
        "password": "Password123!"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Request agent status
    response = client.get(
        "/api/v1/agents/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert data["total"] == 8
    assert data["active"] == 8
