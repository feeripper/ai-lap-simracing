"""Unit tests for analysis pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.pipeline import analyze_lap_files


def test_analyze_lap_files_success(tmp_path):
    """Test successful analysis of two CSV files."""
    # Create user CSV
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
        "throttle": [0.9, 1.0, 0.8],
        "brake": [0, 0, 0.5],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
        "throttle": [1.0, 1.0, 1.0],
        "brake": [0, 0, 0],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run analysis
    result = analyze_lap_files(str(user_csv), str(reference_csv))

    # Validate structure
    assert "metadata" in result
    assert "comparison" in result
    assert "insights" in result

    # Validate metadata
    assert result["metadata"]["user_csv_path"] == str(user_csv.absolute())
    assert result["metadata"]["reference_csv_path"] == str(reference_csv.absolute())
    assert result["metadata"]["num_points"] == 101
    assert result["metadata"]["distance_column"] == "lap_dist_pct"
    assert result["metadata"]["user_rows_raw"] == 3
    assert result["metadata"]["reference_rows_raw"] == 3
    assert result["metadata"]["normalized_points"] == 101

    # Validate comparison
    assert "overall" in result["comparison"]
    assert "sectors" in result["comparison"]

    # Validate insights
    assert "summary" in result["insights"]
    assert "priority" in result["insights"]
    assert "recommendations" in result["insights"]
    assert len(result["insights"]["recommendations"]) > 0


def test_analyze_lap_files_user_csv_not_found(tmp_path):
    """Test error when user CSV file does not exist."""
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    with pytest.raises(FileNotFoundError) as exc_info:
        analyze_lap_files("nonexistent.csv", str(reference_csv))

    assert "user CSV file not found" in str(exc_info.value)


def test_analyze_lap_files_reference_csv_not_found(tmp_path):
    """Test error when reference CSV file does not exist."""
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
    })
    user_data.to_csv(user_csv, index=False)

    with pytest.raises(FileNotFoundError) as exc_info:
        analyze_lap_files(str(user_csv), "nonexistent.csv")

    assert "reference CSV file not found" in str(exc_info.value)


def test_analyze_lap_files_empty_csv(tmp_path):
    """Test error when CSV is empty."""
    # Create empty user CSV
    user_csv = tmp_path / "user.csv"
    pd.DataFrame().to_csv(user_csv, index=False)

    # Create valid reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    with pytest.raises(ValueError) as exc_info:
        analyze_lap_files(str(user_csv), str(reference_csv))

    assert "CSV is empty" in str(exc_info.value)


def test_analyze_lap_files_reference_csv_empty(tmp_path):
    """Test error when reference CSV is empty."""
    # Create valid user CSV
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
    })
    user_data.to_csv(user_csv, index=False)

    # Create empty reference CSV
    reference_csv = tmp_path / "reference.csv"
    pd.DataFrame().to_csv(reference_csv, index=False)

    with pytest.raises(ValueError) as exc_info:
        analyze_lap_files(str(user_csv), str(reference_csv))

    assert "CSV is empty" in str(exc_info.value)


def test_analyze_lap_files_missing_distance_column(tmp_path):
    """Test error when distance column is missing."""
    # Create user CSV without lap_dist_pct
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "speed": [180, 190, 200],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    with pytest.raises(ValueError) as exc_info:
        analyze_lap_files(str(user_csv), str(reference_csv))

    assert "distance column" in str(exc_info.value)


def test_analyze_lap_files_custom_num_points(tmp_path):
    """Test analysis with custom num_points."""
    # Create user CSV
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run analysis with custom num_points
    result = analyze_lap_files(str(user_csv), str(reference_csv), num_points=51)

    # Validate metadata
    assert result["metadata"]["num_points"] == 51
    assert result["metadata"]["normalized_points"] == 51

    # Validate comparison
    assert result["comparison"]["overall"]["num_points"] == 51


def test_analyze_lap_files_keeps_user_minus_reference_direction(tmp_path):
    """Test that user - reference direction is preserved."""
    # Create user CSV with lower speed
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],  # Lower than reference
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV with higher speed
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],  # Higher than user
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run analysis
    result = analyze_lap_files(str(user_csv), str(reference_csv))

    # Validate that speed mean_diff is negative (user - reference)
    speed_mean_diff = result["comparison"]["overall"]["metrics"]["speed"]["mean_diff"]
    assert speed_mean_diff < 0


def test_analyze_lap_files_supports_garage61_column_format(tmp_path):
    """Test that Garage61-style CSVs (LapDistPct 0-1, Speed, Brake, etc.) work."""
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "Speed": [180, 190, 200],
        "LapDistPct": [0, 0.5, 1.0],
        "Brake": [0, 0, 0.5],
        "Throttle": [0.9, 1.0, 0.8],
        "RPM": [7000, 7200, 7500],
        "SteeringWheelAngle": [0.1, 0.2, 0.1],
        "Gear": [3, 4, 5],
    })
    user_data.to_csv(user_csv, index=False)

    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "Speed": [200, 200, 200],
        "LapDistPct": [0, 0.5, 1.0],
        "Brake": [0, 0, 0],
        "Throttle": [1.0, 1.0, 1.0],
        "RPM": [7500, 7500, 7500],
        "SteeringWheelAngle": [0.1, 0.1, 0.1],
        "Gear": [4, 5, 5],
    })
    reference_data.to_csv(reference_csv, index=False)

    result = analyze_lap_files(str(user_csv), str(reference_csv))

    assert "metadata" in result
    assert "comparison" in result
    assert "insights" in result
    assert result["metadata"]["distance_column"] == "lap_dist_pct"


def test_analyze_lap_files_no_compatible_distance_column_raises_clear_error(tmp_path):
    """Test that a clear error is raised when no distance column is compatible."""
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({"Speed": [180, 190, 200]})
    user_data.to_csv(user_csv, index=False)

    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    with pytest.raises(ValueError) as exc_info:
        analyze_lap_files(str(user_csv), str(reference_csv))

    assert "distance column" in str(exc_info.value)
    assert "Expected one of" in str(exc_info.value)
