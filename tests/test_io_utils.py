"""Tests for shared I/O utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.io_utils import DataDirectoryError, validate_data_dir, write_json


def test_validate_data_dir_returns_sorted_matches(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "b.csv").write_text("col\n1\n")
    (data_dir / "a.csv").write_text("col\n2\n")

    result = validate_data_dir(data_dir, glob_pattern="*.csv")
    assert [p.name for p in result] == ["a.csv", "b.csv"]


def test_validate_data_dir_raises_on_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(DataDirectoryError, match="Data directory not found"):
        validate_data_dir(tmp_path / "missing")


def test_validate_data_dir_raises_on_no_matches(tmp_path: Path) -> None:
    data_dir = tmp_path / "empty"
    data_dir.mkdir()

    with pytest.raises(DataDirectoryError, match="No \\*\\.csv files found"):
        validate_data_dir(data_dir, glob_pattern="*.csv")


def test_write_json_creates_file_and_parents(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "dir" / "output.json"
    data = {"key": "value", "num": 42}

    write_json(data, output_path)

    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded == data


def test_write_json_uses_readable_formatting(tmp_path: Path) -> None:
    output_path = tmp_path / "out.json"
    write_json({"a": 1}, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert "  " in content  # indented
