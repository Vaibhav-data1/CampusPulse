from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable

import pandas as pd

STOP_WORDS = {
    "a", "an", "and", "are", "at", "be", "been", "but", "by", "can", "do",
    "for", "from", "has", "have", "in", "is", "it", "its", "of", "on", "or",
    "our", "that", "the", "their", "there", "this", "to", "was", "we", "were",
    "with", "very", "near", "not", "around", "area", "place", "campus",
}
POSITIVE_WORDS = {
    "clean", "comfortable", "excellent", "good", "helpful", "improved",
    "quiet", "safe", "smooth", "stable", "working", "pleasant", "cool",
}
NEGATIVE_WORDS = {
    "bad", "broken", "crowded", "dirty", "difficult", "disconnected",
    "disruption", "failing", "hot", "loud", "noise", "poor", "unsafe",
    "unavailable", "uncomfortable", "urgent", "waste", "worst",
}
TOPIC_KEYWORDS = {
    "Wi-Fi / Connectivity": {"wifi", "wi-fi", "internet", "network", "signal", "connectivity", "disconnected"},
    "Crowding": {"crowded", "crowding", "busy", "packed", "queue", "queues", "overcrowded"},
    "Cleanliness": {"clean", "cleanliness", "dirty", "dirt", "litter", "trash", "waste", "rubbish"},
    "Noise": {"noise", "noisy", "loud", "sound", "music", "construction", "quiet"},
    "Maintenance": {"broken", "repair", "repairs", "maintenance", "leak", "leaking", "working", "fix"},
    "Safety": {"safe", "safety", "unsafe", "danger", "dangerous", "security", "slippery"},
    "Facilities": {"facility", "facilities", "classroom", "building", "equipment", "room"},
    "Temperature / Heat": {"hot", "heat", "temperature", "fan", "fans", "cool", "cold"},
    "Water": {"water", "drinking", "tap", "taps", "leak", "leaking"},
    "Electricity": {"electricity", "power", "outage", "light", "lights", "socket", "sockets"},
    "Seating": {"seat", "seats", "seating", "chair", "chairs", "desk", "desks"},
    "Infrastructure": {"road", "path", "pavement", "infrastructure", "stairs", "lift", "elevator"},
}
TOKEN_PATTERN = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)


def preprocess_text(value: Any) -> list[str]:
    if value is None or pd.isna(value):
        return []
    text = re.sub(r"\s+", " ", str(value).lower()).strip()
    return [
        token for token in TOKEN_PATTERN.findall(text)
        if token not in STOP_WORDS and not token.isnumeric() and len(token) > 1
    ]


def sentiment_for_tokens(tokens: Iterable[str]) -> dict[str, Any]:
    tokens = list(tokens)
    positive = sum(token in POSITIVE_WORDS for token in tokens)
    negative = sum(token in NEGATIVE_WORDS for token in tokens)
    score = round((positive - negative) / max(len(tokens), 1), 3)
    label = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"
    return {"sentiment": label, "sentiment_score": score}


def topics_for_tokens(tokens: Iterable[str]) -> list[str]:
    token_set = set(tokens)
    return [
        topic for topic, keywords in TOPIC_KEYWORDS.items()
        if token_set.intersection(keywords)
    ]


