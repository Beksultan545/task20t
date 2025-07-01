import pytest

@pytest.mark.anyio
async def test_get_me_unauthorized(client):
    response = await client.get("/users/me")
    assert response.status_code == 401

@pytest.mark.anyio
async def test_get_me_authorized(client):
    login = await client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    response = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
