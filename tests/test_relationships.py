import pandas as pd
from app.ml.relationships import compute_relationships


def test_relationships_insufficient():
    df = pd.DataFrame([])
    res = compute_relationships(df)
    assert res["status"] == "insufficient_data"


def test_relationships_positive_correlation():
    # severity and crowd_level strongly positively correlated
    rows = []
    for i in range(10):
        rows.append({"severity": float(i), "crowd_level": float(i * 2)})
    df = pd.DataFrame(rows)
    res = compute_relationships(df)
    assert res["status"] == "ok"
    rels = res["relationships"]
    # find pair a==severity and b==crowd_level
    pair = next((r for r in rels if (r["a"] == "severity" and r["b"] == "crowd_level") or (r["a"] == "crowd_level" and r["b"] == "severity")), None)
    assert pair is not None
    assert pair["sample_size"] == 10
    assert pair["spearman_r"] is not None
    assert pair["interpretation"] in ("strong", "very strong")
