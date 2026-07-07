"""Unit tests for telemetry comparator."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.comparator import compare_laps


def test_compare_laps_basic_speed_throttle_brake():
    """Test basic comparison with speed, throttle, and brake columns."""
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
        "throttle": [0.9, 1.0, 0.8],
        "brake": [0, 0, 0.5],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
        "throttle": [1.0, 1.0, 1.0],
        "brake": [0, 0, 0],
    })

    result = compare_laps(user_lap, reference_lap)

    # Validate overall structure
    assert "overall" in result
    assert "sectors" in result

    # Validate overall metrics
    assert "comparable_columns" in result["overall"]
    assert "num_points" in result["overall"]
    assert "metrics" in result["overall"]

    # Validate comparable columns
    assert set(result["overall"]["comparable_columns"]) == {"brake", "speed", "throttle"}

    # Validate speed mean_diff follows user - reference
    # User: [180, 190, 200], Reference: [200, 200, 200], Diff: [-20, -10, 0], Mean: -10
    assert result["overall"]["metrics"]["speed"]["mean_diff"] == pytest.approx(-10.0)

    # Validate num_points
    assert result["overall"]["num_points"] == 3


def test_compare_laps_optional_steering_and_gear():
    """Test comparison with optional steering and gear columns."""
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
        "steering": [0, 15, 0],
        "gear": [1, 3, 4],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
        "steering": [0, 10, 0],
        "gear": [1, 3, 5],
    })

    result = compare_laps(user_lap, reference_lap)

    # Validate that steering and gear appear in metrics
    assert "steering" in result["overall"]["metrics"]
    assert "gear" in result["overall"]["metrics"]

    # Validate steering diff
    # User: [0, 15, 0], Reference: [0, 10, 0], Diff: [0, 5, 0], Mean: 1.67
    assert result["overall"]["metrics"]["steering"]["mean_diff"] == pytest.approx(5.0 / 3)

    # Validate gear diff
    # User: [1, 3, 4], Reference: [1, 3, 5], Diff: [0, 0, -1], Mean: -0.33
    assert result["overall"]["metrics"]["gear"]["mean_diff"] == pytest.approx(-1.0 / 3)


def test_compare_laps_ignores_non_numeric_columns():
    """Test that non-numeric columns are ignored."""
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
        "driver_name": ["Alice", "Alice", "Alice"],
        "notes": ["good", "ok", "bad"],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
        "driver_name": ["Bob", "Bob", "Bob"],
    })

    result = compare_laps(user_lap, reference_lap)

    # Validate that non-numeric columns are not in comparable_columns
    assert "driver_name" not in result["overall"]["comparable_columns"]
    assert "notes" not in result["overall"]["comparable_columns"]

    # Only speed should be comparable
    assert result["overall"]["comparable_columns"] == ["speed"]


def test_compare_laps_ignores_columns_not_present_in_both():
    """Test that columns present in only one DataFrame are ignored."""
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
        "rpm": [5000, 6000, 7000],  # Only in user
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
        "steering": [0, 10, 0],  # Only in reference
    })

    result = compare_laps(user_lap, reference_lap)

    # Validate that only common columns are compared
    assert result["overall"]["comparable_columns"] == ["speed"]
    assert "rpm" not in result["overall"]["metrics"]
    assert "steering" not in result["overall"]["metrics"]


def test_compare_laps_sectors():
    """Test sector calculation with lap_dist_pct from 0 to 100."""
    # Create 101 points for 0-100%
    distances = list(range(101))
    user_lap = pd.DataFrame({
        "lap_dist_pct": distances,
        "speed": [180 + i * 0.2 for i in distances],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": distances,
        "speed": [200 for _ in distances],
    })

    result = compare_laps(user_lap, reference_lap)

    # Validate exactly 4 sectors
    assert len(result["sectors"]) == 4

    # Validate sector names and boundaries
    assert result["sectors"][0]["name"] == "Sector 1"
    assert result["sectors"][0]["start_pct"] == 0
    assert result["sectors"][0]["end_pct"] == 25

    assert result["sectors"][1]["name"] == "Sector 2"
    assert result["sectors"][1]["start_pct"] == 25
    assert result["sectors"][1]["end_pct"] == 50

    assert result["sectors"][2]["name"] == "Sector 3"
    assert result["sectors"][2]["start_pct"] == 50
    assert result["sectors"][2]["end_pct"] == 75

    assert result["sectors"][3]["name"] == "Sector 4"
    assert result["sectors"][3]["start_pct"] == 75
    assert result["sectors"][3]["end_pct"] == 100

    # Validate that each sector has metrics
    for sector in result["sectors"]:
        assert "metrics" in sector
        assert "speed" in sector["metrics"]


def test_compare_laps_empty_user_lap():
    """Test error when user_lap is empty."""
    user_lap = pd.DataFrame({"lap_dist_pct": []})
    reference_lap = pd.DataFrame({"lap_dist_pct": [0, 50, 100], "speed": [200, 200, 200]})

    with pytest.raises(ValueError) as exc_info:
        compare_laps(user_lap, reference_lap)

    assert "user_lap is empty" in str(exc_info.value)


def test_compare_laps_empty_reference_lap():
    """Test error when reference_lap is empty."""
    user_lap = pd.DataFrame({"lap_dist_pct": [0, 50, 100], "speed": [180, 190, 200]})
    reference_lap = pd.DataFrame({"lap_dist_pct": []})

    with pytest.raises(ValueError) as exc_info:
        compare_laps(user_lap, reference_lap)

    assert "reference_lap is empty" in str(exc_info.value)


def test_compare_laps_missing_distance_column_user():
    """Test error when distance column is missing from user_lap."""
    user_lap = pd.DataFrame({"speed": [180, 190, 200]})
    reference_lap = pd.DataFrame({"lap_dist_pct": [0, 50, 100], "speed": [200, 200, 200]})

    with pytest.raises(ValueError) as exc_info:
        compare_laps(user_lap, reference_lap)

    assert "distance column" in str(exc_info.value)


def test_compare_laps_missing_distance_column_reference():
    """Test error when distance column is missing from reference_lap."""
    user_lap = pd.DataFrame({"lap_dist_pct": [0, 50, 100], "speed": [180, 190, 200]})
    reference_lap = pd.DataFrame({"speed": [200, 200, 200]})

    with pytest.raises(ValueError) as exc_info:
        compare_laps(user_lap, reference_lap)

    assert "distance column" in str(exc_info.value)


def test_compare_laps_no_comparable_columns():
    """Test error when no comparable columns exist."""
    user_lap = pd.DataFrame({"lap_dist_pct": [0, 50, 100]})
    reference_lap = pd.DataFrame({"lap_dist_pct": [0, 50, 100]})

    with pytest.raises(ValueError) as exc_info:
        compare_laps(user_lap, reference_lap)

    assert "no comparable columns" in str(exc_info.value)


def test_compare_laps_different_row_counts():
    """Test error when DataFrames have different row counts."""
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 25, 50, 75, 100],
        "speed": [200, 200, 200, 200, 200],
    })

    with pytest.raises(ValueError) as exc_info:
        compare_laps(user_lap, reference_lap)

    assert "same number of rows" in str(exc_info.value)


def test_compare_laps_sector_boundaries():
    """Test that sector boundaries follow the exact contract."""
    # Create data with points at exact boundaries
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 25, 50, 75, 100],
        "speed": [180, 190, 200, 210, 220],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 25, 50, 75, 100],
        "speed": [200, 200, 200, 200, 200],
    })

    result = compare_laps(user_lap, reference_lap)

    # Point 25 should be in Sector 1 (0 <= lap_dist_pct <= 25)
    # Point 50 should be in Sector 2 (25 < lap_dist_pct <= 50)
    # Point 75 should be in Sector 3 (50 < lap_dist_pct <= 75)
    # Point 100 should be in Sector 4 (75 < lap_dist_pct <= 100)

    # Sector 1 should have points at 0 and 25 (2 points)
    sector1_speed_diff = result["sectors"][0]["metrics"]["speed"]["mean_diff"]
    # Points: 0 (diff -20), 25 (diff -10) -> mean -15
    assert sector1_speed_diff == pytest.approx(-15.0)

    # Sector 2 should have point at 50 (1 point)
    sector2_speed_diff = result["sectors"][1]["metrics"]["speed"]["mean_diff"]
    # Point: 50 (diff 0) -> mean 0
    assert sector2_speed_diff == pytest.approx(0.0)

    # Sector 3 should have point at 75 (1 point)
    sector3_speed_diff = result["sectors"][2]["metrics"]["speed"]["mean_diff"]
    # Point: 75 (diff 10) -> mean 10
    assert sector3_speed_diff == pytest.approx(10.0)

    # Sector 4 should have point at 100 (1 point)
    sector4_speed_diff = result["sectors"][3]["metrics"]["speed"]["mean_diff"]
    # Point: 100 (diff 20) -> mean 20
    assert sector4_speed_diff == pytest.approx(20.0)


def test_compare_laps_empty_sector_returns_empty_metrics():
    """Test that empty sectors return empty metrics instead of NaN."""
    # Create data only in Sector 1 (0-25)
    user_lap = pd.DataFrame({
        "lap_dist_pct": [0, 10, 20, 25],
        "speed": [180, 185, 190, 195],
    })

    reference_lap = pd.DataFrame({
        "lap_dist_pct": [0, 10, 20, 25],
        "speed": [200, 200, 200, 200],
    })

    result = compare_laps(user_lap, reference_lap)

    # Sector 1 should have metrics
    assert result["sectors"][0]["metrics"] != {}
    assert "speed" in result["sectors"][0]["metrics"]

    # Sectors 2, 3, 4 should have empty metrics
    assert result["sectors"][1]["metrics"] == {}
    assert result["sectors"][2]["metrics"] == {}
    assert result["sectors"][3]["metrics"] == {}

    # Ensure no NaN values in the result
    for sector in result["sectors"]:
        for col, metrics in sector["metrics"].items():
            for metric_name, metric_value in metrics.items():
                assert not pd.isna(metric_value), f"NaN found in {sector['name']}.{col}.{metric_name}"
