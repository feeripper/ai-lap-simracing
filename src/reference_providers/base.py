"""Base interface and data structures for reference lap providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass
class ReferenceLapCandidate:
    """A candidate reference lap returned by a provider.

    This is a source-agnostic representation. Local and future external providers
    (e.g. Garage61) both return this shape so the analysis flow stays generic.
    """

    source: str
    csv_path: str
    driver_name: str
    lap_time_seconds: float
    simulator: str
    car: str
    track: str
    source_lap_id: Optional[str] = None
    source_url: Optional[str] = None


@runtime_checkable
class ReferenceLapProvider(Protocol):
    """Protocol implemented by reference lap providers."""

    def find_reference_lap(
        self, simulator: str, car: str, track: str
    ) -> ReferenceLapCandidate:
        """Find a reference lap for the given simulator, car, and track.

        Raises provider-specific exceptions when the simulator, car, track, or an
        active reference lap cannot be found.
        """
        ...

    def get_reference_csv_path(self, reference_lap: ReferenceLapCandidate) -> str:
        """Return the CSV path for a given reference lap candidate."""
        ...
