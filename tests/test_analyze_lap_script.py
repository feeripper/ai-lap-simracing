"""Unit tests for analyze_lap CLI script."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from scripts.analyze_lap import build_parser, main


def test_analyze_lap_script_success(tmp_path, capsys):
    """Test successful execution of the script."""
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

    # Run script
    exit_code = main([str(user_csv), str(reference_csv)])

    # Validate exit code
    assert exit_code == 0

    # Capture stdout
    captured = capsys.readouterr()
    stdout = captured.out

    # Validate stdout is valid JSON
    result = json.loads(stdout)

    # Validate structure
    assert "metadata" in result
    assert "comparison" in result
    assert "insights" in result


def test_analyze_lap_script_custom_num_points(tmp_path, capsys):
    """Test script with custom num_points."""
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

    # Run script with custom num_points
    exit_code = main([str(user_csv), str(reference_csv), "--num-points", "51"])

    # Validate exit code
    assert exit_code == 0

    # Capture stdout
    captured = capsys.readouterr()
    stdout = captured.out

    # Parse JSON
    result = json.loads(stdout)

    # Validate num_points in metadata
    assert result["metadata"]["num_points"] == 51
    assert result["metadata"]["normalized_points"] == 51


def test_analyze_lap_script_missing_user_csv(tmp_path, capsys):
    """Test script with missing user CSV."""
    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run script with non-existent user CSV
    exit_code = main(["nonexistent.csv", str(reference_csv)])

    # Validate exit code
    assert exit_code == 1

    # Capture stderr
    captured = capsys.readouterr()
    stderr = captured.err

    # Validate error message
    assert "user CSV file not found" in stderr


def test_analyze_lap_script_missing_required_args(capsys):
    """Test script with missing required arguments."""
    # Run script without arguments
    with pytest.raises(SystemExit) as exc_info:
        main([])

    # Validate exit code is not 0
    assert exc_info.value.code != 0


def test_build_parser_has_expected_arguments():
    """Test that parser has expected arguments."""
    parser = build_parser()

    # Test with valid arguments
    args = parser.parse_args(["user.csv", "reference.csv"])
    assert args.user_csv_path == "user.csv"
    assert args.reference_csv_path == "reference.csv"
    assert args.distance_column == "lap_dist_pct"
    assert args.num_points == 101

    # Test with custom arguments
    args = parser.parse_args([
        "user.csv",
        "reference.csv",
        "--distance-column",
        "custom_dist",
        "--num-points",
        "51"
    ])
    assert args.distance_column == "custom_dist"
    assert args.num_points == 51
