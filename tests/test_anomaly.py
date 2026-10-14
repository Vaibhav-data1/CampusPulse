import pandas as pd
import pytest

from app.ml.anomaly import detect_anomalies


def _observations(days: int = 8) -> pd.DataFrame:
    rows = []
    for day in range(days):
        rows.append(
            {
                "location": "Library",
                "category": "Noise",
                "severity": 2,
                "crowd_level": 2,
                "environmental_rating": 4,
                "observed_at": f"2026-01-{day + 1:02d}T10:00:00Z",
            }
        )
    return pd.DataFrame(rows)


def test_normal_dataset_returns_structured_result():
    result = detect_anomalies(_observations())
    assert result["status"] == "ok"
    assert result["group_count"] == 8
    assert {"anomaly_count", "anomalies"}.issubset(result)


def test_anomalous_dataset_identifies_unusual_location_day():
    frame = _observations()
    frame.loc[len(frame)] = {
        "location": "Library",
        "category": "Noise",
        "severity": 5,
        "crowd_level": 5,
        "environmental_rating": 1,
        "observed_at": "2026-03-15T18:00:00Z",
    }
    result = detect_anomalies(frame)
    assert result["status"] == "ok"
    assert result["anomaly_count"] >= 1
    assert any(item["period_start"] == "2026-03-15" for item in result["anomalies"])


def test_empty_dataset_is_insufficient():
    result = detect_anomalies(pd.DataFrame(columns=["location", "observed_at", "severity"]))
    assert result["status"] == "insufficient_data"
    assert result["anomaly_count"] == 0


def test_small_dataset_is_not_classified():
    result = detect_anomalies(_observations(days=4))
    assert result["status"] == "insufficient_data"
    assert result["anomalies"] == []


def test_nullable_optional_fields_are_supported():
    frame = _observations()
    frame.loc[0, "crowd_level"] = None
    frame.loc[1, "environmental_rating"] = None
    result = detect_anomalies(frame)
    assert result["status"] == "ok"


def test_missing_required_columns_is_rejected():
    with pytest.raises(ValueError, match="Missing required columns"):
        detect_anomalies(pd.DataFrame({"location": ["Library"], "severity": [2]}))
