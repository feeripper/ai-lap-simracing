"""Shared test fixtures and constants for telemetry tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

GARAGE61_COLUMNS = [
    "Speed",
    "LapDistPct",
    "Lat",
    "Lon",
    "Brake",
    "Throttle",
    "RPM",
    "SteeringWheelAngle",
    "Gear",
]

SAMPLE_FILENAMES = {
    "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv": "user",
    "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv": "ref",
    "Garage61_RomanRichtr_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.472.csv": "ref",
    "Garage61_TravisBumgarner_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.55.695.csv": "ref",
    "Garage61_SlowerDriver_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.58.000.csv": "ref",
}


def write_sample_csv(path: Path, columns: list[str] | None = None) -> None:
    """Write a minimal CSV with standard Garage61 columns."""
    cols = columns or GARAGE61_COLUMNS
    pd.DataFrame({col: [0.0] for col in cols}).to_csv(path, index=False)


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory with sample CSV files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    for filename in SAMPLE_FILENAMES:
        write_sample_csv(data_dir / filename)

    return data_dir
