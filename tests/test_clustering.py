import pandas as pd
from app.ml.clustering import detect_clusters, MINIMUM_GROUPS


def make_day(date_str):
    return date_str


def test_detect_clusters_insufficient():
    # fewer than MINIMUM_GROUPS groups -> insufficient
    rows = []
    for i in range(MINIMUM_GROUPS - 2):
        rows.append({"location": "A", "observed_at": f"2023-01-{i+1}T00:00:00Z", "severity": 3})
    df = pd.DataFrame(rows)
    res = detect_clusters(df)
    assert res["status"] == "insufficient_data"


def test_detect_clusters_ok_basic():
    # create two clear clusters: location X with high severity, location Y with low severity
    rows = []
    for d in range(1, 7):
        rows.append({"location": "X", "observed_at": f"2023-01-{d:02d}T08:00:00Z", "severity": 5})
        rows.append({"location": "Y", "observed_at": f"2023-01-{d:02d}T09:00:00Z", "severity": 1})
    df = pd.DataFrame(rows)
    res = detect_clusters(df)
    assert res["status"] == "ok"
    assert res["selected_k"] >= 2
    assert isinstance(res["clusters"], list)
    assert len(res["clusters"]) == res["selected_k"]


def test_detect_clusters_missing_columns():
    import pytest

    df = pd.DataFrame([{"location": "A", "observed_at": "2023-01-01T00:00:00Z"}])
    with pytest.raises(ValueError):
        detect_clusters(df)
