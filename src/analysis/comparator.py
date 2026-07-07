"""Compare user lap against reference lap for telemetry analysis."""

from __future__ import annotations

import pandas as pd


def compare_laps(
    user_lap: pd.DataFrame,
    reference_lap: pd.DataFrame,
    distance_column: str = "lap_dist_pct",
) -> dict:
    """Compare a user lap against a reference lap.

    This function computes differences between user and reference telemetry data
    for comparable numeric columns. Both laps should already be normalized to the
    same distance basis (e.g., 0-100% of lap distance).

    Args:
        user_lap: DataFrame containing user telemetry data with distance column
        reference_lap: DataFrame containing reference telemetry data with distance column
        distance_column: Name of the column containing lap distance percentage

    Returns:
        A dictionary containing overall metrics and sector-by-sector metrics:
        {
            "overall": {
                "comparable_columns": ["speed", "throttle", ...],
                "num_points": 101,
                "metrics": {
                    "speed": {
                        "mean_diff": -5.2,
                        "min_diff": -20.0,
                        "max_diff": 3.0,
                        "mean_abs_diff": 6.1
                    },
                    ...
                }
            },
            "sectors": [
                {
                    "name": "Sector 1",
                    "start_pct": 0,
                    "end_pct": 25,
                    "metrics": {
                        "speed": {
                            "mean_diff": -4.0,
                            "mean_abs_diff": 5.0
                        },
                        ...
                    }
                },
                ...
            ]
        }

    Raises:
        ValueError: If DataFrames are empty, missing distance column, have different
                    row counts, or no comparable columns exist
    """
    # Validate DataFrames are not empty
    if user_lap.empty:
        raise ValueError("user_lap is empty")

    if reference_lap.empty:
        raise ValueError("reference_lap is empty")

    # Validate distance column exists
    if distance_column not in user_lap.columns:
        raise ValueError(f"distance column '{distance_column}' not found in user_lap")

    if distance_column not in reference_lap.columns:
        raise ValueError(f"distance column '{distance_column}' not found in reference_lap")

    # Validate same number of rows
    if len(user_lap) != len(reference_lap):
        raise ValueError("user_lap and reference_lap must have the same number of rows")

    # Identify comparable columns (numeric, common to both, excluding distance column)
    user_numeric = user_lap.select_dtypes(include=["number"]).columns.tolist()
    ref_numeric = reference_lap.select_dtypes(include=["number"]).columns.tolist()

    common_numeric = set(user_numeric) & set(ref_numeric)
    common_numeric.discard(distance_column)

    comparable_columns = sorted(common_numeric)

    if not comparable_columns:
        raise ValueError("no comparable columns found between user_lap and reference_lap")

    # Calculate overall metrics
    overall_metrics = {}
    for col in comparable_columns:
        user_values = user_lap[col].values
        ref_values = reference_lap[col].values
        diff = user_values - ref_values

        overall_metrics[col] = {
            "mean_diff": float(diff.mean()),
            "min_diff": float(diff.min()),
            "max_diff": float(diff.max()),
            "mean_abs_diff": float(abs(diff).mean()),
        }

    # Define sectors
    sectors = [
        {"name": "Sector 1", "start_pct": 0, "end_pct": 25},
        {"name": "Sector 2", "start_pct": 25, "end_pct": 50},
        {"name": "Sector 3", "start_pct": 50, "end_pct": 75},
        {"name": "Sector 4", "start_pct": 75, "end_pct": 100},
    ]

    # Calculate sector metrics
    sector_results = []
    for sector in sectors:
        start_pct = sector["start_pct"]
        end_pct = sector["end_pct"]

        # Filter rows within this sector following exact contract:
        # Sector 1: 0 <= lap_dist_pct <= 25
        # Sector 2: 25 < lap_dist_pct <= 50
        # Sector 3: 50 < lap_dist_pct <= 75
        # Sector 4: 75 < lap_dist_pct <= 100
        if start_pct == 0:
            mask = (user_lap[distance_column] >= start_pct) & (user_lap[distance_column] <= end_pct)
        else:
            mask = (user_lap[distance_column] > start_pct) & (user_lap[distance_column] <= end_pct)

        # Check if sector has any points
        if mask.sum() == 0:
            sector_metrics = {}
        else:
            sector_metrics = {}
            for col in comparable_columns:
                user_values = user_lap.loc[mask, col].values
                ref_values = reference_lap.loc[mask, col].values
                diff = user_values - ref_values

                sector_metrics[col] = {
                    "mean_diff": float(diff.mean()),
                    "mean_abs_diff": float(abs(diff).mean()),
                }

        sector_results.append({
            "name": sector["name"],
            "start_pct": start_pct,
            "end_pct": end_pct,
            "metrics": sector_metrics,
        })

    return {
        "overall": {
            "comparable_columns": comparable_columns,
            "num_points": len(user_lap),
            "metrics": overall_metrics,
        },
        "sectors": sector_results,
    }
