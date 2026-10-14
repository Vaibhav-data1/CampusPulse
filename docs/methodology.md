# Methodology for CampusPulse

## 1. Problem Definition

CampusPulse addresses a common challenge in campus operations and student experience analysis: environmental conditions are often described in fragmented, unstructured, or inconsistent ways, making it difficult to understand where, when, and under what circumstances recurring patterns emerge. Conventional reporting often captures individual accounts, but it does not necessarily provide a structured analytical view of recurring environmental conditions across the campus footprint.

The project is therefore not designed as a generic complaint portal. Instead, it frames anonymous observations as a dataset for analytical discovery. The system aims to support interpretation of:

- where observation patterns cluster,
- when they occur across time,
- which categories dominate across the campus,
- which aggregated observation patterns are unusual relative to the observed history,
- what people describe in free-text observation entries,
- whether similar observations naturally group together,
- whether measurable variables exhibit statistical association.

This perspective treats observations as evidence for environment intelligence rather than as isolated complaints. The result is a system that emphasizes explainability, privacy, and reproducible analysis over prediction or individualized tracking.

## 2. Objectives

The verified implementation of CampusPulse has the following project objectives:

- collect anonymous, structured campus-environment observations,
- analyze temporal patterns in observation activity,
- analyze spatial patterns across predefined campus zones,
- identify unusual location-day patterns using an unsupervised anomaly detector,
- extract sentiment, topics, and keywords from free-text descriptions,
- discover natural groupings in aggregated observation patterns,
- identify statistical relationships among numeric variables,
- surface results through an interpretable dashboard,
- maintain privacy-safe, deterministic, and reproducible analysis.

Prediction is not a current project objective. The current system performs descriptive and exploratory analytical tasks rather than forecasting future campus conditions.

## 3. Proposed System

CampusPulse is implemented as a privacy-safe, data-driven campus environment intelligence system with a simple analytical stack:

- a React + TypeScript + Vite frontend for submission and dashboard visualization,
- a FastAPI backend for API exposure and request validation,
- a SQLite database for persistent structured observation storage,
- a pandas-based analytics layer for summary and temporal analysis,
- scikit-learn unsupervised methods for anomaly detection and clustering,
- lexical NLP for sentiment/topic/keyword summarization.

The system intentionally works with aggregate, explainable observations. It does not use individual user tracking, GPS, or personal identity data. The frontend and backend are separated, and each analytics endpoint reads the current observation dataset and returns machine-readable results to the dashboard.

## 4. Data Collection

CampusPulse collects anonymous observations through a structured observation form. The backend validates the submitted payload and stores it in the `observations` table. The implemented observation model contains both structured metadata and free-text description.

### Structured metadata

The actual implementation records the following fields:

- `category`: a controlled campus category such as Wi-Fi / Connectivity, Crowding, Cleanliness, Noise, Maintenance, Safety, Facilities, or Other.
- `severity`: integer in the range 1–5.
- `description`: free-text observation content.
- `location`: configured campus zone or area label.
- `observed_at`: optional timestamp for when the observation occurred.
- `approximate_location_id`: optional human-readable approximate sub-area label.
- `crowd_level`: optional integer in the range 1–5.
- `environmental_rating`: optional integer in the range 1–5.
- `created_at`: server-created timestamp for database insertion.

The system distinguishes between:

- structured metadata: location, category, severity, crowd level, environmental rating, timestamps,
- free-text description: narrative explanation of the observed condition.

The categories and locations are controlled through the backend configuration, which avoids arbitrary free-form values and keeps dashboard and analysis outputs consistent.

## 5. Data Structure

The backend storage schema is implemented in `app/backend/app/database.py` and uses a single SQLite table named `observations`.

Each observation row includes:

- a numeric primary key (`id`),
- a creation timestamp (`created_at`),
- a controlled `location`,
- a controlled `category`,
- a severity score (`severity`),
- a free-text `description`,
- an optional `observed_at`,
- an optional `approximate_location_id`,
- an optional `crowd_level`,
- an optional `environmental_rating`.

This structure supports both descriptive analytics and higher-level pattern mining. The schema is intentionally minimal and avoids user identity data, contact metadata, or GPS fields.

## 6. Data Validation and Preprocessing

The system implements validation at both API and database levels.

### Schema and range validation

The backend enforces the following checks:

