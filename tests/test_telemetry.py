"""Tests for CSV discovery, classification and telemetry summary generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.column_mapper import map_columns
from src.telemetry import (
    TelemetryDiscoveryError,
    build_telemetry_summary,
    classify_and_select_laps,
    discover_csv_files,
    write_telemetry_summary,
)


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


def _write_sample_csv(path: Path) -> None:
    pd.DataFrame({col: [0.0] for col in GARAGE61_COLUMNS}).to_csv(path, index=False)


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    files = {
        "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv": "user",
        "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv": "ref",
        "Garage61_RomanRichtr_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.472.csv": "ref",
        "Garage61_TravisBumgarner_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.55.695.csv": "ref",
        "Garage61_SlowerDriver_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.58.000.csv": "ref",
    }
    for filename in files:
        _write_sample_csv(data_dir / filename)

    return data_dir


def test_discover_csv_files(sample_data_dir: Path) -> None:
    files = discover_csv_files(sample_data_dir)
    assert len(files) == 5


def test_classify_and_select_top_three_references(sample_data_dir: Path) -> None:
    csv_files = discover_csv_files(sample_data_dir)
    user_path, reference_paths = classify_and_select_laps(csv_files)

    assert "FelippeAraujo" in user_path.name
    assert len(reference_paths) == 3

    selected_times = [path.name.split("_")[-1].replace(".csv", "") for path in reference_paths]
    assert selected_times == ["01.53.244", "01.53.472", "01.55.695"]


def test_build_telemetry_summary_structure(sample_data_dir: Path) -> None:
    summary = build_telemetry_summary(sample_data_dir)

    user = summary["user_lap"]
    assert user["filename"].endswith("FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv")
    assert user["driver"] == "FelippeAraujo"
    assert user["car"] == "AudiRS3LMSGen2TCR"
    assert user["track"] == "WatkinsGlenInternational(Boot)"
    assert user["lap_time"] == "01.56.068"
    assert user["available_columns"] == GARAGE61_COLUMNS
    assert user["mapped_columns"]["speed"] == "Speed"
    assert user["mapped_columns"]["brake"] == "Brake"

    assert len(summary["reference_laps"]) == 3
    assert summary["reference_laps"][0]["lap_time"] == "01.53.244"
    assert summary["reference_laps"][1]["lap_time"] == "01.53.472"
    assert summary["reference_laps"][2]["lap_time"] == "01.55.695"


def test_requires_user_lap(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(
        data_dir / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )

    with pytest.raises(TelemetryDiscoveryError, match="No user lap found"):
        build_telemetry_summary(data_dir)


def test_requires_reference_lap(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(
        data_dir / "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv"
    )

    with pytest.raises(TelemetryDiscoveryError, match="No reference laps found"):
        build_telemetry_summary(data_dir)


def test_map_columns_returns_null_for_missing_fields() -> None:
    mapped = map_columns(["Speed", "Brake"])
    assert mapped["speed"] == "Speed"
    assert mapped["brake"] == "Brake"
    assert mapped["throttle"] is None


def test_discover_csv_files_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(TelemetryDiscoveryError, match="Data directory not found"):
        discover_csv_files(tmp_path / "nonexistent")


def test_discover_csv_files_empty_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(TelemetryDiscoveryError, match="No CSV files found"):
        discover_csv_files(empty)


def test_classify_multiple_user_laps_picks_first_alphabetically(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(
        data_dir
        / "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv"
    )
    _write_sample_csv(
        data_dir
        / "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.57.000.csv"
    )
    _write_sample_csv(
        data_dir
        / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )
    csv_files = discover_csv_files(data_dir)
    user_path, reference_paths = classify_and_select_laps(csv_files)

    assert "01.56.068" in user_path.name
    assert len(reference_paths) == 1


def test_references_without_lap_time_sorted_last(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(
        data_dir
        / "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv"
    )
    _write_sample_csv(data_dir / "ref_no_time.csv")
    _write_sample_csv(
        data_dir
        / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )
    csv_files = discover_csv_files(data_dir)
    _, reference_paths = classify_and_select_laps(csv_files)

    assert "DanielLewis" in reference_paths[0].name
    assert reference_paths[1].name == "ref_no_time.csv"


def test_write_telemetry_summary_creates_file(sample_data_dir: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "out" / "telemetry_summary.json"
    summary = write_telemetry_summary(sample_data_dir, output_path)

    assert output_path.exists()
    import json

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written == summary
    assert "user_lap" in written
    assert len(written["reference_laps"]) == 3


@pytest.mark.skipif(
    not Path("data").exists() or not any(Path("data").glob("*.csv")),
    reason="Real CSV files not available in data/",
)
def test_build_summary_with_real_data_files() -> None:
    summary = build_telemetry_summary(Path("data"))
    assert "FelippeAraujo" in summary["user_lap"]["filename"]
    assert len(summary["reference_laps"]) == 3
