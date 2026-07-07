"""Normalize telemetry laps by distance percentage for comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd


class DistanceColumnNotFoundError(Exception):
    """Raised when the required distance column is not found in the DataFrame."""


def normalize_lap_by_distance(
    df: pd.DataFrame,
    distance_column: str = "lap_dist_pct",
    num_points: int = 101,
) -> pd.DataFrame:
    """Normalize a telemetry lap to a fixed number of points by distance percentage.

    This function interpolates the telemetry data to a fixed number of points (default 101)
    evenly spaced from 0% to 100% of the lap distance. This allows comparison between
    laps with different sampling rates or numbers of data points.

    Args:
        df: DataFrame containing telemetry data with a distance/percentage column
        distance_column: Name of the column containing lap distance percentage (0-100)
        num_points: Number of points to interpolate to (default: 101 for 0-100%)

    Returns:
        A new DataFrame with normalized telemetry data containing exactly `num_points` rows.
        The distance column will be evenly spaced from 0 to 100. Numeric columns are
        interpolated; non-numeric columns are dropped.

    Raises:
        DistanceColumnNotFoundError: If the distance column is not found in the DataFrame
        ValueError: If the DataFrame is empty, num_points < 2, or has insufficient data

    Example:
        >>> df = pd.DataFrame({
        ...     "lap_dist_pct": [0, 50, 100],
        ...     "speed": [0, 150, 200],
        ...     "throttle": [0, 1, 0]
        ... })
        >>> normalized = normalize_lap_by_distance(df)
        >>> len(normalized)
        101
        >>> normalized["lap_dist_pct"].iloc[0]
        0.0
        >>> normalized["lap_dist_pct"].iloc[-1]
        100.0
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    if num_points < 2:
        raise ValueError(f"num_points must be at least 2, got {num_points}")

    if distance_column not in df.columns:
        raise DistanceColumnNotFoundError(
            f"Distance column '{distance_column}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    # Sort by distance to handle out-of-order data
    df_sorted = df.sort_values(distance_column).copy()

    # Create target distance points (0 to 100) using linspace
    target_distances = np.linspace(0, 100, num_points)

    # Select numeric columns for interpolation (excluding the distance column itself)
    numeric_cols = df_sorted.select_dtypes(include=["number"]).columns.tolist()
    if distance_column in numeric_cols:
        numeric_cols.remove(distance_column)

    # Create result DataFrame with target distances
    result = pd.DataFrame({distance_column: target_distances})

    # Interpolate each numeric column using numpy.interp
    x_original = df_sorted[distance_column].values
    for col in numeric_cols:
        y_original = df_sorted[col].values
        result[col] = np.interp(target_distances, x_original, y_original)

    return result
