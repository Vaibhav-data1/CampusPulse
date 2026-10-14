import sqlite3

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import get_db
from app.ml.anomaly import detect_anomalies
from app.ml.spatial import spatial_intelligence
from app.ml.nlp import analyze_nlp
from ..config import get_locations

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _empty_summary() -> dict:
    return {
        "total_observations": 0,
        "by_category": [],
        "by_location": [],
        "average_severity_by_category": [],
        "average_severity_by_location": [],
        "average_crowd_level": [],
        "average_environmental_rating": [],
        "time_of_day_patterns": [],
        "daily_weekly_trends": [],
        "location_category_hotspots": [],
    }


def _records(frame: pd.DataFrame, value_columns: list[str]) -> list[dict]:
    if frame.empty:
        return []
    return frame[value_columns].where(pd.notna(frame[value_columns]), None).to_dict("records")


@router.get("/summary")
def analytics_summary(connection: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        rows = connection.execute("SELECT * FROM observations").fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve analytics data") from exc

    if not rows:
        return _empty_summary()

    frame = pd.DataFrame([dict(row) for row in rows])
    timestamps = pd.to_datetime(frame["observed_at"], errors="coerce", utc=True)
    valid = frame.loc[timestamps.notna()].copy()
    valid["timestamp"] = timestamps[timestamps.notna()]

    by_category = frame["category"].value_counts().rename_axis("category").reset_index(name="observation_count")
    by_location = frame["location"].value_counts().rename_axis("location").reset_index(name="observation_count")

    severity_category = (
        frame[["category", "severity"]].dropna().groupby("category")["severity"].mean()
        .rename("average_severity").reset_index()
        .sort_values(["average_severity", "category"], ascending=[False, True], kind="stable")
    )
    severity_location = (
        frame[["location", "severity"]].dropna().groupby("location")["severity"].mean()
        .rename("average_severity").reset_index()
        .sort_values(["average_severity", "location"], ascending=[False, True], kind="stable")
    )
    crowd = (
        frame[["location", "crowd_level"]].dropna().groupby("location")["crowd_level"].mean()
        .rename("average_crowd_level").reset_index()
        .sort_values(["average_crowd_level", "location"], ascending=[False, True], kind="stable")
    )
    environment = (
        frame[["location", "environmental_rating"]].dropna().groupby("location")["environmental_rating"].mean()
        .rename("average_environmental_rating").reset_index()
        .sort_values(["average_environmental_rating", "location"], ascending=[False, True], kind="stable")
    )

    hourly = valid["timestamp"].dt.hour.value_counts().rename_axis("hour").reset_index(name="observation_count")
    hourly = hourly.set_index("hour").reindex(range(24), fill_value=0).reset_index()
    hourly["hour_label"] = hourly["hour"].map(lambda hour: f"{hour:02d}:00")

    if valid.empty:
        trends = pd.DataFrame(columns=["period_type", "period_start", "observation_count"])
    else:
        daily = valid["timestamp"].dt.floor("D").value_counts().rename_axis("period_start").reset_index(name="observation_count")
        daily["period_type"] = "daily"
        weekly = (
            valid["timestamp"].dt.tz_localize(None).dt.to_period("W-MON")
            .apply(lambda period: period.start_time).value_counts()
            .rename_axis("period_start").reset_index(name="observation_count")
        )
        weekly["period_type"] = "weekly"
        trends = pd.concat([daily, weekly], ignore_index=True)
        trends["period_start"] = pd.to_datetime(trends["period_start"], utc=True).dt.strftime("%Y-%m-%d")
        trends = trends[["period_type", "period_start", "observation_count"]].sort_values(
            ["period_type", "period_start"], kind="stable"
        )

    hotspot_source = frame[["location", "category", "severity"]].dropna()
    hotspots = (
        hotspot_source.groupby(["location", "category"]).agg(
            observation_count=("severity", "size"),
            average_severity=("severity", "mean"),
        ).reset_index()
    )
    hotspots["severity_score"] = hotspots["observation_count"] * hotspots["average_severity"]
    hotspots = hotspots.sort_values(
        ["severity_score", "observation_count", "average_severity", "location", "category"],
        ascending=[False, False, False, True, True], kind="stable",
    )

    return {
        "total_observations": int(len(frame)),
        "by_category": _records(by_category, ["category", "observation_count"]),
        "by_location": _records(by_location, ["location", "observation_count"]),
        "average_severity_by_category": _records(severity_category, ["category", "average_severity"]),
        "average_severity_by_location": _records(severity_location, ["location", "average_severity"]),
        "average_crowd_level": _records(crowd, ["location", "average_crowd_level"]),
        "average_environmental_rating": _records(environment, ["location", "average_environmental_rating"]),
        "time_of_day_patterns": _records(hourly, ["hour", "hour_label", "observation_count"]),
        "daily_weekly_trends": _records(trends, ["period_type", "period_start", "observation_count"]),
        "location_category_hotspots": _records(
            hotspots, ["location", "category", "observation_count", "average_severity", "severity_score"]
        ),
    }


@router.get("/anomalies")
def analytics_anomalies(connection: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        rows = connection.execute("SELECT * FROM observations").fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve anomaly data") from exc
    frame = pd.DataFrame([dict(row) for row in rows])
    return detect_anomalies(frame) if not frame.empty else detect_anomalies(
        pd.DataFrame(columns=["location", "observed_at", "severity"])
    )


@router.get("/spatial")
def analytics_spatial(
    category: str | None = Query(default=None, min_length=1, max_length=100),
    connection: sqlite3.Connection = Depends(get_db),
) -> dict:
    try:
        rows = connection.execute("SELECT * FROM observations").fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve spatial analytics data") from exc
    frame = pd.DataFrame([dict(row) for row in rows])
    if frame.empty:
        frame = pd.DataFrame(columns=["location", "category", "severity"])
    return spatial_intelligence(frame, get_locations(), category)


@router.get("/nlp")
def analytics_nlp(
    category: str | None = Query(default=None, min_length=1, max_length=100),
    connection: sqlite3.Connection = Depends(get_db),
) -> dict:
    try:
        rows = connection.execute("SELECT * FROM observations").fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve NLP analytics data") from exc
    frame = pd.DataFrame([dict(row) for row in rows])
    if frame.empty:
        frame = pd.DataFrame(columns=["description", "category", "location", "observed_at"])
    if category is not None and "category" in frame:
        frame = frame[frame["category"] == category]
    return analyze_nlp(frame)


from app.ml.clustering import detect_clusters
from app.ml.relationships import compute_relationships


@router.get("/clusters")
def analytics_clusters(
    connection: sqlite3.Connection = Depends(get_db),
) -> dict:
    try:
        rows = connection.execute("SELECT * FROM observations").fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve clustering data") from exc
    frame = pd.DataFrame([dict(row) for row in rows])
    if frame.empty:
        frame = pd.DataFrame(columns=["location", "observed_at", "severity", "crowd_level", "environmental_rating", "category"])
    return detect_clusters(frame)


@router.get("/relationships")
def analytics_relationships(
    connection: sqlite3.Connection = Depends(get_db),
) -> dict:
    try:
        rows = connection.execute("SELECT * FROM observations").fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve relationship data") from exc
    frame = pd.DataFrame([dict(row) for row in rows])
    if frame.empty:
        frame = pd.DataFrame(columns=["severity", "crowd_level", "environmental_rating", "description"])
    # attempt to coerce a sentiment_score if descriptions present and NLP analyzer available
    try:
        if "description" in frame and not frame["description"].isna().all():
            nlp = analyze_nlp(frame[["description"]].rename(columns={"description": "description"}))
            # nlp may produce per-observation sentiment under 'descriptions' key
            if isinstance(nlp, dict) and "descriptions" in nlp:
                descs = nlp["descriptions"]
                # align back if lengths match
                if len(descs) == len(frame):
                    frame = frame.copy()
                    frame["sentiment_score"] = [d.get("score") for d in descs]
    except Exception:
        pass

    # select numeric columns for relationships
    numeric = frame[[c for c in ["severity", "crowd_level", "environmental_rating", "sentiment_score"] if c in frame.columns]]
    return compute_relationships(numeric)
