import { FormEvent, useEffect, useMemo, useState } from "react";
import { AnalyticsSummary, AnomalyResults, fetchAnalytics, fetchAnomalies, fetchClusters, fetchMetadata, fetchNlp, fetchRelationships, fetchSpatial, ClusterResults, Metadata, NlpResults, ObservationPayload, RelationshipResults, SpatialResults, submitObservation } from "./api";

const emptyForm: ObservationPayload = { location: "", category: "", severity: 3, description: "" };
const numberOptions = [1, 2, 3, 4, 5];

function SectionTitle({ eyebrow, title, detail }: { eyebrow: string; title: string; detail?: string }) {
  return <div className="section-heading"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2>{detail && <p>{detail}</p>}</div>;
}

function SectionIntro({ eyebrow, title, detail }: { eyebrow: string; title: string; detail: string }) {
  return <div className="section-intro"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2><p>{detail}</p></div>;
}

function MetricTable({ rows, labelKey, valueKey, valueSuffix = "" }: { rows: Record<string, string | number>[]; labelKey: string; valueKey: string; valueSuffix?: string }) {
  if (!rows.length) return <p className="empty">No observations yet for this metric.</p>;
  const max = Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  return <div className="metric-list">{rows.map((row, index) => <div className="metric-row" key={`${String(row[labelKey])}-${index}`}><div className="metric-label"><span>{String(row[labelKey])}</span><strong>{Number(row[valueKey]).toFixed(valueSuffix ? 1 : 0)}{valueSuffix}</strong></div><div className="bar-track"><span style={{ width: `${Math.max(4, (Number(row[valueKey]) / max) * 100)}%` }} /></div></div>)}</div>;
}

function AnomalyPanel({ results }: { results: AnomalyResults | null }) {
  if (!results) return <div className="card anomaly-card loading" role="status">Loading anomaly signals…</div>;
  if (results.status === "insufficient_data") {
    return <div className="card anomaly-card"><div className="anomaly-heading"><div><p className="eyebrow">Pattern watch</p><h3>Unusual activity</h3></div><span className="anomaly-count">—</span></div><p className="empty">{results.message}</p><p className="anomaly-note">Anomalies will appear after enough location-day patterns have been recorded.</p></div>;
  }
  return <div className="card anomaly-card wide" aria-labelledby="anomaly-title"><div className="anomaly-heading"><div><p className="eyebrow">What is unusual?</p><h3 id="anomaly-title">Anomaly detection</h3><p className="section-note">Identifies location-day patterns that differ substantially from typical observations.</p></div><span className="anomaly-count" aria-label={`${results.anomaly_count} unusual patterns`}>{results.anomaly_count}</span></div><p className="anomaly-note">An anomaly means unusual compared with observed patterns — not necessarily a problem.</p>{results.anomalies.length ? <div className="anomaly-list">{results.anomalies.map((anomaly) => <article className="anomaly-item" key={`${anomaly.location}-${anomaly.period_start}`}><div><strong>{anomaly.location}</strong><span>{anomaly.period_start}{anomaly.dominant_category ? ` · ${anomaly.dominant_category}` : ""}</span></div><p>{anomaly.explanation}</p></article>)}</div> : <p className="empty">No unusual location-day patterns detected.</p>}</div>;
}

