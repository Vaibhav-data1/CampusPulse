from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

MINIMUM_GROUPS = 8


def _insufficient(message: str, available: int) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "message": message,
        "required_minimum": MINIMUM_GROUPS,
        "available_groups": available,
        "clusters": [],
    }


def _summarize_cluster(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "observation_count": int(len(df)),
        "average_severity": round(float(df["average_severity"].mean()), 3),
        "average_crowd_level": (
            round(float(df["average_crowd_level"].mean()), 3) if "average_crowd_level" in df and df["average_crowd_level"].notna().any() else None
        ),
        "average_environmental_rating": (
            round(float(df["average_environmental_rating"].mean()), 3) if "average_environmental_rating" in df and df["average_environmental_rating"].notna().any() else None
        ),
    }


def detect_clusters(df: pd.DataFrame, max_k: int = 6) -> dict[str, Any]:
    """Cluster location-day aggregates and return explainable summaries.

    Aggregation mirrors the anomaly detector: groups by location + UTC day and
    computes numeric features. Clustering is performed only when at least
    MINIMUM_GROUPS groups are available. The cluster count is selected by
    maximizing silhouette score over k = 2..candidate_k (bounded by data).
    """
    required = {"location", "observed_at", "severity"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if df.empty:
        return _insufficient("No observations available to cluster.", 0)

    working = df.copy()
    working["timestamp"] = pd.to_datetime(working["observed_at"], errors="coerce", utc=True)
    working["severity"] = pd.to_numeric(working["severity"], errors="coerce")
    working = working.dropna(subset=["location", "timestamp", "severity"]) 
    if working.empty:
        return _insufficient("No valid observations with location, date and severity.", 0)

    working["period_start"] = working["timestamp"].dt.strftime("%Y-%m-%d")
    grouped = (
        working.groupby(["location", "period_start"], sort=True)
        .agg(
            observation_count=("severity", "size"),
            average_severity=("severity", "mean"),
            average_crowd_level=("crowd_level", "mean") if "crowd_level" in working else ("severity", lambda _: None),
            average_environmental_rating=("environmental_rating", "mean") if "environmental_rating" in working else ("severity", lambda _: None),
        )
        .reset_index()
    )

    group_count = len(grouped)
    if group_count < MINIMUM_GROUPS:
        return _insufficient(f"At least {MINIMUM_GROUPS} location-day groups are required; found {group_count}.", group_count)

    features = ["observation_count", "average_severity"]
    if "average_crowd_level" in grouped:
        features.append("average_crowd_level")
    if "average_environmental_rating" in grouped:
        features.append("average_environmental_rating")

    X = grouped[features].apply(pd.to_numeric, errors="coerce")
    med = X.median()
    X = X.fillna(med).fillna(0)

    # Bound the candidate cluster count to the number of distinct feature patterns.
    # When repeated observations collapse to the same pattern, KMeans with a larger
    # k can warn or fail even though the data is structurally only a couple of
    # clusters. This preserves the model's behavior without creating spurious
    # warnings on tiny fixtures or low-variation datasets.
    unique_pattern_count = int(X.drop_duplicates().shape[0])
    if unique_pattern_count < 2:
        return _insufficient("Not enough distinct observation patterns to cluster reliably.", group_count)

    max_k_candidate = min(max_k, group_count - 1, unique_pattern_count)
    if max_k_candidate < 2:
        return _insufficient("Not enough distinct observation patterns to cluster reliably.", group_count)

    best_k = None
    best_score = -1.0
    best_labels = None
    for k in range(2, max_k_candidate + 1):
        try:
            model = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = model.fit_predict(X)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
                best_labels = labels
        except Exception:
            continue

    if best_k is None or best_labels is None:
        return {
            "status": "insufficient_data",
            "message": "Unable to find a stable clustering for the provided data.",
            "required_minimum": MINIMUM_GROUPS,
            "available_groups": group_count,
            "clusters": [],
        }

    grouped["cluster_id"] = best_labels
    clusters = []
    for cid in sorted(grouped["cluster_id"].unique()):
        members = grouped[grouped["cluster_id"] == cid]
        summary = _summarize_cluster(members)
        # dominant category/location
        dominant_category = None
        if "category" in working:
            cat = working.merge(members[["location", "period_start"]], on=["location", "period_start"]).dropna(subset=["category"])
            if not cat.empty:
                dominant_category = cat["category"].value_counts().idxmax()
        dominant_location = members["location"].mode().iat[0] if not members["location"].empty else None
        clusters.append({
            "cluster_id": int(cid),
            "observation_count": int(len(members)),
            "percentage": round(len(members) / group_count * 100, 1),
            "feature_profile": summary,
            "dominant_category": dominant_category,
            "dominant_location": str(dominant_location) if dominant_location is not None else None,
            "human_summary": (
                f"{int(len(members))} group(s) — avg severity {summary['average_severity']:.1f}/5"
                + (f", avg crowd {summary['average_crowd_level']:.1f}/5" if summary.get("average_crowd_level") is not None else "")
            ),
        })

    return {
        "status": "ok",
        "sample_size": group_count,
        "selected_k": best_k,
        "silhouette_score": round(float(best_score), 4),
        "clusters": clusters,
    }
