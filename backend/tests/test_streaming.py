import pytest


def test_streaming_chat_fallback(client):
    client.post("/api/v1/auth/register", json={
        "email": "stream_user@example.com",
        "name": "Stream User",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "stream_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/streaming/chat", json={
        "message": "Hello AgentForge"
    }, headers=headers)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