function SpatialPanel({ categories }: { categories: string[] }) {
  const [category, setCategory] = useState("");
  const [results, setResults] = useState<SpatialResults | null>(null);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setResults(null); setError(""); setSelectedZone(null);
    fetchSpatial(category || undefined).then(setResults).catch((reason: Error) => setError(reason.message));
  }, [category]);

  const selected = results?.zones.find((zone) => zone.zone_id === selectedZone) ?? null;
  return <section className="spatial-section" aria-labelledby="spatial-title">
    <div className="spatial-toolbar"><div><p className="eyebrow">Where is it happening?</p><h2 id="spatial-title">Spatial intelligence</h2><p className="spatial-description">Shows how observation intensity varies across predefined campus zones.</p></div><label>Filter category<select aria-label="Filter spatial intelligence by category" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></label></div>
    {error && <div className="notice error">{error}</div>}
    {!results && !error && <div className="card loading">Loading zone intelligence…</div>}
    {results && <><div className="spatial-layout"><div className="card zone-map" aria-label="Abstract campus zone heatmap"><div className="heatmap-legend" aria-label="Intensity legend"><span>Lower intensity</span><i className="legend-low" /><i className="legend-mid" /><i className="legend-high" /><span>Higher intensity</span></div><div className="zone-grid">{results.zones.map((zone) => <button className={`zone-tile ${selectedZone === zone.zone_id ? "selected" : ""}`} key={zone.zone_id} onClick={() => setSelectedZone(zone.zone_id)} style={{ background: `color-mix(in srgb, #16847d ${Math.max(8, zone.intensity)}%, white)` }} aria-label={`${zone.display_name}, intensity ${zone.intensity}, ${zone.observation_count} observations`}><strong>{zone.display_name}</strong><span>{zone.observation_count ? `${zone.intensity.toFixed(0)} intensity` : "No observations"}</span></button>)}</div></div><div className="card zone-detail">{selected ? <><p className="eyebrow">Selected zone</p><h3>{selected.display_name}</h3><div className="zone-score"><strong>{selected.intensity.toFixed(0)}</strong><span>intensity / 100</span></div><dl><div><dt>Observations</dt><dd>{selected.observation_count}</dd></div><div><dt>Average severity</dt><dd>{selected.average_severity === null ? "—" : `${selected.average_severity.toFixed(1)} / 5`}</dd></div><div><dt>High severity</dt><dd>{selected.high_severity_count}</dd></div><div><dt>Dominant category</dt><dd>{selected.dominant_category ?? "—"}</dd></div></dl><div className="category-breakdown">{selected.category_distribution.map((item) => <span key={item.category}>{item.category} · {item.observation_count}</span>)}</div></> : <p className="empty">Select a zone to inspect its observed pattern.</p>}</div></div><div className="spatial-insights card"><h3>Supported spatial insights</h3>{results.insights.length ? results.insights.map((insight) => <p key={insight}>{insight}</p>) : <p className="empty">Not enough data to generate a supported spatial insight.</p>}</div></>}
  </section>;
}

function NlpPanel({ categories }: { categories: string[] }) {
  const [category, setCategory] = useState("");
  const [results, setResults] = useState<NlpResults | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    setResults(null); setError("");
    fetchNlp(category || undefined).then(setResults).catch((reason: Error) => setError(reason.message));
  }, [category]);
  if (error) return <section className="nlp-section"><div className="notice error">{error}</div></section>;
  if (!results) return <section className="nlp-section"><div className="card loading">Loading NLP intelligence…</div></section>;
  if (results.status === "empty") return <section className="nlp-section"><div className="card"><p className="eyebrow">NLP intelligence</p><h2>What observations are saying</h2><p className="empty">{results.message}</p></div></section>;
  return <section className="nlp-section" aria-labelledby="nlp-title"><div className="nlp-heading"><div><p className="eyebrow">What are people saying?</p><h2 id="nlp-title">NLP intelligence</h2><p>Analyzes sentiment, themes, and keywords found in observation descriptions.</p></div><label>Filter category<select aria-label="Filter language analysis by category" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All categories</option>{categories.map((item) => <option key={item}>{item}</option>)}</select></label></div><div className="nlp-grid"><div className="card nlp-card"><h3>Sentiment distribution</h3><MetricTable rows={results.sentiment_distribution} labelKey="sentiment" valueKey="percentage" valueSuffix="%" /></div><div className="card nlp-card"><h3>Top inferred topics</h3><MetricTable rows={results.topic_distribution} labelKey="topic" valueKey="observation_count" /></div><div className="card nlp-card"><h3>Top keywords</h3><div className="keyword-cloud">{results.top_keywords.length ? results.top_keywords.map((row) => <span key={String(row.keyword)}>{String(row.keyword)} · {String(row.count)}</span>) : <p className="empty">No meaningful keywords found.</p>}</div></div><div className="card nlp-card"><h3>Sentiment by zone</h3>{results.sentiment_by_location.length ? <div className="sentiment-rows">{results.sentiment_by_location.map((row) => <div key={String(row.location)}><div className="metric-label"><span>{String(row.location)}</span><strong>{String(row.negative_percentage)}% negative</strong></div><div className="bar-track"><span className="negative-bar" style={{ width: `${Number(row.negative_percentage)}%` }} /></div></div>)}</div> : <p className="empty">No location-level text data.</p>}</div><div className="card nlp-card wide"><h3>Sentiment trend</h3>{results.trend_status === "insufficient_data" ? <p className="empty">Not enough data to perform this trend analysis reliably.</p> : results.trend_status === "no_data" ? <p className="empty">No dated descriptions are available.</p> : <MetricTable rows={results.sentiment_trend} labelKey="period_start" valueKey="negative_percentage" valueSuffix="% negative" />}</div></div><div className="nlp-insights card"><h3>Supported text insights</h3>{results.insights.length ? results.insights.map((insight) => <p key={insight}>{insight}</p>) : <p className="empty">Not enough text data for a supported insight.</p>}</div></section>;
}

