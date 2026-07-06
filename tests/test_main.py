"""Tests for the CLI entry point (main.py)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from main import main

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


@pytest.fixture()
def sample_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(
        data_dir
        / "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv"
    )
    _write_sample_csv(
        data_dir
        / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )
    return data_dir


def test_main_success(sample_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output_path = tmp_path / "outputs" / "telemetry_summary.json"
    with patch("main.DATA_DIR", sample_data_dir), patch("main.OUTPUT_PATH", output_path):
        exit_code = main()

    assert exit_code == 0
    assert output_path.exists()

    captured = capsys.readouterr()
    assert "FelippeAraujo" in captured.out
    assert "Reference laps: 1" in captured.out
    assert "DanielLewis" in captured.out


def test_main_missing_data_dir(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing_dir = tmp_path / "nonexistent"
    output_path = tmp_path / "outputs" / "telemetry_summary.json"
    with patch("main.DATA_DIR", missing_dir), patch("main.OUTPUT_PATH", output_path):
        exit_code = main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_main_no_user_lap(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(
        data_dir
        / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )
    output_path = tmp_path / "outputs" / "telemetry_summary.json"
    with patch("main.DATA_DIR", data_dir), patch("main.OUTPUT_PATH", output_path):
        exit_code = main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "No user lap found" in captured.err


def test_main_user_lap_without_lap_time(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(data_dir / "FelippeAraujo_nolap.csv")
    _write_sample_csv(
        data_dir
        / "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv"
    )
    output_path = tmp_path / "outputs" / "telemetry_summary.json"
    with patch("main.DATA_DIR", data_dir), patch("main.OUTPUT_PATH", output_path):
        exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "no lap time" in captured.out
