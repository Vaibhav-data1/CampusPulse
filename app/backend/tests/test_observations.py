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


def test_valid_structured_observation(client):
    response = client.post(
        "/api/v1/observations",
        json={
            "location": "Library",
            "category": "Crowding",
            "severity": 3,
            "description": "Study area is busy.",
            "observed_at": "2026-09-23T10:30:00Z",
            "approximate_location_id": "library-west-wing",
            "crowd_level": 5,
            "environmental_rating": 4,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["crowd_level"] == 5
    assert body["environmental_rating"] == 4
    assert body["approximate_location_id"] == "library-west-wing"


def test_invalid_category_is_rejected(client):
    response = client.post(
        "/api/v1/observations",
        json={"location": "Library", "category": "Food Quality", "severity": 2, "description": "Nope"},
    )
    assert response.status_code == 422


def test_invalid_rating_is_rejected(client):
    response = client.post(
        "/api/v1/observations",
        json={
            "location": "Library",
            "category": "Facilities",
            "severity": 2,
            "description": "Invalid crowd rating.",
            "crowd_level": 6,
        },
    )
    assert response.status_code == 422


def test_metadata_endpoint(client):
    response = client.get("/api/v1/observations/metadata")
    assert response.status_code == 200
    body = response.json()
    assert body["categories"] == [
        "Wi-Fi / Connectivity", "Crowding", "Cleanliness", "Noise",
        "Maintenance", "Safety", "Facilities", "Other",
    ]
    assert "Library" in body["locations"]


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