function ClusterPanel({ results }: { results: ClusterResults | null }) {
  if (!results) return <div className="card loading">Loading clusters…</div>;
  if (results.status === "insufficient_data") return <div className="card"><p className="eyebrow">Pattern clusters</p><h3>Clustered patterns</h3><p className="empty">{results.message ?? "Not enough patterns to cluster."}</p></div>;
  if (!results.clusters.length) return <div className="card"><p className="eyebrow">Pattern clusters</p><h3>Clustered patterns</h3><p className="empty">No clusters detected.</p></div>;
  return <section className="card clusters-card" aria-labelledby="clusters-title"><p className="eyebrow">What hidden patterns exist?</p><h3 id="clusters-title">Pattern discovery</h3><p className="section-note">Groups observations with similar characteristics using unsupervised learning.</p><div className="cluster-list">{results.clusters.map((c) => <article key={String(c.cluster_id)} className="cluster-item"><div><strong>Cluster {String(c.cluster_id)}</strong><span>{c.observation_count} groups · {Math.round(c.percentage)}%</span></div><p>{c.human_summary}</p><div className="cluster-metrics"><span>Severity {c.feature_profile.average_severity === null ? '—' : c.feature_profile.average_severity.toFixed(1)}</span><span>Crowd {c.feature_profile.average_crowd_level === null ? '—' : c.feature_profile.average_crowd_level.toFixed(1)}</span><span>Env {c.feature_profile.average_environmental_rating === null ? '—' : c.feature_profile.average_environmental_rating.toFixed(1)}</span></div></article>)}</div></section>;
}

function RelationshipsPanel({ results }: { results: RelationshipResults | null }) {
  if (!results) return <div className="card loading">Loading relationships…</div>;
  if (results.status === "insufficient_data") return <div className="card"><p className="eyebrow">Relationships</p><h3>Feature relationships</h3><p className="empty">{results.message ?? "Not enough data to compute relationships."}</p></div>;
  if (!results.relationships.length) return <div className="card"><p className="eyebrow">Relationships</p><h3>Feature relationships</h3><p className="empty">No notable relationships found.</p></div>;
  return <section className="card relationships-card" aria-labelledby="relationships-title"><p className="eyebrow">What hidden patterns exist?</p><h3 id="relationships-title">Relationships</h3><p className="section-note">Shows statistical associations between numerical variables; correlation does not imply causation.</p><ul>{results.relationships.map((r) => <li key={`${r.a}-${r.b}`}>{r.a} ↔ {r.b}: <strong>{r.spearman_r === null ? "—" : r.spearman_r.toFixed(2)}</strong> ({r.interpretation})</li>)}</ul></section>;
  }

