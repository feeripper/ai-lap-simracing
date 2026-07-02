"""Parse metadata from Garage61 CSV filenames."""

from __future__ import annotations

import re
from dataclasses import dataclass

LAP_TIME_PATTERN = re.compile(r"(\d{2}\.\d{2}\.\d{3})\.csv$", re.IGNORECASE)
GARAGE61_FILENAME_PATTERN = re.compile(
    r"^(?:Garage61_)?(?P<driver>[^_]+)_(?P<car>[^_]+)_(?P<track>.+)_(?P<lap_time>\d{2}\.\d{2}\.\d{3})\.csv$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FilenameMetadata:
    original_filename: str
    driver: str | None
    car: str | None
    track: str | None
    lap_time: str | None
    lap_time_seconds: float | None


def lap_time_to_seconds(lap_time: str) -> float:
    """Convert MM.SS.mmm lap time string to total seconds."""
    minutes, rest = lap_time.split(".", 1)
    seconds, milliseconds = rest.split(".", 1)
    return int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def parse_filename(filename: str) -> FilenameMetadata:
    """Extract driver, car, track and lap time from a Garage61-style filename."""
    if not filename.lower().startswith("garage61_"):
        lap_time_match = LAP_TIME_PATTERN.search(filename)
        lap_time = lap_time_match.group(1) if lap_time_match else None
        return FilenameMetadata(
            original_filename=filename,
            driver=None,
            car=None,
            track=None,
            lap_time=lap_time,
            lap_time_seconds=lap_time_to_seconds(lap_time) if lap_time else None,
        )

    match = GARAGE61_FILENAME_PATTERN.match(filename)
    if match:
        lap_time = match.group("lap_time")
        return FilenameMetadata(
            original_filename=filename,
            driver=match.group("driver"),
            car=match.group("car"),
            track=match.group("track"),
            lap_time=lap_time,
            lap_time_seconds=lap_time_to_seconds(lap_time),
        )

    lap_time_match = LAP_TIME_PATTERN.search(filename)
    lap_time = lap_time_match.group(1) if lap_time_match else None
    return FilenameMetadata(
        original_filename=filename,
        driver=None,
        car=None,
        track=None,
        lap_time=lap_time,
        lap_time_seconds=lap_time_to_seconds(lap_time) if lap_time else None,
    )
