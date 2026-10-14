from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.ensemble import IsolationForest

MINIMUM_GROUPS = 5
REQUIRED_COLUMNS = {"location", "observed_at", "severity"}
FEATURE_COLUMNS = [
    "observation_count",
    "average_severity",
    "average_crowd_level",
    "average_environmental_rating",
]


def _insufficient(message: str) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "message": message,
        "minimum_groups": MINIMUM_GROUPS,
        "group_count": 0,
        "anomaly_count": 0,
        "anomalies": [],
    }


def detect_anomalies(df: pd.DataFrame) -> dict[str, Any]:
    """Find unusual location-day patterns using Isolation Forest.

    Each valid observation contributes to a location/UTC-day aggregate. Optional
    crowd and environmental fields are median-imputed for model input only;
    their reported group averages remain null when no values were supplied.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_columns}")
    if df.empty:
        return _insufficient("At least five valid location-day groups are required.")

    working = df.copy()
    working["timestamp"] = pd.to_datetime(working["observed_at"], errors="coerce", utc=True)
    working["severity"] = pd.to_numeric(working["severity"], errors="coerce")
    working = working.dropna(subset=["location", "timestamp", "severity"])
    if working.empty:
        return _insufficient("At least five observations with valid location, date, and severity are required.")

    working["period_start"] = working["timestamp"].dt.strftime("%Y-%m-%d")
    grouped = (
        working.groupby(["location", "period_start"], sort=True)
        .agg(
            observation_count=("severity", "size"),
            average_severity=("severity", "mean"),
            average_crowd_level=("crowd_level", "mean") if "crowd_level" in working else ("severity", lambda _: None),
            average_environmental_rating=(
                ("environmental_rating", "mean")
                if "environmental_rating" in working
                else ("severity", lambda _: None)
            ),
        )
        .reset_index()
    )
    if "category" in working:
        category = (
            working.dropna(subset=["category"])
            .groupby(["location", "period_start"])["category"]
            .agg(lambda values: values.value_counts().index[0] if len(values) else None)
            .rename("dominant_category")
        )
        grouped = grouped.merge(category, on=["location", "period_start"], how="left")
    else:
        grouped["dominant_category"] = None

    group_count = len(grouped)
    if group_count < MINIMUM_GROUPS:
        result = _insufficient(
            f"At least {MINIMUM_GROUPS} valid location-day groups are required; found {group_count}."
        )
        result["group_count"] = group_count
        return result

    model_input = grouped[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    model_input = model_input.fillna(model_input.median()).fillna(0)
    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
    )
    predictions = model.fit_predict(model_input)
    grouped["anomaly_score"] = (-model.decision_function(model_input)).round(6)
    grouped["is_anomaly"] = predictions == -1

    anomalies = grouped[grouped["is_anomaly"]].copy()
    anomalies = anomalies.sort_values(
        ["anomaly_score", "period_start", "location"],
        ascending=[False, True, True],
        kind="stable",
    )
    records = []
    for row in anomalies.to_dict("records"):
        context = f"{row['observation_count']} observation(s), average severity {row['average_severity']:.1f}/5"
        if pd.notna(row["average_crowd_level"]):
            context += f", average crowd {row['average_crowd_level']:.1f}/5"
        if pd.notna(row["average_environmental_rating"]):
            context += f", average environmental rating {row['average_environmental_rating']:.1f}/5"
        records.append(
            {
                "location": row["location"],
                "period_start": row["period_start"],
                "dominant_category": row["dominant_category"],
                "observation_count": int(row["observation_count"]),
                "average_severity": round(float(row["average_severity"]), 3),
                "average_crowd_level": (
                    round(float(row["average_crowd_level"]), 3)
                    if pd.notna(row["average_crowd_level"])
                    else None
                ),
                "average_environmental_rating": (
                    round(float(row["average_environmental_rating"]), 3)
                    if pd.notna(row["average_environmental_rating"])
                    else None
                ),
                "anomaly_score": float(row["anomaly_score"]),
                "explanation": f"Unusual compared with observed location-day patterns: {context}.",
            }
        )

    return {
        "status": "ok",
        "message": "Anomalies are unusual compared with observed patterns, not necessarily problems.",
        "minimum_groups": MINIMUM_GROUPS,
        "group_count": group_count,
        "anomaly_count": len(records),
        "anomalies": records,
    }
