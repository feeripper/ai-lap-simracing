"""Discover, classify and summarize Garage61 CSV telemetry files."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from src.column_mapper import map_columns
from src.filename_parser import FilenameMetadata, parse_filename
from src.io_utils import DataDirectoryError, validate_data_dir, write_json

USER_DRIVER_MARKER = "FelippeAraujo"
MAX_REFERENCE_LAPS = 3


class TelemetryDiscoveryError(DataDirectoryError):
    """Raised when CSV discovery or classification requirements are not met."""


@dataclass(frozen=True)
class LapSummary:
    filename: str
    driver: str | None
    car: str | None
    track: str | None
    lap_time: str | None
    lap_time_seconds: float | None
    available_columns: list[str]
    mapped_columns: dict[str, str | None]

    @classmethod
    def from_csv(cls, csv_path: Path, metadata: FilenameMetadata) -> LapSummary:
        df = pd.read_csv(csv_path, nrows=0)
        available_columns = list(df.columns)
        return cls(
            filename=metadata.original_filename,
            driver=metadata.driver,
            car=metadata.car,
            track=metadata.track,
            lap_time=metadata.lap_time,
            lap_time_seconds=metadata.lap_time_seconds,
            available_columns=available_columns,
            mapped_columns=map_columns(available_columns),
        )


def _is_user_lap(filename: str) -> bool:
    return USER_DRIVER_MARKER.lower() in filename.lower()


def _sort_key_for_references(metadata: FilenameMetadata) -> tuple[int, float, str]:
    """Fastest lap first; files without lap time go last."""
    if metadata.lap_time_seconds is None:
        return (1, float("inf"), metadata.original_filename)
    return (0, metadata.lap_time_seconds, metadata.original_filename)


def discover_csv_files(data_dir: Path) -> list[Path]:
    """Return all CSV files in data_dir sorted by filename."""
    try:
        return validate_data_dir(data_dir, glob_pattern="*.csv")
    except DataDirectoryError as exc:
        raise TelemetryDiscoveryError(str(exc)) from exc


def classify_and_select_laps(
    csv_files: list[Path],
) -> tuple[Path, list[Path]]:
    """Split files into user lap and up to 3 fastest reference laps."""
    user_files = [path for path in csv_files if _is_user_lap(path.name)]
    reference_files = [path for path in csv_files if not _is_user_lap(path.name)]

    if not user_files:
        raise TelemetryDiscoveryError(
            f"No user lap found. Expected a CSV filename containing '{USER_DRIVER_MARKER}'."
        )
    if not reference_files:
        raise TelemetryDiscoveryError("No reference laps found. At least one reference CSV is required.")

    if len(user_files) > 1:
        user_files = sorted(user_files, key=lambda path: path.name)

    reference_metadata = [(path, parse_filename(path.name)) for path in reference_files]
    reference_metadata.sort(key=lambda item: _sort_key_for_references(item[1]))
    selected_references = [path for path, _ in reference_metadata[:MAX_REFERENCE_LAPS]]

    return user_files[0], selected_references


def build_lap_summary(csv_path: Path) -> LapSummary:
    metadata = parse_filename(csv_path.name)
    return LapSummary.from_csv(csv_path, metadata)


def build_telemetry_summary(data_dir: Path) -> dict:
    csv_files = discover_csv_files(data_dir)
    user_path, reference_paths = classify_and_select_laps(csv_files)

    user_lap = build_lap_summary(user_path)
    reference_laps = [build_lap_summary(path) for path in reference_paths]

    return {
        "user_lap": asdict(user_lap),
        "reference_laps": [asdict(lap) for lap in reference_laps],
    }


def write_telemetry_summary(data_dir: Path, output_path: Path) -> dict:
    summary = build_telemetry_summary(data_dir)
    write_json(summary, output_path)
    return summary
