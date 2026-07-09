"""Standardize telemetry column names and scales across CSV sources.

This module allows the analysis pipeline to remain generic while supporting CSVs
exported directly from Garage61 (e.g. `LapDistPct`, `Speed`, `SteeringWheelAngle`) as
well as CSVs already using the project's internal column names
(e.g. `lap_dist_pct`, `speed`, `steering`).
"""

from __future__ import annotations

import pandas as pd

# Maps known source column names (case-insensitive) to the internal standardized
# column name used throughout the analysis pipeline.
COLUMN_NAME_MAP: dict[str, str] = {
    "lapdistpct": "lap_dist_pct",
    "lap_dist_pct": "lap_dist_pct",
    "speed": "speed",
    "throttle": "throttle",
    "brake": "brake",
    "steeringwheelangle": "steering",
    "steering": "steering",
    "gear": "gear",
    "rpm": "rpm",
    "lataccel": "lat_accel",
    "longaccel": "long_accel",
    "vertaccel": "vert_accel",
    "yaw": "yaw",
    "yawrate": "yaw_rate",
}

# If the distance column's max value is at or below this threshold, it is assumed to
# be in the 0-1 scale (as exported by Garage61) rather than the internal 0-100 scale.
DISTANCE_SCALE_THRESHOLD = 1.5

DISTANCE_COLUMN = "lap_dist_pct"


def standardize_telemetry_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `df` with standardized telemetry column names and scales.

    - Column names are matched case-insensitively against `COLUMN_NAME_MAP` and
      renamed to the internal standardized name. Unknown columns are left unchanged.
    - If the resulting `lap_dist_pct` column has a max value <= 1.5, it is assumed to
      be in the 0-1 scale and is multiplied by 100 to match the internal 0-100 scale.
      Columns already in the 0-100 scale are left unchanged.

    Args:
        df: Raw telemetry DataFrame, in either Garage61 or internal column format.

    Returns:
        A new DataFrame with standardized column names and distance scale.
    """
    result = df.copy()

    rename_map: dict[str, str] = {}
    for column in result.columns:
        standardized = COLUMN_NAME_MAP.get(column.strip().lower())
        if standardized and standardized != column:
            rename_map[column] = standardized

    if rename_map:
        result = result.rename(columns=rename_map)

    if DISTANCE_COLUMN in result.columns:
        max_value = result[DISTANCE_COLUMN].max()
        if pd.notna(max_value) and max_value <= DISTANCE_SCALE_THRESHOLD:
            result[DISTANCE_COLUMN] = result[DISTANCE_COLUMN] * 100

    return result
