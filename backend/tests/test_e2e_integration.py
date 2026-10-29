import pytest


def test_e2e_user_flow(client):
    # 1. Register
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "e2e_user@example.com",
        "name": "E2E User",
        "password": "SecurePassword123!",
        "role": "engineer"
    })
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "e2e_user@example.com"

    # 2. Login
    login_resp = client.post("/api/v1/auth/login", data={
        "username": "e2e_user@example.com",
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Project
    proj_resp = client.post("/api/v1/projects", json={
        "name": "E2E Test Repo",
        "description": "Integration testing repository",
        "language": "python"
    }, headers=headers)
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 4. List Projects
    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 5. Start Analysis
    analysis_resp = client.post("/api/v1/analysis/start", json={
        "project_id": project_id,
        "analysis_type": "full"
    }, headers=headers)
    assert analysis_resp.status_code == 200
    assert analysis_resp.json()["status"] == "started"

    # 6. Check Cost Summary
    costs_resp = client.get("/api/v1/costs/summary", headers=headers)
    assert costs_resp.status_code == 200
    assert costs_resp.json()["currency"] == "USD"

    # 7. Check AI-OS config
    config_resp = client.get("/api/v1/ai-os/config", headers=headers)
    assert config_resp.status_code == 200
    assert "provider" in config_resp.json()
