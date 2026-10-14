"""Generate a deterministic, synthetic observation dataset for local demos.

This module is intentionally separate from the production API. Demo rows are
marked in the existing approximate-location field because the current schema
has no provenance column; the marker is only used for safe, targeted resets.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "app" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import CATEGORIES, get_locations  # noqa: E402
from app.database import get_connection, init_db  # noqa: E402

SEED = 20260924
DEMO_MARKER = "demo-seed-v1:"
DEFAULT_DAYS = 90
OBSERVATIONS_PER_DAY = 12

_CATEGORY_BASE = {
    "Wi-Fi / Connectivity": (3, 2, 2),
    "Crowding": (4, 4, 3),
    "Cleanliness": (3, 3, 2),
    "Noise": (4, 4, 2),
    "Maintenance": (3, 2, 2),
    "Safety": (2, 2, 3),
    "Facilities": (3, 2, 3),
    "Other": (2, 2, 3),
}
_DESCRIPTIONS = {
    "Wi-Fi / Connectivity": [
        "Wireless connection is stable near the study tables.",
        "Network access is slow during the busiest study period.",
        "Several workstations briefly lost connectivity.",
    ],
    "Crowding": [
        "Seating is comfortable with plenty of room to move.",
        "The area is busy and finding an open seat takes time.",
        "A queue is forming near the entrance during the midday rush.",
    ],
    "Cleanliness": [
        "The area looks tidy and bins are not overflowing.",
        "A few tables need attention after the lunch period.",
        "The walkway is clean and easy to use.",
    ],
    "Noise": [
        "The space is quiet enough for focused work.",
        "Conversation and nearby activity make the area noticeably loud.",
        "A short burst of construction noise interrupted the space.",
    ],
    "Maintenance": [
        "Fixtures appear to be working as expected.",
        "A door is difficult to close and may need adjustment.",
        "A light is flickering near the shared walkway.",
    ],
    "Safety": [
        "The route is well lit and feels clear to navigate.",
        "A blocked path makes movement less comfortable than usual.",
        "Signage is visible and the area is easy to navigate.",
    ],
    "Facilities": [
        "Available facilities are in good working order.",
        "One shared fixture appears temporarily unavailable.",
        "The space is comfortable and resources are easy to access.",
    ],
    "Other": [
        "The campus area feels calm and usable this morning.",
        "The space is generally comfortable with minor disruption.",
        "The area is pleasant and easy to move through.",
    ],
}


def _clamp(value: int) -> int:
    return max(1, min(5, value))


def _category_weights(locations: tuple[str, ...], category: str, location: str) -> int:
    """Create repeatable location/category patterns without hard-coding zones."""
    location_index = locations.index(location)
    category_index = CATEGORIES.index(category)
    return 5 if (location_index + category_index * 2) % 7 in (0, 1) else 1


def generate_demo_observations(
    *,
    seed: int = SEED,
    days: int = DEFAULT_DAYS,
    observations_per_day: int = OBSERVATIONS_PER_DAY,
    start: datetime | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic, schema-shaped synthetic observations.

    The default range is the 90 complete UTC days ending on 2026-09-23. Each
    day has observations at varied academic-day hours, with a few marked
    location-day spikes to make existing anomaly and clustering views useful.
    """
    if days < 1 or observations_per_day < 1:
        raise ValueError("days and observations_per_day must be positive")
    locations = tuple(get_locations())
    if not locations:
        raise ValueError("At least one configured location is required")
    rng = random.Random(seed)
    start = start or datetime(2026, 9, 23, 8, tzinfo=timezone.utc) - timedelta(days=days - 1)
    start = start.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows: list[dict[str, Any]] = []

    for day_index in range(days):
        day = start + timedelta(days=day_index)
        weekday_factor = 1 if day.weekday() < 5 else -1
        for sample_index in range(observations_per_day):
            location = locations[(day_index * 3 + sample_index + rng.randrange(len(locations))) % len(locations)]
            eligible = [
                category for category in CATEGORIES
                for _ in range(_category_weights(locations, category, location))
            ]
            category = rng.choice(eligible)
            base_severity, base_crowd, base_environment = _CATEGORY_BASE[category]
            hour = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20][sample_index]
            if category in {"Crowding", "Noise"}:
                hour += rng.choice([-1, 0, 0, 1])
            observed_at = day + timedelta(hours=hour, minutes=rng.randrange(0, 60))
            crowd = _clamp(base_crowd + (1 if 11 <= hour <= 14 else 0) + weekday_factor + rng.choice([-1, 0, 0, 1]))
            severity = _clamp(base_severity + (1 if crowd >= 5 else 0) + rng.choice([-1, 0, 0, 1]))
            environment = _clamp(base_environment - (1 if severity >= 5 else 0) + rng.choice([-1, 0, 0, 1]))

            # Two deliberate but plausible location-day spikes, not real findings.
            if day_index in {days // 3, (days * 2) // 3} and sample_index < 2:
                severity, crowd, environment = 5, 5, 1
                category = "Noise" if sample_index == 0 else "Crowding"

            description = rng.choice(_DESCRIPTIONS[category])
            rows.append({
                "created_at": (observed_at + timedelta(minutes=5)).isoformat(),
                "location": location,
                "category": category,
                "severity": severity,
                "description": description,
                "observed_at": observed_at.isoformat(),
                "approximate_location_id": f"{DEMO_MARKER}{day_index:03d}-{sample_index:02d}",
                "crowd_level": crowd,
                "environmental_rating": environment,
            })
    return rows


def reset_demo_data(connection) -> int:
    """Delete only rows carrying this generator's reserved marker."""
    cursor = connection.execute(
        "DELETE FROM observations WHERE approximate_location_id LIKE ?",
        (f"{DEMO_MARKER}%",),
    )
    connection.commit()
    return int(cursor.rowcount)


def insert_demo_data(connection, rows: list[dict[str, Any]]) -> int:
    connection.executemany(
        """
        INSERT INTO observations (
            created_at, location, category, severity, description, observed_at,
            approximate_location_id, crowd_level, environmental_rating
        ) VALUES (:created_at, :location, :category, :severity, :description,
                  :observed_at, :approximate_location_id, :crowd_level,
                  :environmental_rating)
        """,
        rows,
    )
    connection.commit()
    return len(rows)


def seed_database(*, clear_demo: bool = False, seed: int = SEED) -> tuple[int, int]:
    """Initialize the configured database and insert a fresh deterministic set."""
    init_db()
    rows = generate_demo_observations(seed=seed)
    with get_connection() as connection:
        removed = reset_demo_data(connection) if clear_demo else 0
        inserted = insert_demo_data(connection, rows)
    return inserted, removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic CampusPulse demo observations.")
    parser.add_argument("--clear-demo", action="store_true", help="Remove only rows marked by this generator first.")
    parser.add_argument("--seed", type=int, default=SEED, help=f"Random seed (default: {SEED}).")
    args = parser.parse_args()
    inserted, removed = seed_database(clear_demo=args.clear_demo, seed=args.seed)
    print(f"Inserted {inserted} synthetic demo observations (seed={args.seed}).")
    if args.clear_demo:
        print(f"Removed {removed} previous rows marked with {DEMO_MARKER!r}.")
    print("Synthetic data only; do not interpret it as a real campus finding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