- `severity` must be an integer between 1 and 5,
- `crowd_level` is optional but, when present, must be between 1 and 5,
- `environmental_rating` is optional but, when present, must be between 1 and 5,
- `location` and `category` are controlled values from the configured lists,
- `description` must be non-empty, which is enforced through the API request model and validation flow,
- timestamps are stored in ISO 8601 strings and interpreted as UTC-aware values where appropriate.

### Timestamp handling

The analytics layer uses pandas `to_datetime(..., utc=True)` to normalize observation times. Naive timestamps are treated as UTC by the implemented logic, which preserves consistency and prevents crashes from mixed timezone-aware and naive inputs. This is an essential requirement for temporal analytics and avoids inconsistent grouping across dates and hours.

### Nullable and optional field handling

Optional fields are not globally dropped from the dataset. Instead, the implementation handles nulls only for the metric being calculated. This is a deliberate design choice to prevent the entire dataset from being discarded when one optional field is missing for a subset of rows. For example, crowd and environmental ratings are used when available and omitted from calculations when not present.

### Text preprocessing

The NLP module applies a rule-based preprocessing pipeline: descriptions are lowercased, normalized, tokenized, and filtered to remove punctuation, numbers, and stop words. The process is deterministic and fully local; no external model service is involved. Empty or tokenless descriptions are safely ignored for NLP analysis.

### Invalid or incomplete data handling

The implementation is careful to avoid silent failure in major analytical steps:

- if required columns are absent, the relevant function raises a clear validation error,
- empty data returns explicit empty or insufficient-data states,
- incomplete timestamp data is filtered out only for time-sensitive calculations,
- null optional metrics are ignored only where those metrics are being evaluated,
- the anomaly detector and clustering logic require minimum-group thresholds before producing results.

This ensures that the system does not misrepresent insufficient or invalid observation histories as stable analytical results.

## 7. Exploratory Data Analysis

The backend summary endpoint provides the first layer of analysis. It aggregates raw observation rows into explainable metrics that support downstream exploration.

The implemented EDA includes:

- total observation count,
- category distribution,
- location distribution,
- mean severity by category,
- mean severity by location,
- mean crowd level by location,
- mean environmental rating by location,
- hourly observation patterns,
- daily and weekly trend counts,
- location-category hotspot rankings.

This stage is important because it provides a baseline understanding of the data before more advanced modules are applied. If the data distribution is sparse or skewed, later steps such as anomaly detection, clustering, or relationship analysis can logically fail or return insufficient-data states rather than misleadingly confident outcomes.

## 8. Temporal Analysis

The analytics layer calculates temporal observation patterns from the `observed_at` field when valid timestamps are available.

### Hourly patterns

The summary computes observation counts by hour of day across the valid timestamped dataset. This reveals recurring activity windows, such as concentration during certain periods of the day.

### Daily and weekly trends

For valid timestamps, the system aggregates counts by calendar day and by weekly periods. These summaries are exposed as daily and weekly trend data and support interpretation of recurring temporal variability.

### Interpretation

Temporal aggregation helps identify when observations are concentrated and whether certain time windows consistently record higher intensity. The implementation does not claim seasonality or forecasting; it reports patterns observed in the dataset and uses them as exploratory evidence.

## 9. Spatial Analysis

CampusPulse uses predefined campus zones, not live GPS observation. The system is intentionally based on controlled `location` values and abstract zone-level aggregation.

### Zone-level aggregation

The spatial analysis module builds a deterministic abstract layout from configured locations and computes zone metrics for each configured area. It includes:

- `zone_id`
- `display_name`
- abstract `layout` coordinates
- observation count
- average severity
- high-severity count
- optional average crowd level
- optional average environmental rating
- dominant category
- category distribution
- anomaly count
- an abstract intensity score from 0 to 100.

### Intensity methodology

The actual implementation calculates intensity as a weighted mean scaled to the 0–100 range. For each populated zone:

- 40% of the score comes from observation frequency relative to the busiest included zone,
- 40% comes from average severity divided by 5,
- 10% comes from average crowd level divided by 5 when available,
- 10% comes from environmental concern, computed as `1 - average_environmental_rating / 5`, when available.

The implementation uses the weighted expression:

`intensity = 100 * (sum(weight * value) / total_weight)`

where `value` is the normalized component and `weight` is the corresponding component weight. If optional metrics are missing, their weights are redistributed across the available components. This yields a explainable, deterministic indicator of observed intensity rather than a prediction score.

### Heatmap and comparison

The dashboard renders an abstract campus-zone heatmap with zone tiles whose color intensity reflects the computed score. Users can filter by category and inspect zone-level details. The output is designed for comparison across predefined areas and is intentionally not a map of individual movement.

