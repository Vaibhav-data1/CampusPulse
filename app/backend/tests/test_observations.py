import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("CAMPUSPULSE_DATABASE_PATH", str(database_path))
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_observation(client):
    payload = {
        "location": "Library",
        "category": "Noise",
        "severity": 4,
        "description": "Loud construction near the study area.",
    }
    created = client.post("/api/v1/observations", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["location"] == "Library"
    assert body["severity"] == 4
    assert "id" in body and "created_at" in body

    listed = client.get("/api/v1/observations", params={"category": "Noise"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_validation_rejects_invalid_severity(client):
    response = client.post(
        "/api/v1/observations",
        json={
            "location": "Cafeteria",
            "category": "Cleanliness",
            "severity": 6,
            "description": "Invalid severity.",
        },
    )
    assert response.status_code == 422


def test_date_range_validation(client):
    response = client.get(
        "/api/v1/observations",
        params={"start_date": "2026-02-01T00:00:00Z", "end_date": "2026-01-01T00:00:00Z"},
    )
    assert response.status_code == 400