function App() {
  const [page, setPage] = useState<"submit" | "dashboard">("submit");
  const [metadata, setMetadata] = useState<Metadata>({ categories: [], locations: [] });
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyResults | null>(null);
  const [clusters, setClusters] = useState<ClusterResults | null>(null);
  const [relationships, setRelationships] = useState<RelationshipResults | null>(null);
  const [form, setForm] = useState<ObservationPayload>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [dashboardError, setDashboardError] = useState("");

  useEffect(() => { fetchMetadata().then(setMetadata).catch((error: Error) => setMessage({ kind: "error", text: error.message })).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (page !== "dashboard") return;
    setDashboardError("");
    fetchAnalytics().then(setAnalytics).catch((error: Error) => setDashboardError(error.message));
    fetchAnomalies().then(setAnomalies).catch((error: Error) => setDashboardError(error.message));
    fetchClusters().then(setClusters).catch((error: Error) => setDashboardError(error.message));
    fetchRelationships().then(setRelationships).catch((error: Error) => setDashboardError(error.message));
  }, [page]);

  const update = (key: keyof ObservationPayload, value: string | number | undefined) => setForm((current) => ({ ...current, [key]: value }));
  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault(); setMessage(null);
    try {
      await submitObservation({ ...form, observed_at: form.observed_at || undefined, approximate_location_id: form.approximate_location_id || undefined });
      setForm(emptyForm); setMessage({ kind: "success", text: "Observation submitted. Thank you for helping us understand campus conditions." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "Unable to submit observation." }); }
  };
  const daily = useMemo(() => analytics?.daily_weekly_trends.filter((row) => row.period_type === "daily") ?? [], [analytics]);
  const weekly = useMemo(() => analytics?.daily_weekly_trends.filter((row) => row.period_type === "weekly") ?? [], [analytics]);
  const activeZones = analytics?.by_location.length ?? 0;
  const activeCategories = analytics?.by_category.length ?? 0;
  const averageSeverity = useMemo(() => {
    if (!analytics?.average_severity_by_category.length) return null;
    const values = analytics.average_severity_by_category.map((row) => Number(row.average_severity)).filter(Number.isFinite);
    return values.length ? values.reduce((total, value) => total + value, 0) / values.length : null;
  }, [analytics]);
  const dominantCategory = analytics?.by_category[0]?.category;
  const topZone = analytics?.by_location[0]?.location;

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage("submit"); }}><span className="brand-mark">CP</span><span>Campus<span>Pulse</span><small>environment intelligence</small></span></a><nav aria-label="Primary navigation"><button className={page === "submit" ? "active" : ""} onClick={() => setPage("submit")}>Submit observation</button><button className={page === "dashboard" ? "active" : ""} onClick={() => setPage("dashboard")}>Analytics dashboard</button></nav></header>
    <main>{page === "submit" ? <section className="hero-grid"><div className="intro"><p className="eyebrow">Make campus visible</p><h1>Small signals.<br /><em>Better environments.</em></h1><p className="lead">Share what you notice around campus. Your anonymous observations help reveal patterns in comfort, access, safety, and everyday campus life.</p><div className="principle"><span>01</span><p><strong>Data, not complaints.</strong><br />Every observation contributes to a clearer picture of the campus environment.</p></div></div><form className="card observation-form" onSubmit={handleSubmit}><SectionTitle eyebrow="New observation" title="What are you noticing?" detail="Required fields are marked with an asterisk." />{message && <div className={`notice ${message.kind}`} role="status">{message.text}</div>}<div className="form-grid"><label>Location *<select required value={form.location} onChange={(event) => update("location", event.target.value)}><option value="">Select an area</option>{metadata.locations.map((location) => <option key={location}>{location}</option>)}</select></label><label>Category *<select required value={form.category} onChange={(event) => update("category", event.target.value)}><option value="">Select a category</option>{metadata.categories.map((category) => <option key={category}>{category}</option>)}</select></label><label>Severity *<select required value={form.severity} onChange={(event) => update("severity", Number(event.target.value))}>{numberOptions.map((value) => <option key={value} value={value}>{value} — {["minimal", "low", "moderate", "high", "critical"][value - 1]}</option>)}</select></label><label>Observed at<input type="datetime-local" value={form.observed_at ?? ""} onChange={(event) => update("observed_at", event.target.value ? new Date(event.target.value).toISOString() : undefined)} /></label><label>Approximate area ID <input maxLength={100} placeholder="e.g. library-west-wing" value={form.approximate_location_id ?? ""} onChange={(event) => update("approximate_location_id", event.target.value)} /></label><label>Crowd level <select value={form.crowd_level ?? ""} onChange={(event) => update("crowd_level", event.target.value ? Number(event.target.value) : undefined)}><option value="">Not observed</option>{numberOptions.map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label>Environmental rating <select value={form.environmental_rating ?? ""} onChange={(event) => update("environmental_rating", event.target.value ? Number(event.target.value) : undefined)}><option value="">Not observed</option>{numberOptions.map((value) => <option key={value} value={value}>{value}</option>)}</select></label></div><label>Description *<textarea required minLength={1} maxLength={2000} rows={4} placeholder="Describe the environmental condition, not a person..." value={form.description} onChange={(event) => update("description", event.target.value)} /></label><div className="privacy"><strong>Privacy first</strong><span>Anonymous observations use predefined, approximate campus zones. Do not include names, IDs, phone numbers, emails, medical information, GPS details, or other personal identifiers. CampusPulse does not track individuals.</span></div><button className="primary-button" disabled={loading}>{loading ? "Loading form..." : "Submit anonymous observation"} <span>→</span></button></form></section> : <section className="dashboard"><div className="dashboard-heading"><div><p className="eyebrow">CampusPulse · Data-driven campus environment intelligence</p><h1>Environment intelligence dashboard</h1><p>Move from what is happening, to where it is happening, to unusual patterns and deeper signals.</p></div><span className="demo-badge">Development demo · synthetic data</span></div>{dashboardError && <div className="notice error" role="alert">{dashboardError}</div>}{!analytics && !dashboardError && <div className="card loading" role="status">Loading campus intelligence…</div>}{analytics && <><section className="overview-section" aria-labelledby="overview-title"><SectionIntro eyebrow="Overview · What is happening?" title="Campus pulse at a glance" detail="A factual snapshot of the observations currently available to the dashboard." /><div className="summary-grid"><div className="summary-stat"><span>Total observations</span><strong>{analytics.total_observations}</strong><small>anonymous signals recorded</small></div><div className="summary-stat"><span>Active zones</span><strong>{activeZones}</strong><small>predefined zones with data</small></div><div className="summary-stat"><span>Active categories</span><strong>{activeCategories}</strong><small>controlled categories represented</small></div><div className="summary-stat"><span>Average severity</span><strong>{averageSeverity === null ? "—" : averageSeverity.toFixed(1)}</strong><small>scale of 1–5</small></div><div className="summary-stat accent"><span>Unusual patterns</span><strong>{anomalies?.status === "ok" ? anomalies.anomaly_count : "—"}</strong><small>{anomalies?.status === "insufficient_data" ? "not enough data yet" : "location-day patterns"}</small></div></div><div className="insight-strip"><strong>Data signals</strong><span>{dominantCategory ? `Most represented category: ${String(dominantCategory)}.` : "Category distribution is not available."}</span><span>{topZone ? `Most represented zone: ${String(topZone)}.` : "Zone distribution is not available."}</span><span>These are synthetic demo patterns, not real campus findings.</span></div></section><section className="dashboard-section" aria-labelledby="trends-title"><SectionIntro eyebrow="Overview · Temporal patterns" title="Volume and trends" detail="Compare observation volume across categories, zones, times of day, and calendar periods." /><div className="dashboard-grid"><div className="card chart-card"><h3 id="trends-title">Observations by category</h3><MetricTable rows={analytics.by_category} labelKey="category" valueKey="observation_count" /></div><div className="card chart-card"><h3>Observations by location</h3><MetricTable rows={analytics.by_location} labelKey="location" valueKey="observation_count" /></div><div className="card chart-card"><h3>Average severity by category</h3><MetricTable rows={analytics.average_severity_by_category} labelKey="category" valueKey="average_severity" valueSuffix="/5" /></div><div className="card chart-card"><h3>Average severity by location</h3><MetricTable rows={analytics.average_severity_by_location} labelKey="location" valueKey="average_severity" valueSuffix="/5" /></div><div className="card chart-card"><h3>Average crowd level</h3><MetricTable rows={analytics.average_crowd_level} labelKey="location" valueKey="average_crowd_level" valueSuffix="/5" /></div><div className="card chart-card"><h3>Environmental rating</h3><MetricTable rows={analytics.average_environmental_rating} labelKey="location" valueKey="average_environmental_rating" valueSuffix="/5" /></div><div className="card chart-card wide"><h3>Time of day patterns</h3><MetricTable rows={analytics.time_of_day_patterns.filter((row) => Number(row.observation_count) > 0)} labelKey="hour_label" valueKey="observation_count" /></div><div className="card chart-card"><h3>Daily trends</h3><MetricTable rows={daily} labelKey="period_start" valueKey="observation_count" /></div><div className="card chart-card"><h3>Weekly trends</h3><MetricTable rows={weekly} labelKey="period_start" valueKey="observation_count" /></div><div className="card table-card wide"><h3>Location / category hotspots</h3>{analytics.location_category_hotspots.length ? <div className="table-scroll"><table><thead><tr><th>Location</th><th>Category</th><th>Observations</th><th>Severity</th><th>Score</th></tr></thead><tbody>{analytics.location_category_hotspots.map((row, index) => <tr key={index}><td>{String(row.location)}</td><td>{String(row.category)}</td><td>{String(row.observation_count)}</td><td>{Number(row.average_severity).toFixed(1)}</td><td>{Number(row.severity_score).toFixed(1)}</td></tr>)}</tbody></table></div> : <p className="empty">No observations available for hotspots.</p>}</div></div></section><SpatialPanel categories={metadata.categories} /><AnomalyPanel results={anomalies} /><NlpPanel categories={metadata.categories} /><ClusterPanel results={clusters} /><RelationshipsPanel results={relationships} /></>}</section>}</main><footer>CampusPulse · anonymous environmental observations · built for better shared spaces</footer>
  </div>;
}

export default App;
