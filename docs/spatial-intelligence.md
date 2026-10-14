# CampusPulse spatial intelligence

Spatial intelligence in CampusPulse means comparing **predefined campus zones**,
not tracking people or plotting precise movement. The existing controlled
`location` field is the zone identity. `approximate_location_id` remains an
optional human-readable sub-area label and is not used as a coordinate.

## API

`GET /api/v1/analytics/spatial` returns every configured zone, including zones
with zero observations. Pass `?category=Noise` to calculate the same view for a
single controlled category.

Each zone includes:

- `zone_id`, `display_name`, and abstract `layout` row/column positions
- observation count, average severity, high-severity count
- optional crowd and environmental averages
- dominant category and category distribution
- anomaly count when the anomaly detector has enough location-day history
- deterministic `intensity` from 0 to 100

The layout is an abstract campus arrangement. It is deliberately not a map and
does not imply geographic distance.

## Intensity methodology

For zones with observations, intensity is a weighted mean scaled to 0–100:

`40% frequency + 40% average severity + 10% average crowd + 10% environmental concern`

Frequency is the zone count divided by the busiest included zone. Severity and
crowd are divided by 5. Environmental concern is `1 - average rating / 5`, so
a lower environmental rating contributes more concern. If optional values are
missing, their weights are proportionally redistributed across available
components. This is an explainable indicator of observed activity, not a
prediction or causal score.

## Privacy and limitations

All results are zone-level aggregates. No GPS, accounts, names, IDs, contact
information, or individual movement tracking is introduced. Small samples can
make rankings unstable, zero-observation zones are not evidence of safety, and
unexpected database locations are retained as clearly labeled non-configured
zones rather than silently discarded. The dashboard labels the visualization
as an abstract campus-zone heatmap and exposes the underlying metrics on click.
