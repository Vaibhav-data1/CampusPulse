# CampusPulse anomaly detection

CampusPulse anomaly detection highlights unusual **location-day** activity so
campus teams can investigate patterns that differ from the observations
collected so far. It is an intelligence aid, not a complaint classifier or a
claim that a location has a problem.

## Aggregation and features

The detector groups observations by their location and UTC calendar day. Each
group becomes one model row with:

- observation count
- average severity
- average crowd level
- average environmental rating

Descriptions are intentionally not used. When an optional crowd or
environmental value is missing, the detector uses the available group values
and median-imputes only the model input. Reported results retain `null` when no
value was observed.

## Method and interpretation

The model is scikit-learn's `IsolationForest`, an unsupervised method that
isolates unusual feature combinations using randomized trees. A result is an
anomaly when the model marks its aggregated pattern as unusual compared with
the other location-day groups in the supplied history. The result includes the
location, date, dominant category, aggregate context, and anomaly score.

“Unusual compared with observed patterns” does not mean “a problem.” A newly
opened event, an especially busy day, or incomplete reporting can all produce
anomalies.

## Data requirements and limitations

At least five valid location-day groups are required. With fewer groups, the
API returns `status: "insufficient_data"` and does not classify anything.
Observations without a valid location, observed timestamp, or severity cannot
form a group. Results depend on the history currently in SQLite, can change as
more observations arrive, and should be reviewed with local context. This
first feature does not predict future activity and does not analyze text.
