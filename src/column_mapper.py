"""Map Garage61 CSV columns to canonical telemetry field names."""

from __future__ import annotations

# Canonical field -> known Garage61 column names (first match wins).
TELEMETRY_COLUMN_ALIASES: dict[str, list[str]] = {
    "speed": ["Speed"],
    "lap_dist_pct": ["LapDistPct"],
    "latitude": ["Lat"],
    "longitude": ["Lon"],
    "brake": ["Brake"],
    "throttle": ["Throttle"],
    "rpm": ["RPM"],
    "steering": ["SteeringWheelAngle"],
    "gear": ["Gear"],
    "clutch": ["Clutch"],
    "abs_active": ["ABSActive"],
    "drs_active": ["DRSActive"],
    "lat_accel": ["LatAccel"],
    "long_accel": ["LongAccel"],
    "vert_accel": ["VertAccel"],
    "yaw": ["Yaw"],
    "yaw_rate": ["YawRate"],
    "position_type": ["PositionType"],
}


def map_columns(available_columns: list[str]) -> dict[str, str | None]:
    """Return canonical field names mapped to actual CSV column names."""
    available = set(available_columns)
    return {
        canonical: next((alias for alias in aliases if alias in available), None)
        for canonical, aliases in TELEMETRY_COLUMN_ALIASES.items()
    }
