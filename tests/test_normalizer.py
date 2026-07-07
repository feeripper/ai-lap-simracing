"""Unit tests for telemetry normalizer."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.normalizer import DistanceColumnNotFoundError, normalize_lap_by_distance


def test_normalize_lap_with_valid_data():
    """Test normalizing a lap with valid telemetry data."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [0, 150, 200],
        "throttle": [0, 1, 0],
        "brake": [1, 0, 1],
    })

    result = normalize_lap_by_distance(df)

    # Check that we have 101 points
    assert len(result) == 101

    # Check that distance column is 0 to 100
    assert result["lap_dist_pct"].iloc[0] == 0
    assert result["lap_dist_pct"].iloc[-1] == 100

    # Check that numeric columns are preserved
    assert "speed" in result.columns
    assert "throttle" in result.columns
    assert "brake" in result.columns

    # Check interpolation: at 0%, values should match start
    assert result["speed"].iloc[0] == 0
    assert result["throttle"].iloc[0] == 0
    assert result["brake"].iloc[0] == 1

    # Check interpolation: at 100%, values should match end
    assert result["speed"].iloc[-1] == 200
    assert result["throttle"].iloc[-1] == 0
    assert result["brake"].iloc[-1] == 1


def test_normalize_lap_with_custom_num_points():
    """Test normalizing with a custom number of points."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [0, 150, 200],
    })

    result = normalize_lap_by_distance(df, num_points=51)

    assert len(result) == 51
    assert result["lap_dist_pct"].iloc[0] == 0
    assert result["lap_dist_pct"].iloc[-1] == 100


def test_normalize_lap_with_out_of_order_data():
    """Test that out-of-order data is handled correctly."""
    df = pd.DataFrame({
        "lap_dist_pct": [100, 0, 50],
        "speed": [200, 0, 150],
        "throttle": [0, 0, 1],
    })

    result = normalize_lap_by_distance(df)

    # Should still produce correct interpolation
    assert len(result) == 101
    assert result["speed"].iloc[0] == 0
    assert result["speed"].iloc[-1] == 200


def test_normalize_lap_with_missing_distance_column():
    """Test error when distance column is missing."""
    df = pd.DataFrame({
        "speed": [0, 150, 200],
        "throttle": [0, 1, 0],
    })

    with pytest.raises(DistanceColumnNotFoundError) as exc_info:
        normalize_lap_by_distance(df)

    assert "lap_dist_pct" in str(exc_info.value)
    assert "not found" in str(exc_info.value)


def test_normalize_lap_with_empty_dataframe():
    """Test error when DataFrame is empty."""
    df = pd.DataFrame({"lap_dist_pct": []})

    with pytest.raises(ValueError) as exc_info:
        normalize_lap_by_distance(df)

    assert "empty" in str(exc_info.value).lower()


def test_normalize_lap_with_non_numeric_columns():
    """Test that non-numeric columns are dropped."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [0, 150, 200],
        "driver_name": ["Alice", "Alice", "Alice"],  # Non-numeric
        "team": ["TeamA", "TeamA", "TeamA"],  # Non-numeric
    })

    result = normalize_lap_by_distance(df)

    # Non-numeric columns should be dropped
    assert "driver_name" not in result.columns
    assert "team" not in result.columns

    # Numeric columns should be preserved
    assert "speed" in result.columns
    assert "lap_dist_pct" in result.columns


def test_normalize_lap_interpolation_at_midpoint():
    """Test that interpolation works correctly at the midpoint."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 100],
        "speed": [0, 200],
        "throttle": [0, 1],
    })

    result = normalize_lap_by_distance(df)

    # At 50%, values should be interpolated
    midpoint_idx = 50  # Index 50 is 50% in 101 points
    assert result["speed"].iloc[midpoint_idx] == 100  # Midpoint of 0 and 200
    assert result["throttle"].iloc[midpoint_idx] == 0.5  # Midpoint of 0 and 1


def test_normalize_lap_with_gear_column():
    """Test that gear column (integer) is preserved and interpolated."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 33, 66, 100],
        "speed": [0, 100, 150, 200],
        "gear": [1, 2, 3, 4],
    })

    result = normalize_lap_by_distance(df)

    assert "gear" in result.columns
    # Gear should be interpolated (may be float values)
    assert result["gear"].iloc[0] == 1
    assert result["gear"].iloc[-1] == 4


def test_normalize_lap_with_steering_column():
    """Test that steering column is preserved and interpolated."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [0, 150, 200],
        "steering": [0, 15, 0],  # Steering angle in degrees
    })

    result = normalize_lap_by_distance(df)

    assert "steering" in result.columns
    assert result["steering"].iloc[0] == 0
    assert result["steering"].iloc[-1] == 0
    # At 50%, should be around 15
    assert abs(result["steering"].iloc[50] - 15) < 0.1


def test_normalize_lap_with_custom_distance_column():
    """Test using a custom distance column name."""
    df = pd.DataFrame({
        "distance_pct": [0, 50, 100],
        "speed": [0, 150, 200],
    })

    result = normalize_lap_by_distance(df, distance_column="distance_pct")

    assert len(result) == 101
    assert "distance_pct" in result.columns
    assert result["distance_pct"].iloc[0] == 0
    assert result["distance_pct"].iloc[-1] == 100


def test_normalize_lap_with_irregular_distance_points():
    """Test that irregular distance points don't generate NaN."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 0.7, 13.4, 57.8, 100],
        "speed": [0, 50, 120, 180, 200],
        "throttle": [0, 0.8, 1, 0.9, 0],
    })

    result = normalize_lap_by_distance(df)

    # Check that no NaN values are present
    assert result["speed"].isna().sum() == 0
    assert result["throttle"].isna().sum() == 0

    # Check that interpolation still works
    assert result["speed"].iloc[0] == 0
    assert result["speed"].iloc[-1] == 200
    assert result["throttle"].iloc[0] == 0
    assert result["throttle"].iloc[-1] == 0


def test_normalize_lap_with_num_points_less_than_2():
    """Test error when num_points is less than 2."""
    df = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [0, 150, 200],
    })

    with pytest.raises(ValueError) as exc_info:
        normalize_lap_by_distance(df, num_points=1)

    assert "at least 2" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        normalize_lap_by_distance(df, num_points=0)

    assert "at least 2" in str(exc_info.value)