### Privacy and design limitations

CampusPulse does not use:

- GPS,
- individual movement tracking,
- exact personal position telemetry,
- precise geolocation.

This design preserves privacy and aligns with the project goal of analyzing environment conditions at zone level rather than identifying or monitoring people.

## 10. Anomaly Detection

The anomaly detection module is implemented in `app/ml/anomaly.py` and uses the scikit-learn `IsolationForest` model.

### Data preparation

The model aggregates observations by `location` and UTC calendar day (`period_start`). Each group becomes a single row containing:

- `observation_count`,
- `average_severity`,
- `average_crowd_level`,
- `average_environmental_rating`,
- `dominant_category` where available.

Descriptions are not used as model features for this stage. The detector focuses on aggregate pattern intensity, rather than raw text, to avoid treating language content as the primary source of anomaly detection.

### Model behavior

Isolation Forest is an unsupervised anomaly-detection method that isolates unusual combinations in feature space using random partitioning. Observations that are structurally different from the rest of the history are marked as anomalous. The implementation uses a deterministic random state and returns both the anomaly score and a human-readable explanation.

### Output

For each anomalous location-day group, the output includes:

- the affected location,
- the date (`period_start`),
- the dominant category,
- observation count,
- average severity,
- average crowd and environmental context when present,
- anomaly score,
- explanation string.

The message is deliberately phrased as: "Unusual compared with observed location-day patterns" rather than as a direct claim that a location is a problem. This aligns with the project’s analytical rather than punitive framing.

### Minimum-data safeguard

The implementation requires at least five valid location-day groups before anomaly detection is attempted. For smaller datasets, the endpoint returns an `insufficient_data` state instead of silently classifying everything as unusual. This protects the system from misleading conclusions that arise when the observed history is too sparse.

## 11. Natural Language Processing

The NLP module is implemented in `app/ml/nlp.py` and uses a structured lexical approach built from the repository’s own vocabulary rules.

### Preprocessing

Descriptions are normalized to lowercase and tokenized with a regex-based tokenizer. Common stop words are removed, along with numeric strings. The original description is preserved in the database; only the analysis representation is transformed.

### Sentiment analysis

The implementation calculates a lexical sentiment score using domain-specific positive and negative word sets. The score is:

`(positive token count - negative token count) / token count`

This yields a `Positive`, `Negative`, or `Neutral` label. The result is an approximate indicator, not a deep semantic understanding of the text.

### Topic detection

Topic detection is based on keyword dictionaries related to categories such as:

- Wi-Fi / Connectivity,
- Crowding,
- Cleanliness,
- Noise,
- Maintenance,
- Safety,
- Facilities,
- Temperature / Heat,
- Water,
- Electricity,
- Seating,
- Infrastructure.

The system identifies which topics are present in each observation description and aggregates counts across descriptions.

### Keyword extraction

The NLP module counts the most frequent meaningful tokens after stop-word filtering. This provides a transparent view of the vocabulary most often used in the observed descriptions.

### Limitations

The system is not an LLM, not a transformer-based model, and not a deep-learning system. It is a local lexical analysis method designed for explainability and reproducibility. It does not interpret sarcasm, complex negation, or context-dependent meaning in the way a more advanced language model would.

## 12. Pattern Discovery / Clustering

Unsupervised clustering is implemented in `app/ml/clustering.py` and applied to aggregated location-day observations.

### Feature profile

The grouping uses aggregated numeric features such as:

- observation count,
- average severity,
- average crowd level when available,
- average environmental rating when available.

### Method

The implementation uses KMeans clustering over the aggregated feature matrix. It evaluates a bounded range of cluster counts and selects the best value using the silhouette score. This avoids forcing a cluster count when the dataset is too sparse or contains too little distinct variation to justify a larger number of clusters.

### Output

Each cluster summary includes:

- cluster ID,
- observation count,
- percentage of total groups,
- feature profile,
- dominant category,
- dominant location,
- human-readable summary.

The output is designed to surface recurring patterns that may be structurally similar, even when they are not identical.

## 13. Relationship Analysis

The relationship analysis module is implemented in `app/ml/relationships.py` and uses Spearman’s rank correlation coefficient.

### Variables considered

The numeric variables evaluated include:

- `severity`,
- `crowd_level`,
- `environmental_rating`,
- `sentiment_score` when available.

### Why Spearman?

Spearman is used because it measures monotonic relationships without requiring a linear relationship among the variables. This is appropriate for ordinal and semi-ordinal variables such as severity scores and crowd ratings.

