from __future__ import annotations

import re
from typing import Any, Iterable

import pandas as pd

from .anomaly import detect_anomalies

REQUIRED_COLUMNS = {"location", "category", "severity"}
ZONE_COLUMNS = [
    "zone_id",
    "display_name",
    "layout",
    "intensity",
    "observation_count",
    "average_severity",
    "high_severity_count",
    "average_crowd_level",
    "average_environmental_rating",
    "dominant_category",
    "category_distribution",
    "anomaly_count",
]


def _zone_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "unknown"


def build_zone_metadata(locations: Iterable[str]) -> list[dict[str, Any]]:
    """Return stable abstract layout metadata; positions are not geographic coordinates."""
    names = list(dict.fromkeys(str(location).strip() for location in locations if str(location).strip()))
    columns = 3
    return [
        {
            "zone_id": _zone_id(name),
            "display_name": name,
            "layout": {"row": index // columns, "column": index % columns},
        }
        for index, name in enumerate(names)
    ]


def _empty_zone(zone: dict[str, Any]) -> dict[str, Any]:
    return {
        **zone,
        "intensity": 0.0,
        "observation_count": 0,
        "average_severity": None,
        "high_severity_count": 0,
        "average_crowd_level": None,
        "average_environmental_rating": None,
        "dominant_category": None,
        "category_distribution": [],
        "anomaly_count": 0,
    }


def spatial_intelligence(
    df: pd.DataFrame,
    locations: Iterable[str],
    category: str | None = None,
) -> dict[str, Any]:
    """Aggregate explainable zone-level metrics for an abstract campus heatmap.

    Intensity is a 0-100 score:
    40% frequency (zone count / busiest included zone), 40% average severity
    (average / 5), 10% average crowd (average / 5), and 10% environmental
    concern (1 - average rating / 5). Missing optional metrics redistribute
    their weight proportionally across available components.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    zones = build_zone_metadata(locations)
    result = [_empty_zone(zone) for zone in zones]
    if df.empty:
        return {
            "status": "empty",
            "category": category,
            "zone_count": len(result),
            "zones": result,
            "insights": [],
        }

    working = df.copy()
    for field in ("severity", "crowd_level", "environmental_rating"):
        if field in working:
            working[field] = pd.to_numeric(working[field], errors="coerce")
    working["location"] = working["location"].astype("string").str.strip()
    working["category"] = working["category"].astype("string").str.strip()
    working = working.dropna(subset=["location", "category", "severity"])
    if category is not None:
        working = working[working["category"] == category]

    configured = {zone["display_name"]: index for index, zone in enumerate(zones)}
    unexpected = sorted(set(working["location"].dropna()) - set(configured))
    if unexpected:
        zones.extend(build_zone_metadata(unexpected))
        result.extend(_empty_zone(zone) for zone in zones[len(result):])
        configured.update({zone["display_name"]: index for index, zone in enumerate(zones)})

    if working.empty:
        return {
            "status": "empty",
            "category": category,
            "zone_count": len(result),
            "zones": result,
            "insights": [],
        }

    grouped = working.groupby("location", sort=True)
    counts = grouped.size()
    max_count = float(counts.max()) or 1.0
    anomaly_counts: dict[str, int] = {}
    if "observed_at" in working:
        anomaly_data = detect_anomalies(working)
        for anomaly in anomaly_data.get("anomalies", []):
            anomaly_counts[anomaly["location"]] = anomaly_counts.get(anomaly["location"], 0) + 1

    for name, group in grouped:
        index = configured.get(str(name))
        if index is None:
            continue
        severity = float(group["severity"].mean())
        crowd = float(group["crowd_level"].mean()) if "crowd_level" in group and group["crowd_level"].notna().any() else None
        environment = (
            float(group["environmental_rating"].mean())
            if "environmental_rating" in group and group["environmental_rating"].notna().any()
            else None
        )
        components = [
            (0.4, float(counts[name]) / max_count),
            (0.4, severity / 5),
        ]
        if crowd is not None:
            components.append((0.1, crowd / 5))
        if environment is not None:
            components.append((0.1, 1 - environment / 5))
        total_weight = sum(weight for weight, _ in components)
        intensity = round(100 * sum(weight * value for weight, value in components) / total_weight, 2)
        category_counts = group["category"].value_counts()
        result[index].update(
            intensity=intensity,
            observation_count=int(counts[name]),
            average_severity=round(severity, 3),
            high_severity_count=int((group["severity"] >= 4).sum()),
            average_crowd_level=round(crowd, 3) if crowd is not None else None,
            average_environmental_rating=round(environment, 3) if environment is not None else None,
            dominant_category=str(category_counts.index[0]),
            category_distribution=[
                {"category": str(key), "observation_count": int(value)}
                for key, value in category_counts.items()
            ],
            anomaly_count=anomaly_counts.get(str(name), 0),
        )

    populated = [zone for zone in result if zone["observation_count"]]
    insights: list[str] = []
    if populated:
        highest = max(populated, key=lambda zone: (zone["intensity"], zone["display_name"]))
        insights.append(f"{highest['display_name']} has the highest observation intensity.")
        category_locations: dict[str, dict[str, Any]] = {}
        for zone in populated:
            if zone["dominant_category"]:
                category_locations.setdefault(zone["dominant_category"], {"name": zone["display_name"], "count": 0})
                category_locations[zone["dominant_category"]]["count"] += zone["category_distribution"][0]["observation_count"]
        if category_locations:
            top_category, location = max(category_locations.items(), key=lambda item: (item[1]["count"], item[0]))
            insights.append(f"{top_category} observations are concentrated in {location['name']}.")

    return {
        "status": "ok",
        "category": category,
        "zone_count": len(result),
        "zones": result,
        "insights": insights,
    }
