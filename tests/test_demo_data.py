from datetime import datetime, timezone

import pytest

from scripts.seed_demo_data import (
    CATEGORIES,
    DEMO_MARKER,
    generate_demo_observations,
    insert_demo_data,
    reset_demo_data,
)
from app.config import get_locations
from app.database import get_connection, init_db
from app.schemas import ObservationCreate


def test_generation_is_deterministic_and_repeatable():
    first = generate_demo_observations(days=3, observations_per_day=4)
    second = generate_demo_observations(days=3, observations_per_day=4)
    assert first == second


def test_generated_rows_match_schema_and_controlled_values():
    rows = generate_demo_observations(days=2, observations_per_day=3)
    assert len(rows) == 6
    required = {
        "created_at", "location", "category", "severity", "description",
        "observed_at", "approximate_location_id", "crowd_level",
        "environmental_rating",
    }
    for row in rows:
        assert set(row) == required
        ObservationCreate.model_validate(row)
        assert row["location"] in get_locations()
        assert row["category"] in CATEGORIES
        assert all(1 <= row[field] <= 5 for field in ("severity", "crowd_level", "environmental_rating"))
        parsed = datetime.fromisoformat(row["observed_at"])
        assert parsed.tzinfo == timezone.utc
        assert row["approximate_location_id"].startswith(DEMO_MARKER)


def test_generated_descriptions_contain_no_pii_like_content():
    rows = generate_demo_observations(days=2, observations_per_day=5)
    text = " ".join(row["description"] for row in rows).lower()
    for forbidden in ("@", "phone", "email", "student id", "medical"):
        assert forbidden not in text


def test_safe_reset_removes_demo_rows_but_preserves_real_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("CAMPUSPULSE_DATABASE_PATH", str(tmp_path / "demo.db"))
    init_db()
    rows = generate_demo_observations(days=1, observations_per_day=2)
    with get_connection() as connection:
        insert_demo_data(connection, rows)
        connection.execute(
            """
            INSERT INTO observations (
                created_at, location, category, severity, description,
                observed_at, approximate_location_id, crowd_level, environmental_rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-09-23T00:00:00+00:00", "Library", "Other", 2,
                "Real observation kept during demo reset.",
                "2026-09-23T00:00:00+00:00", "real-zone-1", 2, 3,
            ),
        )
        connection.commit()
        assert reset_demo_data(connection) == 2
        remaining = connection.execute("SELECT approximate_location_id FROM observations").fetchall()
    assert [row[0] for row in remaining] == ["real-zone-1"]


def test_invalid_generation_size_is_rejected():
    with pytest.raises(ValueError):
        generate_demo_observations(days=0)