def analyze_nlp(
    df: pd.DataFrame,
    minimum_trend_observations: int = 5,
) -> dict[str, Any]:
    if "description" not in df.columns:
        raise ValueError("Missing required columns: description")
    if df.empty:
        return {
            "status": "empty",
            "message": "No observation descriptions are available.",
            "observation_count": 0,
            "sentiment_distribution": [],
            "sentiment_by_category": [],
            "sentiment_by_location": [],
            "topic_distribution": [],
            "topic_by_category": [],
            "topic_by_location": [],
            "top_keywords": [],
            "sentiment_trend": [],
            "trend_status": "no_data",
            "insights": [],
        }

    working = df.copy()
    working["tokens"] = working["description"].map(preprocess_text)
    working["has_text"] = working["tokens"].map(bool)
    working = working[working["has_text"]].copy()
    if working.empty:
        return {
            "status": "empty",
            "message": "No non-empty observation descriptions are available.",
            "observation_count": 0,
            "sentiment_distribution": [],
            "sentiment_by_category": [],
            "sentiment_by_location": [],
            "topic_distribution": [],
            "topic_by_category": [],
            "topic_by_location": [],
            "top_keywords": [],
            "sentiment_trend": [],
            "trend_status": "no_data",
            "insights": [],
        }

    sentiment = working["tokens"].map(sentiment_for_tokens)
    working["sentiment"] = sentiment.map(lambda item: item["sentiment"])
    working["sentiment_score"] = sentiment.map(lambda item: item["sentiment_score"])
    working["topics"] = working["tokens"].map(topics_for_tokens)

    def distribution(series: pd.Series, name: str) -> list[dict[str, Any]]:
        counts = series.value_counts().rename_axis(name).reset_index(name="observation_count")
        counts["percentage"] = (counts["observation_count"] / len(series) * 100).round(1)
        return counts.to_dict("records")

    sentiment_distribution = distribution(working["sentiment"], "sentiment")
    topic_counts = Counter(topic for topics in working["topics"] for topic in topics)
    topic_distribution = [
        {"topic": topic, "observation_count": count,
         "percentage": round(count / len(working) * 100, 1)}
        for topic, count in sorted(topic_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    keyword_counts = Counter(token for tokens in working["tokens"] for token in tokens)
    top_keywords = [
        {"keyword": keyword, "count": count}
        for keyword, count in keyword_counts.most_common(10)
    ]

    def grouped_sentiment(column: str) -> list[dict[str, Any]]:
        if column not in working:
            return []
        rows = []
        for value, group in working.dropna(subset=[column]).groupby(column, sort=True):
            rows.append({
                column: str(value),
                "observation_count": len(group),
                "negative_percentage": round((group["sentiment"] == "Negative").mean() * 100, 1),
                "neutral_percentage": round((group["sentiment"] == "Neutral").mean() * 100, 1),
                "positive_percentage": round((group["sentiment"] == "Positive").mean() * 100, 1),
            })
        return rows

    def grouped_topics(column: str) -> list[dict[str, Any]]:
        if column not in working:
            return []
        counts: Counter[tuple[str, str]] = Counter()
        for _, row in working.dropna(subset=[column]).iterrows():
            for topic in row["topics"]:
                counts[(str(row[column]), topic)] += 1
        return [
            {column: group, "topic": topic, "observation_count": count}
            for (group, topic), count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    trend_status = "insufficient_data"
    trend: list[dict[str, Any]] = []
    if "observed_at" in working:
        timestamps = pd.to_datetime(working["observed_at"], errors="coerce", utc=True)
        dated = working.loc[timestamps.notna()].copy()
        dated["period_start"] = timestamps[timestamps.notna()].dt.strftime("%Y-%m-%d")
        if len(dated) >= minimum_trend_observations:
            trend = [
                {
                    "period_start": str(period),
                    "observation_count": len(group),
                    "negative_percentage": round((group["sentiment"] == "Negative").mean() * 100, 1),
                    "positive_percentage": round((group["sentiment"] == "Positive").mean() * 100, 1),
                    "average_sentiment_score": round(group["sentiment_score"].mean(), 3),
                }
                for period, group in dated.groupby("period_start", sort=True)
            ]
            trend_status = "ok"

    insights: list[str] = []
    if sentiment_distribution:
        common_sentiment = sentiment_distribution[0]["sentiment"]
        insights.append(f"{common_sentiment} sentiment is most common in the available descriptions.")
    if topic_distribution:
        insights.append(f"{topic_distribution[0]['topic']} is the most frequently detected inferred topic.")
    category_sentiment = grouped_sentiment("category")
    if category_sentiment:
        most_negative = max(category_sentiment, key=lambda row: (row["negative_percentage"], row["category"]))
        if most_negative["observation_count"] >= 3:
            insights.append(
                f"Negative sentiment is most frequent among {most_negative['category']} observations."
            )

    return {
        "status": "ok",
        "message": "Sentiment and topics are approximate lexical indicators, not human-level language understanding.",
        "observation_count": len(working),
        "sentiment_distribution": sentiment_distribution,
        "sentiment_by_category": category_sentiment,
        "sentiment_by_location": grouped_sentiment("location"),
        "topic_distribution": topic_distribution,
        "topic_by_category": grouped_topics("category"),
        "topic_by_location": grouped_topics("location"),
        "top_keywords": top_keywords,
        "sentiment_trend": trend,
        "trend_status": trend_status,
        "insights": insights,
    }
