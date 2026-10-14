# Reproducible demo data

CampusPulse includes a development-only generator for demonstrating the existing
dashboard and analytics pipeline without presenting synthetic observations as
real campus findings.

From the repository root, with the backend dependencies installed:

```bash
python scripts/seed_demo_data.py
python scripts/seed_demo_data.py --clear-demo
```

The default command inserts **1,080 observations**: 12 observations per day
over 90 UTC days, from **2026-06-26 through 2026-09-23**. The default fixed
seed is `20260924`. Use `--seed` to intentionally create a different
repeatable synthetic scenario. The database path is the normal
`CAMPUSPULSE_DATABASE_PATH` setting, so a temporary database can be selected
for a local demo.

The generator varies all configured locations and controlled categories,
weekday/weekend and academic-day timing, severity, crowd level,
environmental rating, and short descriptions. Location/category affinities
create spatial patterns; midday crowd/noise patterns create temporal
variation; and two small high-severity, low-environment spikes provide
plausible unusual location-day groups for the existing anomaly detector.
Descriptions are intentionally varied so the existing NLP topics, keywords,
and sentiment summaries have something to analyze.

The schema currently has no provenance column. To avoid deleting real
observations, generated rows carry the reserved non-personal marker
`demo-seed-v1:` in `approximate_location_id`. `--clear-demo` deletes only
rows beginning with that exact marker, then a fresh deterministic set can be
inserted. Do not use that prefix for manually submitted observations.

No names, IDs, email addresses, phone numbers, GPS coordinates, accounts, or
other personal information are generated. Every result produced from this
dataset is synthetic and must be labelled as such.
