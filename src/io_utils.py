"""Shared I/O utilities for reading data directories and writing output files."""

from __future__ import annotations

import json
from pathlib import Path


class DataDirectoryError(Exception):
    """Raised when a required data directory is missing or empty."""


def validate_data_dir(data_dir: Path, glob_pattern: str = "*.csv") -> list[Path]:
    """Validate that data_dir exists and contains files matching glob_pattern.

    Returns the sorted list of matching paths.
    Raises DataDirectoryError if the directory is missing or has no matches.
    """
    if not data_dir.is_dir():
        raise DataDirectoryError(f"Data directory not found: {data_dir}")

    matched_files = sorted(data_dir.glob(glob_pattern))
    if not matched_files:
        raise DataDirectoryError(f"No {glob_pattern} files found in {data_dir}")

    return matched_files


def write_json(data: dict | list, output_path: Path) -> None:
    """Write data as formatted JSON, creating parent directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
