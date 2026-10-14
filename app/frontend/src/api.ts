export type Metadata = { categories: string[]; locations: string[] };
export type ObservationPayload = {
  location: string;
  category: string;
  severity: number;
  description: string;
  observed_at?: string;
  approximate_location_id?: string;
  crowd_level?: number;
  environmental_rating?: number;
};
export type MetricRow = Record<string, string | number>;
export type AnalyticsSummary = {
  total_observations: number;
  by_category: MetricRow[];
  by_location: MetricRow[];
  average_severity_by_category: MetricRow[];
  average_severity_by_location: MetricRow[];
  average_crowd_level: MetricRow[];
  average_environmental_rating: MetricRow[];
  time_of_day_patterns: MetricRow[];
  daily_weekly_trends: MetricRow[];
  location_category_hotspots: MetricRow[];
};
export type Anomaly = {
  location: string;
  period_start: string;
  dominant_category: string | null;
  observation_count: number;
  average_severity: number;
  average_crowd_level: number | null;
  average_environmental_rating: number | null;
  anomaly_score: number;
  explanation: string;
};
export type AnomalyResults = {
  status: "ok" | "insufficient_data";
  message: string;
  minimum_groups: number;
  group_count: number;
  anomaly_count: number;
  anomalies: Anomaly[];
};
export type SpatialZone = {
  zone_id: string;
  display_name: string;
  layout: { row: number; column: number };
  intensity: number;
  observation_count: number;
  average_severity: number | null;
  high_severity_count: number;
  average_crowd_level: number | null;
  average_environmental_rating: number | null;
  dominant_category: string | null;
  category_distribution: { category: string; observation_count: number }[];
  anomaly_count: number;
};
export type SpatialResults = {
  status: "ok" | "empty";
  category: string | null;
  zone_count: number;
  zones: SpatialZone[];
  insights: string[];
};
export type NlpResults = {
  status: "ok" | "empty";
  message: string;
  observation_count: number;
  sentiment_distribution: MetricRow[];
  sentiment_by_category: MetricRow[];
  sentiment_by_location: MetricRow[];
  topic_distribution: MetricRow[];
  topic_by_category: MetricRow[];
  topic_by_location: MetricRow[];
  top_keywords: MetricRow[];
  sentiment_trend: MetricRow[];
  trend_status: "ok" | "insufficient_data" | "no_data";
  insights: string[];
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const fetchMetadata = () => request<Metadata>("/api/v1/observations/metadata");
export const fetchAnalytics = () => request<AnalyticsSummary>("/api/v1/analytics/summary");
export const fetchAnomalies = () => request<AnomalyResults>("/api/v1/analytics/anomalies");
export type ClusterSummary = {
  cluster_id: number | string;
  observation_count: number;
  percentage: number;
  feature_profile: {
    average_severity: number | null;
    average_crowd_level: number | null;
    average_environmental_rating: number | null;
  };
  dominant_category: string | null;
  dominant_location: string | null;
  human_summary: string;
};
export type ClusterResults = {
  status: "ok" | "insufficient_data" | "empty";
  message?: string;
  group_count?: number;
  minimum_groups?: number;
  clusters: ClusterSummary[];
};
export const fetchClusters = () => request<ClusterResults>("/api/v1/analytics/clusters");
export type Relationship = {
  a: string;
  b: string;
  spearman_r: number | null;
  sample_size: number;
  interpretation: string;
};
export type RelationshipResults = {
  status: "ok" | "insufficient_data" | "empty";
  message?: string;
  relationships: Relationship[];
};
export const fetchRelationships = () => request<RelationshipResults>("/api/v1/analytics/relationships");
export const fetchSpatial = (category?: string) =>
  request<SpatialResults>(`/api/v1/analytics/spatial${category ? `?category=${encodeURIComponent(category)}` : ""}`);
export const fetchNlp = (category?: string) =>
  request<NlpResults>(`/api/v1/analytics/nlp${category ? `?category=${encodeURIComponent(category)}` : ""}`);
export const submitObservation = (payload: ObservationPayload) =>
  request("/api/v1/observations", { method: "POST", body: JSON.stringify(payload) });
