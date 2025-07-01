import pytest

@pytest.mark.anyio
async def test_create_note(client):
    login = await client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    response = await client.post("/notes/", json={"text": "My first note"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["text"] == "My first note"

@pytest.mark.anyio
async def test_get_notes(client):
    login = await client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    response = await client.get("/notes/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.anyio
async def test_get_single_note(client):
    login = await client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    create_resp = await client.post("/notes/", json={"text": "Test Note"}, headers={"Authorization": f"Bearer {token}"})
    note_id = create_resp.json()["id"]

    response = await client.get(f"/notes/{note_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == note_id

@pytest.mark.anyio
async def test_update_note(client):
    login = await client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    create_resp = await client.post("/notes/", json={"text": "Old Text"}, headers={"Authorization": f"Bearer {token}"})
    note_id = create_resp.json()["id"]

    response = await client.put(f"/notes/{note_id}", json={"text": "Updated Text"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["text"] == "Updated Text"

@pytest.mark.anyio
async def test_delete_note(client):
    login = await client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login.json()["access_token"]

    create_resp = await client.post("/notes/", json={"text": "To be deleted"}, headers={"Authorization": f"Bearer {token}"})
    note_id = create_resp.json()["id"]

    response = await client.delete(f"/notes/{note_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["detail"] == "Note deleted successfully"

    response = await client.get(f"/notes/{note_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
