"""End-to-end pipeline for analyzing user lap against reference lap."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from src.analysis.comparator import compare_laps
from src.analysis.diagnosis import generate_diagnosis
from src.analysis.insight_generator import generate_insights
from src.analysis.normalizer import normalize_lap_by_distance
from src.analysis.telemetry_columns import standardize_telemetry_columns


DIAGNOSIS_VERSION = "1.0"


def analyze_lap_files(
    user_csv_path: str,
    reference_csv_path: str,
    distance_column: str = "lap_dist_pct",
    num_points: int = 101,
) -> dict:
    """Analyze a user lap against a reference lap from CSV files.

    This function reads two CSV files, normalizes them to the same distance basis,
    compares the telemetry data, and generates coaching insights.

    Args:
        user_csv_path: Path to the user's lap CSV file
        reference_csv_path: Path to the reference lap CSV file
        distance_column: Name of the column containing lap distance percentage
        num_points: Number of points to normalize to (default: 101)

    Returns:
        A dictionary containing:
        {
            "metadata": {
                "user_csv_path": "...",
                "reference_csv_path": "...",
                "num_points": 101,
                "distance_column": "lap_dist_pct",
                "user_rows_raw": 123,
                "reference_rows_raw": 123,
                "normalized_points": 101
            },
            "comparison": {
                "overall": {...},
                "sectors": [...]
            },
            "insights": {
                "summary": "...",
                "priority": "...",
                "recommendations": [...],
                "sector_insights": [...]
            }
        }

    Raises:
        FileNotFoundError: If CSV files do not exist
        ValueError: If CSVs are empty or missing required columns
    """
    # Validate CSV files exist
    user_csv = Path(user_csv_path)
    reference_csv = Path(reference_csv_path)

    if not user_csv.exists():
        raise FileNotFoundError(f"user CSV file not found: {user_csv_path}")

    if not reference_csv.exists():
        raise FileNotFoundError(f"reference CSV file not found: {reference_csv_path}")

    # Read CSV files
    try:
        user_lap = pd.read_csv(user_csv_path)
    except EmptyDataError:
        raise ValueError("user CSV is empty")

    try:
        reference_lap = pd.read_csv(reference_csv_path)
    except EmptyDataError:
        raise ValueError("reference CSV is empty")

    # Validate CSVs are not empty
    if user_lap.empty:
        raise ValueError("user CSV is empty")

    if reference_lap.empty:
        raise ValueError("reference CSV is empty")

    # Standardize column names/scales (e.g. Garage61 exports) before validation.
    user_lap = standardize_telemetry_columns(user_lap)
    reference_lap = standardize_telemetry_columns(reference_lap)

    # Validate distance column exists
    if distance_column not in user_lap.columns:
        raise ValueError(
            f"distance column '{distance_column}' not found in user CSV. "
            f"Expected one of: lap_dist_pct, LapDistPct"
        )

    if distance_column not in reference_lap.columns:
        raise ValueError(
            f"distance column '{distance_column}' not found in reference CSV. "
            f"Expected one of: lap_dist_pct, LapDistPct"
        )

    # Store raw row counts
    user_rows_raw = len(user_lap)
    reference_rows_raw = len(reference_lap)

    # Measure processing time (from normalization through diagnosis generation)
    start_time = time.perf_counter()

    # Normalize both laps
    user_normalized = normalize_lap_by_distance(user_lap, distance_column, num_points)
    reference_normalized = normalize_lap_by_distance(reference_lap, distance_column, num_points)

    # Compare laps
    comparison = compare_laps(user_normalized, reference_normalized, distance_column)

    # Generate insights
    insights = generate_insights(comparison)

    # Generate diagnosis
    diagnosis = generate_diagnosis(comparison, diagnosis_version=DIAGNOSIS_VERSION)

    # Use the diagnosis summary (based on number of opportunities) for the persisted summary
    insights["summary"] = diagnosis.get("summary")

    processing_time_ms = round((time.perf_counter() - start_time) * 1000, 6)

    # Surface warnings from diagnosis or validation
    warnings = diagnosis.get("warnings", [])

    # Return complete result
    return {
        "status": "completed",
        "diagnosis_version": DIAGNOSIS_VERSION,
        "processing_time_ms": processing_time_ms,
        "metadata": {
            "user_csv_path": str(user_csv.absolute()),
            "reference_csv_path": str(reference_csv.absolute()),
            "num_points": num_points,
            "distance_column": distance_column,
            "user_rows_raw": user_rows_raw,
            "reference_rows_raw": reference_rows_raw,
            "normalized_points": len(user_normalized),
        },
        "comparison": comparison,
        "insights": insights,
        "diagnosis": diagnosis,
        "top_opportunities": diagnosis.get("top_opportunities", []),
        "training_plan": diagnosis.get("training_plan", {}),
        "warnings": warnings,
    }