### Interpretation

The output includes both the coefficient and a qualitative interpretation such as `weak`, `moderate`, `strong`, or `very strong`. The implementation makes clear that these are statistical associations and not causal claims.

### Important caveat

Correlation does not imply causation. The relationship analysis tells us whether measurable variables tend to move together in a monotonic pattern; it does not establish that one factor caused another.

## 14. Data Sufficiency

The project explicitly handles insufficient or sparse data rather than silently producing misleading outputs. Several modules include minimum-data conditions:

- anomaly detection requires at least five valid location-day groups,
- clustering requires enough distinct groups to support meaningful clustering,
- NLP sentiment trend analysis requires a minimum number of dated descriptions,
- relationship analysis requires a minimum number of numeric rows before computing correlations.

When the dataset is too sparse, the API returns an `insufficient_data` or empty state rather than inventing a result. This improves analytical honesty and avoids false confidence.

## 15. Visualization

The dashboard is built in React and consumes the backend analytics endpoints. It presents the results in a human-readable form with the following major sections:

- overview metrics,
- category and location distributions,
- temporal charts and trends,
- spatial heatmap over predefined campus zones,
- anomaly panel,
- NLP sentiment and topic summaries,
- clustering summaries,
- relationship summaries.

The UI is designed to communicate data-driven intelligence rather than a generic issue tracker. Each section includes loading, empty, and error states where appropriate, and the dashboard clearly distinguishes analytical outputs from any claim of a real campus condition.

## 16. Privacy and Ethical Considerations

CampusPulse is implemented as a privacy-safe analytics system. It does not include account management or user identity tracking. The system intentionally avoids collecting:

- names,
- student IDs,
- emails,
- phone numbers,
- GPS coordinates,
- user accounts,
- individual movement tracking,
- external submission of text to a third-party service.

Observations are anonymous at the system design level. The project also includes a privacy warning in the frontend that instructs users not to include personal identifiers in their descriptions. This is consistent with the system’s goal of generating campus-level intelligence without exposing individuals.

## 17. Limitations

The current implementation has important limitations that should be acknowledged:

- It is not a causal inference framework.
- It does not predict future campus behavior.
- It does not use GPS or precise movement data.
- NLP is lexical and explainable rather than fully semantic.
- Spatial analysis is zone-level and approximate rather than geographically exact.
- The system depends on the quality and coverage of observation data.
- Some metrics may be unavailable when the dataset is too sparse or when certain optional fields are absent.

These limitations are important because they define the appropriate interpretation of the dashboard outputs: they are analytical summaries of observed data, not definitive judgments about individual behavior or campus conditions.

## 18. Reproducibility

CampusPulse includes a deterministic synthetic demo dataset for development and demonstration. The current generator creates 1,080 observations across 90 UTC days from 2026-06-26 to 2026-09-23 using a fixed seed, `20260924`.

This dataset is documented as synthetic demonstration data and is not presented as real campus information. Its role is to validate that the full system can process representative variation across locations, categories, timestamps, severity, crowd, environmental rating, and text descriptions.

The demo data generator is separated from production observation logic and is intended for local demonstration rather than deployment as a production API feature. The generator uses a reserved `demo-seed-v1:` marker in `approximate_location_id` for safe targeted clearing of synthetic rows without deleting real observations.

## 19. Overall Analytical Pipeline

The end-to-end pipeline implemented in the project is as follows:

1. Anonymous observations are submitted through the frontend form.
2. The backend validates the payload against controlled categories, ranges, and optional fields.
3. Valid observations are stored in SQLite.
4. The analytics layer loads the current observation table into pandas DataFrames.
5. Summary statistics are computed for total counts, category/location distributions, and temporal patterns.
6. Spatial analysis aggregates outcomes by predefined campus zones and computes intensity scores.
7. Anomaly detection groups observations by location and UTC day and applies Isolation Forest to identify unusual patterns.
8. NLP analysis tokenizes descriptions and derives sentiment, topics, and keyword summaries.
9. Clustering groups similar aggregated observation profiles using KMeans to reveal naturally occurring pattern clusters.
10. Relationship analysis measures monotonic statistical associations among numeric variables using Spearman correlation.
11. These outputs are returned to the frontend through REST endpoints and rendered in the dashboard.

This pipeline is explainable, privacy-safe, and reproducible. It supports descriptive campus-environment intelligence without introducing individual tracking or fabricated analytical conclusions.
