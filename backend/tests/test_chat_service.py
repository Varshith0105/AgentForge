import pytest


def test_chat_creation_and_messages(client):
    # Register & Login
    client.post("/api/v1/auth/register", json={
        "email": "chat_user@example.com",
        "name": "Chat User",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", data={
        "username": "chat_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Chat
    chat_resp = client.post("/api/v1/chats", json={
        "title": "Architecture Discussion",
        "model": "gpt-4o"
    }, headers=headers)
    assert chat_resp.status_code == 201
    chat_id = chat_resp.json()["id"]

    # Get Chat Messages
    msg_resp = client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    assert msg_resp.status_code == 200
    assert isinstance(msg_resp.json(), list)
