"""Internal data structures for the reference collector layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

SOURCE_GARAGE61 = "garage61"


@dataclass
class Garage61LapCandidate:
    """A candidate reference lap discovered on Garage61.

    This is an internal, source-specific representation used by the collector before a
    lap becomes a persisted ``ReferenceLap``. It intentionally carries the raw metadata
    returned by the source so nothing is lost during collection.
    """

    source_lap_id: str
    driver_name: str
    lap_time_seconds: float
    simulator: str
    car: str
    track: str
    source: str = SOURCE_GARAGE61
    source_url: Optional[str] = None
    track_layout: Optional[str] = None
    csv_path: Optional[str] = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
