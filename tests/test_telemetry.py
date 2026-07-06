"""Tests for CSV discovery, classification and telemetry summary generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.column_mapper import map_columns
from src.telemetry import (
    TelemetryDiscoveryError,
    build_telemetry_summary,
    classify_and_select_laps,
    discover_csv_files,
)
from tests.conftest import GARAGE61_COLUMNS, write_sample_csv


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
    write_sample_csv(
        data_dir / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )

    with pytest.raises(TelemetryDiscoveryError, match="No user lap found"):
        build_telemetry_summary(data_dir)


def test_requires_reference_lap(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    write_sample_csv(
        data_dir / "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv"
    )

    with pytest.raises(TelemetryDiscoveryError, match="No reference laps found"):
        build_telemetry_summary(data_dir)


def test_map_columns_returns_null_for_missing_fields() -> None:
    mapped = map_columns(["Speed", "Brake"])
    assert mapped["speed"] == "Speed"
    assert mapped["brake"] == "Brake"
    assert mapped["throttle"] is None


@pytest.mark.skipif(
    not Path("data").exists() or not any(Path("data").glob("*.csv")),
    reason="Real CSV files not available in data/",
)
def test_build_summary_with_real_data_files() -> None:
    summary = build_telemetry_summary(Path("data"))
    assert "FelippeAraujo" in summary["user_lap"]["filename"]
    assert len(summary["reference_laps"]) == 3
