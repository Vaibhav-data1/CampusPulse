from __future__ import annotations

from typing import Any

import pandas as pd

MINIMUM_PAIRS = 5


def compute_relationships(df: pd.DataFrame) -> dict[str, Any]:
    """Compute pairwise Spearman correlations between numeric observation features.

    Returns a list of relations with coefficient, p-value not computed (simple)
    and sample size. Requires at least MINIMUM_PAIRS rows after grouping.
    """
    if df.empty:
        return {"status": "insufficient_data", "message": "No data provided.", "relationships": []}

    # restrict to numeric candidate columns
    candidates = [
        "severity",
        "crowd_level",
        "environmental_rating",
        "sentiment_score",
    ]
    present = [c for c in candidates if c in df.columns]
    if not present:
        return {"status": "insufficient_data", "message": "No numeric feature columns present for relationship analysis.", "relationships": []}

    working = df[present].apply(pd.to_numeric, errors="coerce")
    working = working.dropna(how="all")
    if len(working) < MINIMUM_PAIRS:
        return {"status": "insufficient_data", "message": f"At least {MINIMUM_PAIRS} observations are required; found {len(working)}.", "relationships": []}

    corrs = working.corr(method="spearman")

    relationships: list[dict[str, Any]] = []
    n = len(working)
    for i, a in enumerate(present):
        for b in present[i + 1 :]:
            coef = corrs.at[a, b]
            relationships.append(
                {
                    "a": a,
                    "b": b,
                    "spearman_r": None if pd.isna(coef) else round(float(coef), 4),
                    "sample_size": n,
                    "interpretation": _interpret_coefficient(coef) if not pd.isna(coef) else "insufficient",
                }
            )

    return {"status": "ok", "relationships": relationships}


def _interpret_coefficient(coef: float | None) -> str:
    if coef is None:
        return "insufficient"
    c = abs(coef)
    if c >= 0.8:
        return "very strong"
    if c >= 0.6:
        return "strong"
    if c >= 0.4:
        return "moderate"
    if c >= 0.2:
        return "weak"
    return "negligible"
