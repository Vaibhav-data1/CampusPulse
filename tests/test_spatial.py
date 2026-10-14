import pandas as pd
import pytest

from app.ml.spatial import spatial_intelligence


def frame():
    return pd.DataFrame(
        [
            {"location": "Library", "category": "Noise", "severity": 4, "crowd_level": 3, "environmental_rating": 3, "observed_at": "2026-01-01T10:00:00Z"},
            {"location": "Library", "category": "Noise", "severity": 5, "crowd_level": None, "environmental_rating": 2, "observed_at": "2026-01-02T10:00:00Z"},
            {"location": "Cafeteria", "category": "Crowding", "severity": 3, "crowd_level": 5, "environmental_rating": None, "observed_at": "2026-01-01T10:00:00Z"},
            {"location": "Cafeteria", "category": "Noise", "severity": 2, "crowd_level": 4, "environmental_rating": 4, "observed_at": "2026-01-02T10:00:00Z"},
        ]
    )


def test_empty_includes_zero_observation_zones():
    result = spatial_intelligence(pd.DataFrame(columns=["location", "category", "severity"]), ["Library", "Cafeteria"])
    assert result["status"] == "empty"
    assert [zone["observation_count"] for zone in result["zones"]] == [0, 0]


def test_zone_metrics_and_intensity_are_deterministic():
    result = spatial_intelligence(frame(), ["Library", "Cafeteria", "Main Gate"])
    library = next(zone for zone in result["zones"] if zone["display_name"] == "Library")
    assert library["observation_count"] == 2
    assert library["dominant_category"] == "Noise"
    assert library["high_severity_count"] == 2
    assert library["intensity"] > 0
    assert next(zone for zone in result["zones"] if zone["display_name"] == "Main Gate")["intensity"] == 0


def test_category_filter_and_null_optional_values():
    result = spatial_intelligence(frame(), ["Library", "Cafeteria"], "Crowding")
    cafeteria = next(zone for zone in result["zones"] if zone["display_name"] == "Cafeteria")
    library = next(zone for zone in result["zones"] if zone["display_name"] == "Library")
    assert cafeteria["observation_count"] == 1
    assert cafeteria["average_environmental_rating"] is None
    assert library["observation_count"] == 0


def test_unexpected_location_is_retained_as_nonconfigured_zone():
    result = spatial_intelligence(
        pd.DataFrame([{"location": "Temporary Zone", "category": "Noise", "severity": 2}]),
        ["Library"],
    )
    assert any(zone["display_name"] == "Temporary Zone" for zone in result["zones"])


def test_missing_columns_are_rejected():
    with pytest.raises(ValueError, match="Missing required columns"):
        spatial_intelligence(pd.DataFrame({"location": ["Library"]}), ["Library"])
