# CampusPulse analytics module

This module contains the first analytics layer for CampusPulse. It is intentionally separated from the FastAPI backend so that dashboard summaries, trend analysis, and future ML feature generation can evolve independently.

## What these metrics measure

- `counts_by_category`: number of observations in each category
- `counts_by_location`: number of observations reported in each campus area
- `average_severity_by_category`: mean impact severity for each category
- `average_severity_by_location`: mean impact severity for each campus area
- `average_crowd_level_by_location`: mean crowd intensity for each location
- `average_environmental_rating_by_location`: average perceived environmental quality per location
- `time_of_day_patterns`: how observation volume changes by hour of the day
- `daily_weekly_trends`: daily and weekly observation trends over time
- `location_category_hotspots`: combinations of location and category with the strongest count/severity signal
- `basic_data_quality_statistics`: overall dataset health, missing values, unique entries, and observation date range

## Why these metrics matter

These signals give CampusPulse a structured, privacy-safe, and explainable view of campus conditions. They help identify recurring environmental issues, areas with sustained pressure, time-based problem windows, and possible hotspot zones. This creates the foundation for future spatial analysis, anomaly detection, clustering, and predictive analytics.

## Future ML consumption

The outputs produced by this module are designed to feed future ML components without depending on the FastAPI layer. For example:

- hotspot rankings can be used as feature summaries for clustering and anomaly detection
- hourly and daily trends can support time-series forecasting
- categorical and spatial summaries can become model inputs for risk scoring
- data-quality reports can flag low-quality observations before ML processing

The module intentionally operates on ordinary pandas DataFrames so it can be reused in notebooks, scheduled jobs, dashboards, and later ML pipelines.
