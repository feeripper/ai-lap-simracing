"""Tests for telemetry column standardization (Garage61 compatibility)."""

from __future__ import annotations

import pandas as pd

from src.analysis.telemetry_columns import standardize_telemetry_columns


def test_renames_garage61_columns_to_internal_names():
    df = pd.DataFrame(
        {
            "Speed": [180, 190, 200],
            "LapDistPct": [0, 0.5, 1.0],
            "Brake": [0, 0.2, 0],
            "Throttle": [1.0, 0.8, 1.0],
            "RPM": [7000, 7200, 7500],
            "SteeringWheelAngle": [0.1, 0.2, 0.1],
            "Gear": [3, 4, 5],
        }
    )

    result = standardize_telemetry_columns(df)

    assert "lap_dist_pct" in result.columns
    assert "speed" in result.columns
    assert "brake" in result.columns
    assert "throttle" in result.columns
    assert "rpm" in result.columns
    assert "steering" in result.columns
    assert "gear" in result.columns
    assert "Speed" not in result.columns
    assert "LapDistPct" not in result.columns


def test_converts_0_1_scale_to_0_100():
    df = pd.DataFrame({"LapDistPct": [0, 0.5, 1.0], "speed": [180, 190, 200]})

    result = standardize_telemetry_columns(df)

    assert result["lap_dist_pct"].iloc[0] == 0.0
    assert result["lap_dist_pct"].iloc[1] == 50.0
    assert result["lap_dist_pct"].iloc[2] == 100.0


def test_legacy_csv_with_lap_dist_pct_0_100_unchanged():
    df = pd.DataFrame({"lap_dist_pct": [0, 50, 100], "speed": [180, 190, 200]})

    result = standardize_telemetry_columns(df)

    assert list(result["lap_dist_pct"]) == [0, 50, 100]
    assert list(result.columns) == ["lap_dist_pct", "speed"]


def test_unknown_columns_left_unchanged():
    df = pd.DataFrame({"lap_dist_pct": [0, 50, 100], "Lat": [1.1, 1.2, 1.3], "Lon": [2.1, 2.2, 2.3]})

    result = standardize_telemetry_columns(df)

    assert "Lat" in result.columns
    assert "Lon" in result.columns
