import pandas as pd

from app.ml.analytics import (
    average_crowd_level_by_location,
    average_environmental_rating_by_location,
    average_severity_by_category,
    average_severity_by_location,
    basic_data_quality_statistics,
    counts_by_category,
    counts_by_location,
    daily_weekly_trends,
    location_category_hotspots,
    time_of_day_patterns,
)


def test_counts_by_category():
    df = pd.DataFrame(
        {
            "category": ["Noise", "Noise", "Cleanliness", "Crowding", None],
            "severity": [4, 5, 3, 2, 1],
        }
    )

    result = counts_by_category(df)
    assert result["category"].tolist() == ["Noise", "Cleanliness", "Crowding"]
    assert result["observation_count"].tolist() == [2, 1, 1]


def test_counts_by_location():
    df = pd.DataFrame({"location": ["Library", "Library", "Cafeteria", None]})

    result = counts_by_location(df)
    assert result["location"].tolist() == ["Library", "Cafeteria"]
    assert result["observation_count"].tolist() == [2, 1]


def test_average_severity_by_category_and_location():
    df = pd.DataFrame(
        {
            "category": ["Noise", "Noise", "Facilities"],
            "location": ["Library", "Library", "Cafeteria"],
            "severity": [4, 2, 5],
        }
    )

    category_result = average_severity_by_category(df)
    location_result = average_severity_by_location(df)

    assert category_result["category"].tolist() == ["Noise", "Facilities"]
    assert category_result["average_severity"].tolist() == [3.0, 5.0]
    assert location_result["location"].tolist() == ["Cafeteria", "Library"]
    assert location_result["average_severity"].tolist() == [5.0, 3.0]


def test_average_crowd_and_environmental_rating_by_location():
    df = pd.DataFrame(
        {
            "location": ["Library", "Library", "Cafeteria"],
            "crowd_level": [3, 5, 2],
            "environmental_rating": [4, 2, 5],
        }
    )

    crowd = average_crowd_level_by_location(df)
    environment = average_environmental_rating_by_location(df)

    assert crowd["location"].tolist() == ["Library", "Cafeteria"]
    assert crowd["average_crowd_level"].tolist() == [4.0, 2.0]
    assert environment["location"].tolist() == ["Library", "Cafeteria"]
    assert environment["average_environmental_rating"].tolist() == [3.0, 5.0]


def test_time_of_day_patterns():
    df = pd.DataFrame(
        {
            "observed_at": [
                "2025-01-01T08:15:00Z",
                "2025-01-01T08:45:00Z",
                "2025-01-01T18:00:00Z",
            ]
        }
    )

    result = time_of_day_patterns(df)
    assert result["hour"].tolist()[:9] == [0, 1, 2, 3, 4, 5, 6, 7, 8]
    assert result.loc[result["hour"] == 8, "observation_count"].iloc[0] == 2
    assert result.loc[result["hour"] == 18, "observation_count"].iloc[0] == 1


def test_daily_weekly_trends():
    df = pd.DataFrame(
        {
            "observed_at": [
                "2025-01-01T09:00:00Z",
                "2025-01-01T11:00:00Z",
                "2025-01-08T12:00:00Z",
            ]
        }
    )

    result = daily_weekly_trends(df)
    assert {"daily", "weekly"}.issubset(set(result["period_type"]))
    assert result[result["period_type"] == "daily"]["observation_count"].sum() == 2
    assert result[result["period_type"] == "weekly"]["observation_count"].sum() == 3


def test_location_category_hotspots():
    df = pd.DataFrame(
        {
            "location": ["Library", "Library", "Library", "Cafeteria"],
            "category": ["Noise", "Noise", "Cleanliness", "Noise"],
            "severity": [4, 5, 3, 2],
        }
    )

    result = location_category_hotspots(df)
    assert result.iloc[0]["location"] == "Library"
    assert result.iloc[0]["category"] == "Noise"
    assert result.iloc[0]["observation_count"] == 2
    assert result.iloc[0]["average_severity"] == 4.5


def test_basic_data_quality_statistics():
    df = pd.DataFrame(
        {
            "location": ["Library", None, "Cafeteria"],
            "category": ["Noise", "Crowding", None],
            "severity": [4, None, 2],
            "observed_at": ["2025-01-01T08:00:00Z", "2025-01-03T15:00:00Z", None],
        }
    )

    result = basic_data_quality_statistics(df)
    assert result["total_observations"] == 3
    assert result["unique_locations"] == 2
    assert result["unique_categories"] == 2
    assert result["missing_values"]["location"] == 1
    assert result["missing_values"]["category"] == 1
    assert result["date_range"]["start"] == pd.Timestamp("2025-01-01 08:00:00")


def test_empty_dataset_is_handled_safely():
    empty = pd.DataFrame(columns=["location", "category", "severity", "crowd_level", "environmental_rating", "observed_at"])

    assert counts_by_category(empty).empty
    assert counts_by_location(empty).empty
    assert average_severity_by_category(empty).empty
    assert average_severity_by_location(empty).empty
    assert average_crowd_level_by_location(empty).empty
    assert average_environmental_rating_by_location(empty).empty
    assert time_of_day_patterns(empty).empty
    assert daily_weekly_trends(empty).empty
    assert location_category_hotspots(empty).empty
    assert basic_data_quality_statistics(empty)["total_observations"] == 0


def test_nullable_fields_are_handled_correctly():
    df = pd.DataFrame(
        {
            "location": ["Library", "Cafeteria", None],
            "category": ["Noise", None, "Cleanliness"],
            "severity": [4, pd.NA, 2],
            "crowd_level": [pd.NA, 5, None],
            "environmental_rating": [4, None, 3],
            "observed_at": ["2025-02-01T10:00:00Z", None, "2025-02-03T15:00:00Z"],
        }
    )

    crowd = average_crowd_level_by_location(df)
    environment = average_environmental_rating_by_location(df)
    quality = basic_data_quality_statistics(df)

    assert crowd["average_crowd_level"].tolist() == [5.0]
    assert environment["average_environmental_rating"].tolist() == [3.5, 3.0]
    assert quality["missing_values"]["crowd_level"] == 2
