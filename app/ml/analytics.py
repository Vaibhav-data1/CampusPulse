from __future__ import annotations

import pandas as pd


def _datetime_series(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series([], dtype="datetime64[ns]")

    if "observed_at" in df.columns:
        source = "observed_at"
    elif "created_at" in df.columns:
        source = "created_at"
    else:
        return pd.Series([], dtype="datetime64[ns]")

    return pd.to_datetime(df[source], errors="coerce")


def counts_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Count observations grouped by category."""
    if df.empty or "category" not in df.columns:
        return pd.DataFrame(columns=["category", "observation_count"])

    counts = (
        df["category"].dropna().astype(str).value_counts().rename_axis("category").reset_index(name="observation_count")
    )
    return counts.sort_values("observation_count", ascending=False).reset_index(drop=True)


def counts_by_location(df: pd.DataFrame) -> pd.DataFrame:
    """Count observations grouped by location."""
    if df.empty or "location" not in df.columns:
        return pd.DataFrame(columns=["location", "observation_count"])

    counts = (
        df["location"].dropna().astype(str).value_counts().rename_axis("location").reset_index(name="observation_count")
    )
    return counts.sort_values("observation_count", ascending=False).reset_index(drop=True)


def average_severity_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean severity per category."""
    if df.empty or "category" not in df.columns or "severity" not in df.columns:
        return pd.DataFrame(columns=["category", "average_severity"])

    summary = (
        df[["category", "severity"]].dropna().groupby("category", dropna=False)["severity"].mean().reset_index()
    )
    summary = summary.rename(columns={"severity": "average_severity"})
    return summary.sort_values("average_severity", ascending=False).reset_index(drop=True)


def average_severity_by_location(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean severity per location."""
    if df.empty or "location" not in df.columns or "severity" not in df.columns:
        return pd.DataFrame(columns=["location", "average_severity"])

    summary = (
        df[["location", "severity"]].dropna().groupby("location", dropna=False)["severity"].mean().reset_index()
    )
    summary = summary.rename(columns={"severity": "average_severity"})
    return summary.sort_values("average_severity", ascending=False).reset_index(drop=True)


def average_crowd_level_by_location(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean crowd level per location for campus occupancy patterns."""
    if df.empty or "location" not in df.columns or "crowd_level" not in df.columns:
        return pd.DataFrame(columns=["location", "average_crowd_level"])

    summary = (
        df[["location", "crowd_level"]].dropna().groupby("location", dropna=False)["crowd_level"].mean().reset_index()
    )
    summary = summary.rename(columns={"crowd_level": "average_crowd_level"})
    return summary.sort_values("average_crowd_level", ascending=False).reset_index(drop=True)


def average_environmental_rating_by_location(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean environmental rating per location."""
    if df.empty or "location" not in df.columns or "environmental_rating" not in df.columns:
        return pd.DataFrame(columns=["location", "average_environmental_rating"])

    summary = (
        df[["location", "environmental_rating"]].dropna().groupby("location", dropna=False)["environmental_rating"].mean().reset_index()
    )
    summary = summary.rename(columns={"environmental_rating": "average_environmental_rating"})
    return summary.sort_values("average_environmental_rating", ascending=False).reset_index(drop=True)


def time_of_day_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize observation activity by hour of day (00:00 through 23:00)."""
    timestamps = _datetime_series(df)
    if timestamps.empty:
        return pd.DataFrame(columns=["hour", "hour_label", "observation_count"])

    valid = timestamps.dropna()
    if valid.empty:
        return pd.DataFrame(columns=["hour", "hour_label", "observation_count"])

    hourly_counts = valid.dt.hour.value_counts().rename_axis("hour").reset_index(name="observation_count")
    hourly_counts["hour"] = hourly_counts["hour"].astype(int)
    hourly_counts = hourly_counts.set_index("hour").reindex(range(24), fill_value=0).reset_index().rename(columns={"index": "hour"})
    hourly_counts["hour_label"] = hourly_counts["hour"].map(lambda value: f"{value:02d}:00")
    return hourly_counts[["hour", "hour_label", "observation_count"]].sort_values("hour").reset_index(drop=True)


def daily_weekly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Return daily and weekly observation counts for trend analysis."""
    timestamps = _datetime_series(df)
    if timestamps.empty:
        return pd.DataFrame(columns=["period_type", "period_start", "observation_count"])

    valid = timestamps.dropna()
    if valid.empty:
        return pd.DataFrame(columns=["period_type", "period_start", "observation_count"])

    daily = (
        valid.dt.floor("D").value_counts().rename_axis("period_start").reset_index(name="observation_count")
    )
    daily["period_type"] = "daily"
    weekly = (
        valid.dt.to_period("W-MON").apply(lambda value: value.start_time).value_counts().rename_axis("period_start").reset_index(name="observation_count")
    )
    weekly["period_type"] = "weekly"
    result = pd.concat([daily, weekly], ignore_index=True)
    result["period_start"] = pd.to_datetime(result["period_start"]).dt.strftime("%Y-%m-%d")
    result = result[["period_type", "period_start", "observation_count"]]
    return result.sort_values(["period_type", "period_start"], ascending=[True, True]).reset_index(drop=True)


def location_category_hotspots(df: pd.DataFrame) -> pd.DataFrame:
    """Rank location-category combinations by observation volume and average severity."""
    required = {"location", "category", "severity"}
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame(columns=["location", "category", "observation_count", "average_severity", "severity_score"])

    subset = df[["location", "category", "severity"]].dropna()
    if subset.empty:
        return pd.DataFrame(columns=["location", "category", "observation_count", "average_severity", "severity_score"])

    counts = subset.groupby(["location", "category"]).size().rename("observation_count")
    average_severity = subset.groupby(["location", "category"])["severity"].mean().rename("average_severity")
    result = counts.to_frame().join(average_severity).reset_index()
    result["severity_score"] = result["observation_count"] * result["average_severity"]
    result = result.sort_values(["severity_score", "observation_count", "average_severity"], ascending=[False, False, False])
    return result.reset_index(drop=True)


def basic_data_quality_statistics(df: pd.DataFrame) -> dict:
    """Report high-level data quality measures for downstream analytics and modeling."""
    if df.empty:
        return {
            "total_observations": 0,
            "missing_values": {},
            "unique_locations": 0,
            "unique_categories": 0,
            "date_range": {"start": None, "end": None},
        }

    timestamps = _datetime_series(df)
    valid_dates = timestamps.dropna()
    date_range = {"start": valid_dates.min() if not valid_dates.empty else None, "end": valid_dates.max() if not valid_dates.empty else None}

    return {
        "total_observations": int(len(df)),
        "missing_values": df.isna().sum().astype(int).to_dict(),
        "unique_locations": int(df["location"].dropna().nunique()) if "location" in df.columns else 0,
        "unique_categories": int(df["category"].dropna().nunique()) if "category" in df.columns else 0,
        "date_range": date_range,
    }
