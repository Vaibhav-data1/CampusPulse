import pandas as pd
import pytest

from app.ml.nlp import analyze_nlp, preprocess_text


def observations():
    return pd.DataFrame([
        {"description": "The clean and quiet library is comfortable.", "category": "Facilities", "location": "Library", "observed_at": "2026-01-01T10:00:00Z"},
        {"description": "Wi-Fi is broken and the network is disconnected.", "category": "Wi-Fi / Connectivity", "location": "Library", "observed_at": "2026-01-02T10:00:00Z"},
        {"description": "The cafeteria is very crowded and loud.", "category": "Crowding", "location": "Cafeteria", "observed_at": "2026-01-03T10:00:00Z"},
        {"description": "Fans are broken and the classroom is hot.", "category": "Facilities", "location": "Academic Block", "observed_at": "2026-01-04T10:00:00Z"},
        {"description": "The room is fine today.", "category": "Facilities", "location": "Academic Block", "observed_at": "2026-01-05T10:00:00Z"},
    ])


def test_preprocessing_removes_stop_words_and_handles_malformed_text():
    assert preprocess_text("  THE library!!! 123 ") == ["library"]
    assert preprocess_text(None) == []
    assert preprocess_text("...") == []


def test_sentiment_topics_and_keywords():
    result = analyze_nlp(observations())
    assert result["status"] == "ok"
    assert result["observation_count"] == 5
    assert {row["sentiment"] for row in result["sentiment_distribution"]} >= {"Positive", "Negative"}
    assert any(row["topic"] == "Noise" for row in result["topic_distribution"])
    assert any(row["keyword"] == "broken" for row in result["top_keywords"])
    assert result["trend_status"] == "ok"


def test_multiple_topics_and_nullable_descriptions():
    frame = observations()
    frame.loc[len(frame)] = {"description": None, "category": "Other", "location": "Other", "observed_at": None}
    result = analyze_nlp(frame)
    assert result["observation_count"] == 5
    assert any(row["topic"] == "Temperature / Heat" for row in result["topic_distribution"])


def test_empty_and_short_data_states():
    empty = analyze_nlp(pd.DataFrame(columns=["description", "category", "location"]))
    assert empty["status"] == "empty"
    short = analyze_nlp(pd.DataFrame([{"description": "ok"}]))
    assert short["status"] == "ok"
    assert short["trend_status"] == "insufficient_data"


def test_invalid_columns_are_rejected():
    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_nlp(pd.DataFrame({"category": ["Noise"]}))
